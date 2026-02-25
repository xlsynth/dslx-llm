# SPDX-License-Identifier: Apache-2.0

import dataclasses
import difflib
import json
import optparse
import os
import re
import subprocess
from pathlib import Path
from typing import Optional, List, Dict

import termcolor
from tempcompat import TemporaryDirectory as CompatTemporaryDirectory

import tools
import critic
from dslx_run_flags import extract_dslx_run_flags
from dslx_text import strip_fences

try:
    import openai  # type: ignore
except ModuleNotFoundError:
    openai = None

PROMPT_FILE = "prompt.md"
SAMPLES_DIR = "samples/"
DEFAULT_DSLX_INTERPRETER_FLAGS = ['--type_inference_v2=true']

# Models that require a reasoning effort config to be set.
NEED_REASONING_EFFORT = set(['o3-mini', 'o4-mini', 'gpt-5.1', 'gpt-5.2'])
MODEL_CHOICES = [
    'gpt-3.5-turbo',
    'gpt-4o-mini',
    'gpt-4o',
    'o1-preview',
    'o1-mini',
    'o1',
    'o1-pro',
    'o3-mini',
    'o3',
    'o4-mini',
    'gpt-4.1',
    'gpt-4.1-mini',
    'gpt-5.1',
    'gpt-5.2',
]

def load_system_prompt() -> str:
    # Load the system prompt
    with open(PROMPT_FILE, "r") as f:
        system_prompt = f.read()

    system_prompt += '\n\n**Important:** reply **only** with the DSLX code text that solves this problem, it will be piped **directly** to a DSLX interpreter! Do **not** apologize or explain! Do not write any tests as they may interfere with the (hidden) acceptance test suite. I will respond with any error text that might occur when running an acceptance test suite.\n'
    return system_prompt

SYSTEM_PROMPT = load_system_prompt()

DSLX_CRITIC_REFERENCE = critic.load_dslx_critic_reference(PROMPT_FILE)

def print_color_diff(text1: str, text2: str) -> None:
    d = difflib.Differ()
    diff = list(d.compare(text1.splitlines(), text2.splitlines()))

    for line in diff:
        if line.startswith("+ "):  # Added lines
            print(termcolor.colored(line, "green"))
        elif line.startswith("- "):  # Removed lines
            print(termcolor.colored(line, "red"))
        elif line.startswith("? "):  # Contextual hints
            print(termcolor.colored(line, "yellow"))
        else:  # Unchanged lines
            print(line)

@dataclasses.dataclass
class Sample:
    prompt: str
    signature: str
    tests: str
    prologue: Optional[str] = None
    requirements: Optional[str] = None

def parse_sample(file_path: Path) -> Sample:
    """Parse the sample file to extract the prompt, signature, and tests."""
    with open(file_path, "r") as f:
        content = f.read()
    sections: dict[str, list[str]] = {}
    current_section: Optional[str] = None
    for line in content.splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip().lower()
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)
    return Sample(
        prompt="\n".join(sections["prompt"]).strip(),
        signature="\n".join(sections["signature"]).strip(),
        tests="\n".join(sections["tests"]).strip(),
        prologue="\n".join(sections["prologue"]).strip() if "prologue" in sections else None,
        requirements="\n".join(sections["requirements"]).strip() if "requirements" in sections else None,
    )

# Gathers statistics about token usage from current run
TOTAL_USAGE = {
    "input": 0,
    "cached": 0,
    "output": 0,
}

def print_usage(usage: openai.types.CompletionUsage | None):
    """Display token usage of a response and gathers data for a statistics."""
    if usage is None:
        return

    # Gather stats
    TOTAL_USAGE["cached"] += usage.prompt_tokens_details.cached_tokens
    TOTAL_USAGE["input"] += usage.prompt_tokens - usage.prompt_tokens_details.cached_tokens
    TOTAL_USAGE["output"] += usage.completion_tokens
    # Display used tokens
    termcolor.cprint(
        f"Used tokens - in {usage.prompt_tokens} (cached {usage.prompt_tokens_details.cached_tokens})"
        f" - out {usage.completion_tokens} - total {usage.total_tokens}",
        color="red",
    )

class CodeGenerator:
    def __init__(self, model: str, reasoning_effort: Optional[str], system_prompt: str, timeout: int | float | None = None):
        """Initialize the CodeGenerator with a persistent OpenAI connection."""
        if openai is None:
            raise RuntimeError(
                'The "openai" Python package is required to run evaluations. '
                'Install it (e.g. `pip install -r requirements.txt`) and retry.'
            )
        client_kwargs = {"timeout": 60 * timeout} if timeout else {}
        self.client = openai.Client(**client_kwargs)
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.messages = [
            {"role": "user", "content": system_prompt}
        ]

    def _get_chat_kwargs(self):
        if self.model in NEED_REASONING_EFFORT:
            assert self.reasoning_effort is not None
            return {
                'model': self.model,
                'reasoning_effort': self.reasoning_effort,
                'messages': self.messages,
            }
        return {'model': self.model, 'messages': self.messages}

    def generate_code(self, prompt: str, signature: str, prologue: Optional[str] = None) -> str:
        """Generate code using the OpenAI API and retain context for follow-ups."""
        # Add user prompt to the message history
        message = prompt
        if prologue:
            message += '\n\nPrologue:\n' + prologue
        message += '\n\nSignature:\n' + signature
        termcolor.cprint('<<PROBLEM', color='blue')
        print(message)
        termcolor.cprint('PROBLEM', color='blue')
        self.messages.append({"role": "user", "content": message})

        # Make the API call
        response = self.client.chat.completions.create(
            **self._get_chat_kwargs()
        )
        print_usage(response.usage)

        # Capture assistant response and add it to the message history
        assistant_response = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response

    def provide_feedback(self, error_message):
        """Feed follow-up errors back into the conversation."""
        # Add the error message as a user input to the message history
        self.messages.append({"role": "user", "content": f"Error encountered:\n{error_message}"})

        # Make the API call
        response = self.client.chat.completions.create(
            **self._get_chat_kwargs()
        )
        print_usage(response.usage)

        # Capture assistant response and add it to the message history
        assistant_response = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response

@dataclasses.dataclass
class RunResult:
    command: str
    success: bool
    retcode: int
    stdout: str
    stderr: str

def format_retcode(retcode: int) -> str:
    if retcode < 0:
        return f"{retcode} (signal {-retcode})"
    return str(retcode)

def get_first_n_failed_tests(stderr: str, n: int = 5):
    """Extracts first n failed tests from STDERR."""
    # Make sure the output contains tests' results
    if "RUN UNITTEST" not in stderr or "FAILED" not in stderr:
        return stderr

    matches = re.findall(r"\[ RUN UNITTEST  \].*?\n[^\[](?:.|\n)*?\[        FAILED \].*?$", stderr, re.MULTILINE)
    summary = stderr.rsplit("\n", maxsplit=2)[1]
    return "\n".join(matches[:n] if n > 0 else matches) + f"\n{summary}\n"

def run_dslx_tests(generated_code: str, sample: Sample, sample_filename: str, tmpdir: str, test_file: Path | None, additional_dslx_path: Path | None) -> RunResult:
    """Run DSLX tests using the interpreter."""
    prologue_lines = []
    if sample.prologue:
        prologue = strip_fences(sample.prologue)
        for line in prologue.splitlines():
            prologue_lines.append(line.strip())
    # Keep run options directives at the top of the file by appending any implicit
    # imports after the sample prologue.
    has_import_std = (
        'import std;' in generated_code
        or any(line.strip() == 'import std;' for line in prologue_lines)
    )
    if not has_import_std:
        prologue_lines.append('import std;')

    # Get additional tests from separate file
    additional_tests = None
    if test_file:
        with test_file.open("r") as fd:
            additional_tests = fd.read()

    full_code = '\n'.join(prologue_lines) + '\n\n' + strip_fences(generated_code) + "\n\n// -- tests\n\n" + strip_fences(sample.tests)
    if additional_tests:
        full_code += f"\n\n// -- {str(test_file)}\n\n" + additional_tests
    x_path = os.path.join(tmpdir, sample_filename + ".x")
    with open(x_path, "w") as f:
        f.write(full_code)

    extra_flags = list(DEFAULT_DSLX_INTERPRETER_FLAGS)
    if sample.prologue:
        extra_flags.extend(extract_dslx_run_flags(sample.prologue))
    extra_flags.extend(extract_dslx_run_flags(generated_code))
    cmd = [
        tools.DSLX_INTERPRETER_MAIN,
        x_path,
        '--dslx_stdlib_path',
        tools.DSLX_STDLIB_PATH,
        *extra_flags,
        '--compare=jit',
    ]
    if additional_dslx_path:
        cmd += ["--dslx_path", str(additional_dslx_path.resolve())]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    success = result.returncode == 0
    command = subprocess.list2cmdline(cmd)
    return RunResult(command, success, result.returncode, result.stdout, result.stderr)

@dataclasses.dataclass
class EvaluateSampleResult:
    success: bool
    first_attempt_success: bool
    generated: str | None

def evaluate_sample(
    sample_path: Path,
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
) -> EvaluateSampleResult:
    """Evaluate a single sample.

    Args:
        sample_path: The path to the sample file.
        model: The model to evaluate.
        reasoning_effort: The reasoning effort to use, i.e. in case of o3-mini.
        max_retries: The maximum number of retries to attempt before declaring failure.
        test_file: The optional path where generated code will be saved.
        reduce_test_errors: How many (at most) test failures should be provided as a feedback? If None, the whole STDERR is used.
        additional_dslx_path: The optional path with additional DSLX modules.
        timeout: The timeout of one request.

    Returns:
        A tuple containing a boolean indicating whether the sample was evaluated successfully and a boolean indicating whether the sample was evaluated successfully on the first attempt.
    """
    _, sample_filename = os.path.split(sample_path)
    sample_filename, _ = os.path.splitext(sample_filename)

    sample: Sample = parse_sample(sample_path)
    codegen = CodeGenerator(model, reasoning_effort, SYSTEM_PROMPT, timeout)

    with CompatTemporaryDirectory(suffix=f'-{model}-{sample_filename}', delete=False) as tmpdir:
        print('tmpdir:', tmpdir)

        all_generated = []

        feedback_from_last_iteration = None
        first_attempt_success = False
        for attempt in range(1, max(1, max_retries) + 1):
            print(f"🤖 Attempt {attempt}:")
            if feedback_from_last_iteration is not None:
                generated_code = codegen.provide_feedback('```\n' + feedback_from_last_iteration + '\n```\n')
            else:
                generated_code = codegen.generate_code(sample.prompt, sample.signature, sample.prologue)

            all_generated.append(generated_code)

            # Pre-validate that the assistant surrounded the solution in a
            # balanced triple-backtick block. If not, notify the model and
            # retry without invoking the (potentially costly) DSLX toolchain.
            try:
                _ = strip_fences(generated_code)
            except ValueError as e:
                print('🛑 Malformed or unbalanced ``` fences: requesting regeneration…')
                feedback_from_last_iteration = (
                    'Your response did not include a *balanced* triple-backtick fenced code block. '
                    'Error details: ' + str(e) + '\n'
                    'Please output the DSLX solution wrapped in ``` fences as previously requested.'
                )
                continue

            # Fences look good → proceed to compile / run tests.
            run_result = run_dslx_tests(generated_code, sample, f'{sample_filename}-attempt-{attempt}', tmpdir, test_file, additional_dslx_path)

            # From here on, normal path: run_result is defined.

            # Persist run outputs for later inspection (both success and failure).
            with open(os.path.join(tmpdir, f'{sample_filename}-attempt-{attempt}-result-retcode.txt'), 'w') as f:
                print(run_result.retcode, file=f)
            with open(os.path.join(tmpdir, f'{sample_filename}-attempt-{attempt}-result-stdout.txt'), 'w') as f:
                f.write(run_result.stdout)
            with open(os.path.join(tmpdir, f'{sample_filename}-attempt-{attempt}-result-stderr.txt'), 'w') as f:
                f.write(run_result.stderr)

            termcolor.cprint('<<GENERATED', color='blue')
            print(generated_code)
            termcolor.cprint('GENERATED', color='blue')

            if len(all_generated) >= 2:
                termcolor.cprint('<<DIFF', color='blue')
                print_color_diff(all_generated[-2], all_generated[-1])
                termcolor.cprint('DIFF', color='blue')

            if run_result.success:
                # Tests are cheap; only if they pass do we run the (more expensive) critic.
                if run_critic_step and sample.requirements:
                    termcolor.cprint('<<CRITIQUEE', color='blue')
                    print(strip_fences(generated_code).strip())
                    termcolor.cprint('CRITIQUEE', color='blue')

                    termcolor.cprint('<<CRITIC', color='blue')
                    critic_result = critic.run_critic(
                        critic_model=critic_model,
                        critic_reasoning_effort=critic_reasoning_effort,
                        generated_code=generated_code,
                        need_reasoning_effort=NEED_REASONING_EFFORT,
                        dslx_critic_reference=DSLX_CRITIC_REFERENCE,
                        prompt=sample.prompt,
                        signature=sample.signature,
                        requirements=sample.requirements,
                    )
                    print(critic_result.raw_json)
                    termcolor.cprint('CRITIC', color='blue')

                    with open(os.path.join(tmpdir, f'{sample_filename}-attempt-{attempt}-critic.json'), 'w') as f:
                        f.write(critic_result.raw_json)

                    if not critic_result.ok:
                        feedback_from_last_iteration = (
                            "Requirements check failed (tests passed). Please revise the implementation to satisfy the requirements.\n\n"
                            f"Critic message: {critic_result.message}\n"
                        )
                        continue

                print(f"✅ Success on attempt {attempt}")
                return EvaluateSampleResult(True, attempt == 1, all_generated[-1])

            print(
                f"❌ Error on attempt {attempt}; "
                f"retcode: {format_retcode(run_result.retcode)}; "
                f"command: {run_result.command}"
            )

            if reduce_test_errors is not None:
                first_failures = get_first_n_failed_tests(run_result.stderr, reduce_test_errors)
            else:
                first_failures = run_result.stderr
            termcolor.cprint(f'<<OUTPUT {"[filtered]" if reduce_test_errors is not None else ""}', color='blue')
            print(first_failures, end='')
            termcolor.cprint('OUTPUT', color='blue')

            feedback_from_last_iteration = first_failures

    print("❌ All attempts failed.")
    return EvaluateSampleResult(
        success=False,
        first_attempt_success=first_attempt_success,
        generated=all_generated[-1] if all_generated else None
    )

def get_sample_choices() -> list[str]:
    """Returns available sample names (sorted, unique)."""
    return sorted({p.stem for p in Path(SAMPLES_DIR).glob("*.md")})

def parse_only_csv(value: str) -> list[str]:
    parts = [p.strip() for p in value.split(",")]
    return [p for p in parts if p]

def main() -> None:
    """Main function to evaluate all samples."""
    parser = optparse.OptionParser()
    parser.add_option('--list', action='store_true', default=False, help='list available samples and exit')
    parser.add_option('--model', default=None, choices=MODEL_CHOICES, help='choose a model to query; choices: %s' % '|'.join(MODEL_CHOICES))
    parser.add_option('--sample', default=None, choices=get_sample_choices(), help='evaluate a single sample by name')
    parser.add_option('--only', default=None, help='comma-separated list of samples to evaluate (e.g. foo,bar,baz)')
    parser.add_option('--external-sample', default=None, type=str, help="Path to the external sample that will be evaluated")
    parser.add_option('--external-prompt', default=None, type=str, help="Path to the prompt to use instead of prompt.md")
    parser.add_option('--max-retries', default=3, type=int)
    parser.add_option('--reasoning-effort', default='high', choices=['low', 'medium', 'high'], help='choose a reasoning effort; choices: %s' % '|'.join(['low', 'medium', 'high']))
    parser.add_option('--no-critic', action='store_true', default=False, help='disable the requirements critic step')
    parser.add_option('--critic-model', default=None, choices=MODEL_CHOICES, help='model to use for requirements critic step (defaults to --model)')
    parser.add_option('--critic-reasoning-effort', default=None, choices=['low', 'medium', 'high'], help='reasoning effort for critic model (defaults to --reasoning-effort)')
    parser.add_option('--test-file', type='string', default=None, help='File with additional tests')
    parser.add_option('--save-to', type='string', default=None, help="Path where generated component should be saved")
    parser.add_option('--reduce-test-errors', type=int, default=None, help='How many (at most) test failures should be provided as a feedback? If None, the whole STDERR is used')
    parser.add_option('--additional-dslx-path', type=str, default=None, help='Where to look for additional DSLX modules')
    parser.add_option('--timeout', default=None, type=int, help="Timeout of a one request in minutes")
    opts, args = parser.parse_args()

    if args:
        parser.error('No args are expected')

    sample_choices = get_sample_choices()
    if opts.list:
        for name in sample_choices:
            print(name)
        return

    if opts.model is None:
        parser.error('--model is required')

    # Use external prompt
    if opts.external_prompt:
        global PROMPT_FILE
        global SYSTEM_PROMPT
        PROMPT_FILE = opts.external_prompt
        SYSTEM_PROMPT = load_system_prompt()

    if opts.sample and opts.only:
        parser.error('cannot specify both --sample and --only')

    sample_files: List[Path] = list(Path(SAMPLES_DIR).glob("*.md"))
    sample_files = sorted(sample_files)

    if opts.sample:
        sample_files = [Path(SAMPLES_DIR, opts.sample + '.md')]
    elif opts.only:
        only_list = parse_only_csv(opts.only)
        if not only_list:
            parser.error('--only was provided but no sample names were found')
        unknown = sorted(set(only_list) - set(sample_choices))
        if unknown:
            parser.error('unknown sample(s) in --only: %s' % ','.join(unknown))
        # Preserve user-provided order while avoiding duplicates.
        seen = set()
        deduped_only = []
        for name in only_list:
            if name in seen:
                continue
            seen.add(name)
            deduped_only.append(name)
        sample_files = [Path(SAMPLES_DIR, name + '.md') for name in deduped_only]

    if opts.external_sample:
        # If neither sample nor only was specified, evaluate only external sample
        if opts.sample is None and opts.only is None:
            sample_files = [Path(opts.external_sample)]
        else:
            sample_files.append(Path(opts.external_sample))

    results: Dict[Path, EvaluateSampleResult] = {}

    critic_model = opts.critic_model or opts.model
    critic_reasoning_effort = opts.critic_reasoning_effort or opts.reasoning_effort

    for sample_file in sample_files:
        print(f"Evaluating {sample_file}...")
        result: EvaluateSampleResult = evaluate_sample(
            sample_file,
            opts.model,
            reasoning_effort=opts.reasoning_effort,
            max_retries=opts.max_retries,
            run_critic_step=not opts.no_critic,
            critic_model=critic_model,
            critic_reasoning_effort=critic_reasoning_effort,
            test_file=Path(opts.test_file) if opts.test_file else None,
            reduce_test_errors=opts.reduce_test_errors,
            additional_dslx_path=Path(opts.additional_dslx_path) if opts.additional_dslx_path else None,
            timeout=opts.timeout,
        )
        results[sample_file] = result

    # Generate a scorecard
    total_samples = len(results)
    total_success = sum(1 for r in results.values() if r.success)
    first_attempt_success_count = sum(1 for r in results.values() if r.first_attempt_success)

    print("\n=== SCORECARD ===")
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
            opts.save_to = Path(opts.save_to)
            opts.save_to.parent.mkdir(exist_ok=True)
            with opts.save_to.open("w") as fd:
                fd.write(result.generated)
            print(f"Generated XLS saved to {str(opts.save_to)}")

    print("\nSummary:")
    print(f"Total Samples: {total_samples}")
    print(f"Pass Rate (First Attempt): {first_attempt_success_count / total_samples:.2%}")
    print(f"Pass Rate (All Attempts): {total_success / total_samples:.2%}")
    print("\nUsed tokens:")
    print(f"Input (without cached): {TOTAL_USAGE['input']}")
    print(f"Cached tokens: {TOTAL_USAGE['cached']}")
    print(f"Output: {TOTAL_USAGE['output']}")

if __name__ == "__main__":
    main()
