# SPDX-License-Identifier: Apache-2.0

import optparse
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional


import critic
from eval_shared import (
    EvaluateSampleResult,
    RunResult,
    build_full_code,
    collect_dslx_run_flags,
    evaluate_sample_with_runner,
    format_model_variant,
    get_sample_choices,
    load_system_prompt,
    REASONING_EFFORT_CHOICES,
    resolve_reasoning_efforts,
    resolve_sample_files,
)
import providers
import tools


PROMPT_FILE = "proc_eval/prompt.md"
SAMPLES_DIR = "proc_eval/samples"
SYSTEM_PROMPT = load_system_prompt(PROMPT_FILE)
DSLX_CRITIC_REFERENCE = critic.load_dslx_critic_reference(PROMPT_FILE)


def run_proc_tests(
    generated_code: str,
    sample,
    sample_filename: str,
    tmpdir: str,
    test_file: Path | None,
    additional_dslx_path: Path | None,
    *,
    max_ticks: Optional[int],
    trace_channels: bool,
    trace_calls: bool,
) -> RunResult:
    full_code = build_full_code(generated_code, sample, test_file)
    x_path = os.path.join(tmpdir, sample_filename + ".x")
    with open(x_path, "w") as f:
        f.write(full_code)

    extra_flags = collect_dslx_run_flags(generated_code, sample)
    if max_ticks is not None:
        extra_flags.append(f'--max_ticks={max_ticks}')
    if trace_channels:
        extra_flags.append('--trace_channels')
    if trace_calls:
        extra_flags.append('--trace_calls')

    cmd = [
        tools.DSLX_INTERPRETER_MAIN,
        x_path,
        '--dslx_stdlib_path',
        tools.DSLX_STDLIB_PATH,
        *extra_flags,
        '--compare=none',
    ]
    if additional_dslx_path:
        cmd += ["--dslx_path", str(additional_dslx_path.resolve())]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return RunResult(
        subprocess.list2cmdline(cmd),
        result.returncode == 0,
        result.returncode,
        result.stdout,
        result.stderr,
    )


def evaluate_sample(
    sample_path: Path,
    provider: providers.ProviderModule,
    model: str,
    *,
    reasoning_effort: Optional[str],
    max_retries: int,
    run_critic_step: bool,
    critic_model: str,
    critic_reasoning_effort: Optional[str],
    test_file: Optional[Path],
    reduce_test_errors: Optional[int] = None,
    additional_dslx_path: Optional[Path] = None,
    timeout: Optional[int] = None,
    max_ticks: Optional[int] = None,
    trace_channels: bool = False,
    trace_calls: bool = False,
) -> EvaluateSampleResult:
    def run_candidate(generated_code, sample, attempt_filename, tmpdir):
        return run_proc_tests(
            generated_code,
            sample,
            attempt_filename,
            tmpdir,
            test_file,
            additional_dslx_path,
            max_ticks=max_ticks,
            trace_channels=trace_channels,
            trace_calls=trace_calls,
        )

    return evaluate_sample_with_runner(
        sample_path,
        provider,
        model,
        system_prompt=SYSTEM_PROMPT,
        reasoning_effort=reasoning_effort,
        max_retries=max_retries,
        run_candidate=run_candidate,
        run_critic_step=run_critic_step,
        critic_model=critic_model,
        critic_reasoning_effort=critic_reasoning_effort,
        dslx_critic_reference=DSLX_CRITIC_REFERENCE,
        timeout=timeout,
        reduce_test_errors=reduce_test_errors,
    )


# Get provide from environment as it affects model options.
PROVIDER = os.environ.get('PROVIDER', 'openai')


def main() -> None:
    provider = getattr(providers, PROVIDER)
    parser = optparse.OptionParser()
    parser.add_option('--list', action='store_true', default=False, help='list available proc samples and exit')
    parser.add_option('--model', default=None, choices=provider.MODEL_CHOICES, help='choose a model to query; choices: %s' % '|'.join(provider.MODEL_CHOICES))
    parser.add_option(
        '--custom-model-slug',
        default=None,
        type='string',
        help='use an arbitrary provider model slug instead of the built-in --model choices',
    )
    parser.add_option('--sample', default=None, choices=get_sample_choices(SAMPLES_DIR), help='evaluate a single proc sample by name')
    parser.add_option('--only', default=None, help='comma-separated list of proc samples to evaluate (e.g. foo,bar,baz)')
    parser.add_option('--external-sample', default=None, type=str, help="Path to the external proc sample that will be evaluated")
    parser.add_option('--external-prompt', default=None, type=str, help="Path to the prompt to use instead of proc_eval/prompt.md")
    parser.add_option('--max-retries', default=3, type=int)
    parser.add_option(
        '--reasoning-effort',
        default=None,
        choices=REASONING_EFFORT_CHOICES,
        help='reasoning effort for reasoning-capable models; choices: %s'
             % '|'.join(REASONING_EFFORT_CHOICES),
    )
    parser.add_option('--no-critic', action='store_true', default=False, help='disable the requirements critic step')
    parser.add_option('--critic-model', default=None, choices=provider.MODEL_CHOICES, help='model to use for requirements critic step (defaults to --model)')
    parser.add_option(
        '--critic-reasoning-effort',
        default=None,
        choices=REASONING_EFFORT_CHOICES,
        help='reasoning effort for reasoning-capable critic models '
             '(defaults to --reasoning-effort when the critic model matches); '
             'choices: %s' % '|'.join(REASONING_EFFORT_CHOICES),
    )
    parser.add_option('--test-file', type='string', default=None, help='File with additional proc tests')
    parser.add_option('--save-to', type='string', default=None, help="Path where generated proc should be saved")
    parser.add_option('--reduce-test-errors', type=int, default=None, help='How many (at most) test failures should be provided as feedback? If None, the whole STDERR is used')
    parser.add_option('--additional-dslx-path', type=str, default=None, help='Where to look for additional DSLX modules')
    parser.add_option('--timeout', default=None, type=int, help="Timeout of one request in minutes")
    parser.add_option('--max-ticks', default=None, type=int, help='Override the interpreter max proc ticks for this run')
    parser.add_option('--trace-channels', action='store_true', default=False, help='Trace channel send/receive activity during proc execution')
    parser.add_option('--trace-calls', action='store_true', default=False, help='Trace interpreted function calls during proc execution')
    opts, args = parser.parse_args()

    if args:
        parser.error('No args are expected')

    sample_choices = get_sample_choices(SAMPLES_DIR)
    if opts.list:
        for name in sample_choices:
            print(name)
        return

    if opts.model is not None and opts.custom_model_slug is not None:
        parser.error('cannot specify both --model and --custom-model-slug')

    if opts.model is None and opts.custom_model_slug is None:
        parser.error('either --model or --custom-model-slug is required')

    model = opts.custom_model_slug or opts.model

    if opts.external_prompt:
        global PROMPT_FILE
        global SYSTEM_PROMPT
        global DSLX_CRITIC_REFERENCE
        PROMPT_FILE = opts.external_prompt
        SYSTEM_PROMPT = load_system_prompt(PROMPT_FILE)
        DSLX_CRITIC_REFERENCE = critic.load_dslx_critic_reference(PROMPT_FILE)

    if opts.sample and opts.only:
        parser.error('cannot specify both --sample and --only')

    try:
        sample_files = resolve_sample_files(SAMPLES_DIR, opts.sample, opts.only, opts.external_sample)
    except ValueError as e:
        parser.error(str(e))

    results: Dict[Path, EvaluateSampleResult] = {}

    critic_model = opts.critic_model or model
    reasoning_effort, critic_reasoning_effort = resolve_reasoning_efforts(
        parser,
        provider,
        model=model,
        reasoning_effort=opts.reasoning_effort,
        run_critic_step=not opts.no_critic,
        critic_model=critic_model,
        critic_reasoning_effort=opts.critic_reasoning_effort,
    )
    model_variant = format_model_variant(model, reasoning_effort)
    critic_variant = format_model_variant(critic_model, critic_reasoning_effort)

    for sample_file in sample_files:
        print(f"Evaluating {sample_file} with {model_variant}...")
        result = evaluate_sample(
            sample_file,
            provider,
            model,
            reasoning_effort=reasoning_effort,
            max_retries=opts.max_retries,
            run_critic_step=not opts.no_critic,
            critic_model=critic_model,
            critic_reasoning_effort=critic_reasoning_effort,
            test_file=Path(opts.test_file) if opts.test_file else None,
            reduce_test_errors=opts.reduce_test_errors,
            additional_dslx_path=Path(opts.additional_dslx_path) if opts.additional_dslx_path else None,
            timeout=opts.timeout,
            max_ticks=opts.max_ticks,
            trace_channels=opts.trace_channels,
            trace_calls=opts.trace_calls,
        )
        results[sample_file] = result

    total_samples = len(results)
    total_success = sum(1 for r in results.values() if r.success)
    first_attempt_success_count = sum(1 for r in results.values() if r.first_attempt_success)

    print("\n=== SCORECARD ===")
    print(f"Model: {model_variant}")
    if not opts.no_critic:
        print(f"Critic: {critic_variant}")
    for sample, result in results.items():
        if result.success:
            status = "PASS"
            leader = "✅"
        else:
            status = "FAIL"
            leader = "❌"
        first_attempt = "FIRST ATTEMPT" if result.first_attempt_success else "MULTIPLE ATTEMPTS"
        print(f"{leader} {sample}: {status} ({first_attempt})")
        if opts.save_to and result.generated:
            save_to = Path(opts.save_to)
            save_to.parent.mkdir(exist_ok=True)
            with save_to.open("w") as fd:
                fd.write(result.generated)
            print(f"Generated XLS saved to {str(save_to)}")

    print("\nSummary:")
    print(f"Total Samples: {total_samples}")
    print(f"Pass Rate (First Attempt): {first_attempt_success_count / total_samples:.2%}")
    print(f"Pass Rate (All Attempts): {total_success / total_samples:.2%}")
    print("\nUsed tokens:")
    print(f"Input (without cached): {provider.TOTAL_USAGE['input']}")
    print(f"Cached tokens: {provider.TOTAL_USAGE['cached']}")
    print(f"Output: {provider.TOTAL_USAGE['output']}")


if __name__ == "__main__":
    main()
