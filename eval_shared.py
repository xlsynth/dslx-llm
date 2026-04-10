# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import dataclasses
import difflib
import optparse
import os
import re
from pathlib import Path
from typing import Any, Callable, Optional, List

import termcolor
from tempcompat import TemporaryDirectory as CompatTemporaryDirectory

import critic
from dslx_run_flags import extract_dslx_run_flags
from dslx_text import strip_fences
from openai_compat import REASONING_EFFORT_CHOICES
import providers


DEFAULT_DSLX_INTERPRETER_FLAGS: List[str] = []
PROMPT_REPLY_SUFFIX = (
    '\n\n**Important:** reply **only** with the DSLX code text that solves this '
    'problem, it will be piped **directly** to a DSLX interpreter! Do **not** '
    'apologize or explain! Do not write any tests as they may interfere with '
    'the (hidden) acceptance test suite. I will respond with any error text '
    'that might occur when running an acceptance test suite.\n'
)


def load_system_prompt(prompt_file: str | Path) -> str:
    with open(prompt_file, "r") as f:
        return f.read() + PROMPT_REPLY_SUFFIX


def print_color_diff(text1: str, text2: str) -> None:
    d = difflib.Differ()
    diff = list(d.compare(text1.splitlines(), text2.splitlines()))

    for line in diff:
        if line.startswith("+ "):
            print(termcolor.colored(line, "green"))
        elif line.startswith("- "):
            print(termcolor.colored(line, "red"))
        elif line.startswith("? "):
            print(termcolor.colored(line, "yellow"))
        else:
            print(line)


@dataclasses.dataclass
class Sample:
    prompt: str
    signature: str
    tests: str
    prologue: Optional[str] = None
    requirements: Optional[str] = None


def parse_sample(file_path: Path) -> Sample:
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


def build_full_code(generated_code: str, sample: Sample, test_file: Path | None) -> str:
    prologue_lines = []
    if sample.prologue:
        prologue = strip_fences(sample.prologue)
        for line in prologue.splitlines():
            prologue_lines.append(line.strip())

    has_import_std = (
        'import std;' in generated_code
        or any(line.strip() == 'import std;' for line in prologue_lines)
    )
    if not has_import_std:
        prologue_lines.append('import std;')

    additional_tests = None
    if test_file:
        with test_file.open("r") as fd:
            additional_tests = fd.read()

    parts = []
    if prologue_lines:
        parts.append('\n'.join(prologue_lines))
    parts.append(strip_fences(generated_code))
    parts.append("// -- tests\n\n" + strip_fences(sample.tests))
    full_code = "\n\n".join(parts)
    if additional_tests:
        full_code += f"\n\n// -- {str(test_file)}\n\n" + additional_tests
    return full_code


def collect_dslx_run_flags(generated_code: str, sample: Sample) -> list[str]:
    extra_flags = list(DEFAULT_DSLX_INTERPRETER_FLAGS)
    if sample.prologue:
        extra_flags.extend(extract_dslx_run_flags(sample.prologue))
    extra_flags.extend(extract_dslx_run_flags(generated_code))
    return extra_flags


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


def get_first_n_failed_tests(stderr: str, n: int = 5) -> str:
    if "RUN UNITTEST" not in stderr or "FAILED" not in stderr:
        return stderr

    matches = re.findall(r"\[ RUN UNITTEST  \].*?\n[^\[](?:.|\n)*?\[        FAILED \].*?$", stderr, re.MULTILINE)
    summary = stderr.rsplit("\n", maxsplit=2)[1]
    return "\n".join(matches[:n] if n > 0 else matches) + f"\n{summary}\n"


@dataclasses.dataclass
class EvaluateSampleResult:
    success: bool
    first_attempt_success: bool
    generated: str | None


RunCandidate = Callable[[str, Sample, str, str], RunResult]


def format_model_variant(model: str, reasoning_effort: Optional[str]) -> str:
    if reasoning_effort is None:
        return model
    return f'{model}@{reasoning_effort}'


def sanitize_model_variant_for_path(model: str, reasoning_effort: Optional[str]) -> str:
    return re.sub(r'[^A-Za-z0-9_.@-]+', '_', format_model_variant(model, reasoning_effort))


def evaluate_sample_with_runner(
    sample_path: Path,
    provider: providers.ProviderModule,
    model: str,
    *,
    system_prompt: str,
    reasoning_effort: Optional[str],
    max_retries: int,
    run_candidate: RunCandidate,
    run_critic_step: bool,
    critic_model: str,
    critic_reasoning_effort: Optional[str],
    dslx_critic_reference: str,
    timeout: Optional[int] = None,
    reduce_test_errors: Optional[int] = None,
) -> EvaluateSampleResult:
    _, sample_filename = os.path.split(sample_path)
    sample_filename, _ = os.path.splitext(sample_filename)
    model_slug_for_path = sanitize_model_variant_for_path(model, reasoning_effort)

    sample = parse_sample(sample_path)
    codegen = provider.CodeGenerator(model, reasoning_effort, system_prompt, timeout)

    with CompatTemporaryDirectory(
        suffix=f'-{model_slug_for_path}-{sample_filename}',
        delete=False,
    ) as tmpdir:
        print('tmpdir:', tmpdir)

        all_generated = []
        feedback_from_last_iteration = None

        for attempt in range(1, max(1, max_retries) + 1):
            print(f"🤖 Attempt {attempt}:")
            if feedback_from_last_iteration is not None:
                generated_code = codegen.provide_feedback('```\n' + feedback_from_last_iteration + '\n```\n')
            else:
                generated_code = codegen.generate_code(sample.prompt, sample.signature, sample.prologue)

            all_generated.append(generated_code)

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

            run_result = run_candidate(
                generated_code,
                sample,
                f'{sample_filename}-attempt-{attempt}',
                tmpdir,
            )

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
                if run_critic_step and sample.requirements:
                    termcolor.cprint('<<CRITIQUEE', color='blue')
                    print(strip_fences(generated_code).strip())
                    termcolor.cprint('CRITIQUEE', color='blue')

                    termcolor.cprint('<<CRITIC', color='blue')
                    critic_result = provider.run_critic(
                        critic_model=critic_model,
                        critic_reasoning_effort=critic_reasoning_effort,
                        generated_code=generated_code,
                        dslx_critic_reference=dslx_critic_reference,
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
        first_attempt_success=False,
        generated=all_generated[-1] if all_generated else None,
    )


def get_sample_choices(samples_dir: str | Path) -> list[str]:
    return sorted({p.stem for p in Path(samples_dir).glob("*.md")})


def parse_only_csv(value: str) -> list[str]:
    parts = [p.strip() for p in value.split(",")]
    return [p for p in parts if p]


def resolve_sample_files(
    samples_dir: str | Path,
    sample: Optional[str],
    only: Optional[str],
    external_sample: Optional[str],
) -> list[Path]:
    sample_choices = get_sample_choices(samples_dir)
    sample_files = sorted(Path(samples_dir).glob("*.md"))

    if sample:
        sample_files = [Path(samples_dir, sample + '.md')]
    elif only:
        only_list = parse_only_csv(only)
        if not only_list:
            raise ValueError('--only was provided but no sample names were found')
        unknown = sorted(set(only_list) - set(sample_choices))
        if unknown:
            raise ValueError('unknown sample(s) in --only: %s' % ','.join(unknown))
        seen = set()
        deduped_only = []
        for name in only_list:
            if name in seen:
                continue
            seen.add(name)
            deduped_only.append(name)
        sample_files = [Path(samples_dir, name + '.md') for name in deduped_only]

    if external_sample:
        if sample is None and only is None:
            sample_files = [Path(external_sample)]
        else:
            sample_files.append(Path(external_sample))

    return sample_files


def resolve_reasoning_efforts(
    parser: optparse.OptionParser,
    provider: providers.ProviderModule,
    *,
    model: str,
    reasoning_effort: Optional[str],
    run_critic_step: bool,
    critic_model: str,
    critic_reasoning_effort: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    reasoning_choices = provider.get_reasoning_effort_choices(model)
    if reasoning_choices is None:
        if reasoning_effort is not None:
            parser.error(
                f'--reasoning-effort cannot be used with non-reasoning model {model!r}'
            )
    else:
        if reasoning_effort is None:
            parser.error(
                f'--reasoning-effort is required for reasoning-capable model {model!r}; '
                f'allowed values: {", ".join(reasoning_choices)}'
            )
        if reasoning_effort not in reasoning_choices:
            parser.error(
                f'--reasoning-effort={reasoning_effort!r} is not supported by model '
                f'{model!r}; allowed values: {", ".join(reasoning_choices)}'
            )

    if not run_critic_step:
        return reasoning_effort, None

    if critic_reasoning_effort is None and critic_model == model:
        critic_reasoning_effort = reasoning_effort

    critic_reasoning_choices = provider.get_reasoning_effort_choices(critic_model)
    if critic_reasoning_choices is None:
        if critic_reasoning_effort is not None:
            parser.error(
                '--critic-reasoning-effort cannot be used with non-reasoning '
                f'critic model {critic_model!r}'
            )
    else:
        if critic_reasoning_effort is None:
            parser.error(
                f'--critic-reasoning-effort is required for reasoning-capable '
                f'critic model {critic_model!r}; allowed values: '
                f'{", ".join(critic_reasoning_choices)}'
            )
        if critic_reasoning_effort not in critic_reasoning_choices:
            parser.error(
                f'--critic-reasoning-effort={critic_reasoning_effort!r} is not '
                f'supported by critic model {critic_model!r}; allowed values: '
                f'{", ".join(critic_reasoning_choices)}'
            )

    return reasoning_effort, critic_reasoning_effort
