# SPDX-License-Identifier: Apache-2.0

import dataclasses
import difflib
import json
import optparse
import os
import re
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict

import termcolor
from tempcompat import TemporaryDirectory as CompatTemporaryDirectory

import tools

try:
    import openai  # type: ignore
except ModuleNotFoundError:
    openai = None

PROMPT_FILE = "prompt.md"
SAMPLES_DIR = "samples/"

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

def load_dslx_critic_reference() -> str:
    """Loads a small DSLX language reference excerpt to help the critic model."""
    with open(PROMPT_FILE, "r") as f:
        content = f.read()

    # We want to include the key semantics that affect "graph of operations":
    # - immutable arrays and `update`
    # - `for` loops as accumulator-evolving expressions
    # Provide a stable excerpt to keep token usage bounded.
    intro = content.splitlines()[:80]
    intro_text = "\n".join(intro).strip()

    def slice_between(start_marker: str, end_marker: str) -> str:
        try:
            start = content.index(start_marker)
            end = content.index(end_marker, start)
        except ValueError:
            return ""
        return content[start:end].strip()

    immutable_updates = slice_between("**Immutable Array Updates**", "**No Mutation, Even In Control Flow Blocks**")
    for_loops = slice_between("**For Loops**", "**No While Loops**")

    parts = [
        "DSLX language reference (excerpt):",
        intro_text,
    ]
    if immutable_updates:
        parts.append(immutable_updates)
    if for_loops:
        parts.append(for_loops)
    return "\n\n".join(parts).strip()

DSLX_CRITIC_REFERENCE = load_dslx_critic_reference()

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

class CodeGenerator:
    def __init__(self, model: str, reasoning_effort: Optional[str], system_prompt: str):
        """Initialize the CodeGenerator with a persistent OpenAI connection."""
        if openai is None:
            raise RuntimeError(
                'The "openai" Python package is required to run evaluations. '
                'Install it (e.g. `pip install -r requirements.txt`) and retry.'
            )
        self.client = openai.Client()
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

        # Capture assistant response and add it to the message history
        assistant_response = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response

def strip_fences(text: str) -> str:
    """Return content inside the outermost triple-backtick fence.

    Strict version: if an opening fence is present it *must* have a corresponding
    closing fence at the same indentation level. Otherwise we raise a
    ValueError so the calling logic can request a regeneration from the model.
    """
    text = text.strip()

    if not text.startswith('```'):
        return text  # Unfenced – treat as literal DSLX.

    lines = text.splitlines()

    # Look for a matching closing fence from the end to capture the outermost.
    try:
        closing_index = len(lines) - 1 - lines[::-1].index('```')
    except ValueError:
        raise ValueError('Missing closing ``` fence in code block.')

    if closing_index == 0:
        raise ValueError('Code block consists solely of an opening ``` fence.')

    return '\n'.join(lines[1:closing_index])

@dataclasses.dataclass
class CriticResult:
    ok: bool
    confidence: float
    message: str
    raw_json: str

CRITIC_SYSTEM_PROMPT = """You are a strict requirements checker for DSLX code solutions.

You will be given:
- A problem prompt (English)
- A function signature (DSLX)
- A list of requirements (English)
- A short DSLX language reference excerpt
- A candidate DSLX implementation

Your job is to decide whether the implementation meets the requirements. You must:
- Treat comments as claims, not proof.
- Decide based on the actual code structure.
- If you cannot find concrete evidence that a requirement is satisfied, mark it as NOT satisfied.

Important: The graph of operations matters, not merely whether a `for` loop iterates over all indices.
For example, visiting every `i` is not evidence of a dense prefix network if most iterations simply copy
state or if the data dependencies do not match the required structure. When the requirements are about
algorithm structure (e.g. a Kogge-Stone prefix network), focus on:
- What values are combined (data dependencies), not just which indices are iterated over.
- Whether each stage recomputes prefix signals from the prior stage (stage-to-stage dependency), vs. a
  sequential in-stage dependence that is effectively ripple-like.
- Whether conditionals skip the combine operator for most indices, which can make the structure sparse.

Return ONLY valid JSON with this schema:
{
  "pass": true|false,
  "confidence": 0.0..1.0,
  "message": "If pass=false: short, actionable reason(s). If pass=true: short confirmation.",
  "per_requirement": [
    {"id": "string", "pass": true|false, "evidence": ["string", ...], "message": "string"}
  ]
}
"""

def _chat_kwargs(model: str, reasoning_effort: Optional[str], messages):
    if model in NEED_REASONING_EFFORT:
        assert reasoning_effort is not None
        return {'model': model, 'reasoning_effort': reasoning_effort, 'messages': messages}
    return {'model': model, 'messages': messages}

def _parse_critic_json(text: str) -> dict:
    # Allow the critic to wrap the JSON in a triple-backtick block.
    raw = strip_fences(text).strip()
    return json.loads(raw)

def run_critic(
    *,
    critic_model: str,
    critic_reasoning_effort: Optional[str],
    sample: Sample,
    generated_code: str,
) -> CriticResult:
    assert sample.requirements is not None
    if openai is None:
        raise RuntimeError(
            'The "openai" Python package is required to run evaluations. '
            'Install it (e.g. `pip install -r requirements.txt`) and retry.'
        )

    candidate = strip_fences(generated_code).strip()
    user_message = (
        "Problem prompt:\n"
        f"{sample.prompt}\n\n"
        "Signature:\n"
        f"{sample.signature}\n\n"
        "Requirements:\n"
        f"{sample.requirements}\n\n"
        f"{DSLX_CRITIC_REFERENCE}\n\n"
        "Candidate DSLX implementation:\n"
        "```dslx\n"
        f"{candidate}\n"
        "```"
    )

    client = openai.Client()
    messages = [
        {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    last_text = ""
    for attempt in range(1, 3):
        response = client.chat.completions.create(
            **_chat_kwargs(critic_model, critic_reasoning_effort, messages)
        )
        last_text = response.choices[0].message.content.strip()
        try:
            parsed = _parse_critic_json(last_text)
        except Exception as e:
            # Ask for a regeneration with strictly valid JSON.
            messages.append({"role": "assistant", "content": last_text})
            messages.append({
                "role": "user",
                "content": (
                    "Your previous response was not valid JSON and could not be parsed. "
                    f"Parsing error: {e}. "
                    "Please respond again with ONLY valid JSON matching the schema exactly."
                ),
            })
            continue

        ok = bool(parsed.get("pass"))
        confidence = float(parsed.get("confidence", 0.0))
        message = str(parsed.get("message", "")).strip()
        raw_json = strip_fences(last_text).strip()
        return CriticResult(ok=ok, confidence=confidence, message=message, raw_json=raw_json)

    return CriticResult(
        ok=False,
        confidence=0.0,
        message="Critic did not return valid JSON after retries.",
        raw_json=strip_fences(last_text).strip(),
    )

@dataclasses.dataclass
class RunResult:
    command: str
    success: bool
    retcode: int
    stdout: str
    stderr: str

_DSLX_RUN_FLAGS_RE = re.compile(r"^\s*//\s*dslx_run_(?:flags|options):\s*(.*)\s*$")

def extract_dslx_run_flags(*texts: Optional[str]) -> list[str]:
    """Extracts interpreter flags from directive comment lines.

    Supported directives:
      // dslx_run_flags: --warnings_as_errors=false
      // dslx_run_options: --warnings_as_errors=false
    """
    flags: list[str] = []
    for text in texts:
        if not text:
            continue
        for line in text.splitlines():
            m = _DSLX_RUN_FLAGS_RE.match(line)
            if not m:
                continue
            extra = m.group(1).strip()
            if not extra:
                continue
            for tok in shlex.split(extra):
                assert tok.startswith('--'), f'dslx_run_* directive token must start with "--": {tok!r}'
                flags.append(tok)

    # Deduplicate while preserving order.
    seen = set()
    deduped: list[str] = []
    for f in flags:
        if f in seen:
            continue
        seen.add(f)
        deduped.append(f)
    return deduped

def run_dslx_tests(generated_code: str, sample: Sample, sample_filename: str, tmpdir: str) -> RunResult:
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

    full_code = '\n'.join(prologue_lines) + '\n\n' + strip_fences(generated_code) + "\n\n// -- tests\n\n" + strip_fences(sample.tests)
    x_path = os.path.join(tmpdir, sample_filename + ".x")
    with open(x_path, "w") as f:
        f.write(full_code)

    extra_flags = extract_dslx_run_flags(sample.prologue, generated_code)
    cmd = [
        tools.DSLX_INTERPRETER_MAIN,
        x_path,
        '--dslx_stdlib_path',
        tools.DSLX_STDLIB_PATH,
        *extra_flags,
        '--compare=jit',
    ]
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

def evaluate_sample(
    sample_path: Path,
    model: str,
    *,
    reasoning_effort: Optional[str],
    max_retries: int,
    run_critic_step: bool,
    critic_model: str,
    critic_reasoning_effort: Optional[str],
) -> EvaluateSampleResult:
    """Evaluate a single sample.

    Args:
        sample_path: The path to the sample file.
        model: The model to evaluate.
        reasoning_effort: The reasoning effort to use, i.e. in case of o3-mini.
        max_retries: The maximum number of retries to attempt before declaring failure.

    Returns:
        A tuple containing a boolean indicating whether the sample was evaluated successfully and a boolean indicating whether the sample was evaluated successfully on the first attempt.
    """
    _, sample_filename = os.path.split(sample_path)
    sample_filename, _ = os.path.splitext(sample_filename)

    sample: Sample = parse_sample(sample_path)
    codegen = CodeGenerator(model, reasoning_effort, SYSTEM_PROMPT)

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
            run_result = run_dslx_tests(generated_code, sample, f'{sample_filename}-attempt-{attempt}', tmpdir)

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
                    critic_result = run_critic(
                        critic_model=critic_model,
                        critic_reasoning_effort=critic_reasoning_effort,
                        sample=sample,
                        generated_code=generated_code,
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
                return EvaluateSampleResult(True, attempt == 1)

            print(f"❌ Error on attempt {attempt}; command: {run_result.command}")

            termcolor.cprint('<<OUTPUT', color='blue')
            print(run_result.stderr, end='')
            termcolor.cprint('OUTPUT', color='blue')

            feedback_from_last_iteration = run_result.stderr

    print("❌ All attempts failed.")
    return EvaluateSampleResult(success=False, first_attempt_success=first_attempt_success)

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
    parser.add_option('--max-retries', default=3, type=int)
    parser.add_option('--reasoning-effort', default='high', choices=['low', 'medium', 'high'], help='choose a reasoning effort; choices: %s' % '|'.join(['low', 'medium', 'high']))
    parser.add_option('--no-critic', action='store_true', default=False, help='disable the requirements critic step')
    parser.add_option('--critic-model', default=None, choices=MODEL_CHOICES, help='model to use for requirements critic step (defaults to --model)')
    parser.add_option('--critic-reasoning-effort', default=None, choices=['low', 'medium', 'high'], help='reasoning effort for critic model (defaults to --reasoning-effort)')
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

    print("\nSummary:")
    print(f"Total Samples: {total_samples}")
    print(f"Pass Rate (First Attempt): {first_attempt_success_count / total_samples:.2%}")
    print(f"Pass Rate (All Attempts): {total_success / total_samples:.2%}")

if __name__ == "__main__":
    main()
