# SPDX-License-Identifier: Apache-2.0

import dataclasses
import difflib
import optparse
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import openai
import termcolor

PROMPT_FILE = "prompt.md"
SAMPLES_DIR = "samples/"
DSLX_INTERPRETER = "dslx_interpreter_main"
DSLX_STDLIB_PATH = os.environ['DSLX_STDLIB_PATH']

assert os.path.exists(os.path.join(DSLX_STDLIB_PATH, 'std.x'))

def load_system_prompt() -> str:
    # Load the system prompt
    with open(PROMPT_FILE, "r") as f:
        system_prompt = f.read()

    system_prompt += '\n\n**Important:** reply **only** with the DSLX code text that solves this problem, it will be piped **directly** to a DSLX interpreter! Do **not** apologize or explain! Do not write any tests as they may interfere with the (hidden) acceptance test suite. I will respond with any error text that might occur when running an acceptance test suite.\n'
    return system_prompt

SYSTEM_PROMPT = load_system_prompt()

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

def parse_sample(file_path: str) -> dict[str, str]:
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
    return {k: "\n".join(v).strip() for k, v in sections.items()}

class CodeGenerator:
    def __init__(self, model: str, reasoning_effort: Optional[str], system_prompt: str):
        """Initialize the CodeGenerator with a persistent OpenAI connection."""
        self.client = openai.Client()
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.messages = [
            {"role": "user", "content": system_prompt}
        ]

    def _get_chat_kwargs(self):
        if self.model == 'o3-mini':
            assert self.reasoning_effort is not None
            return {
                'model': 'o3-mini',
                'reasoning_effort': self.reasoning_effort,
                'messages': self.messages,
            }
        return {'model': self.model, 'messages': self.messages}

    def generate_code(self, prompt, signature):
        """Generate code using the OpenAI API and retain context for follow-ups."""
        # Add user prompt to the message history
        self.messages.append({"role": "user", "content": f"{prompt}\n\nSignature:\n{signature}"})

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
    text = text.strip()
    if text.startswith('```'):
        lines = text.splitlines()
        assert lines[-1] == '```'
        text = '\n'.join(lines[1:-1])
    return text

@dataclasses.dataclass
class RunResult:
    command: str
    success: bool
    retcode: int
    stdout: str
    stderr: str

def run_dslx_tests(generated_code: str, test_cases: str, sample_filename: str, tmpdir: str) -> RunResult:
    """Run DSLX tests using the interpreter."""
    prologue_lines = []
    if 'import std;' not in generated_code:
        prologue_lines.append('import std;')

    full_code = '\n'.join(prologue_lines) + '\n\n' + strip_fences(generated_code) + "\n\n// -- tests\n\n" + strip_fences(test_cases)
    x_path = os.path.join(tmpdir, sample_filename + ".x")
    with open(x_path, "w") as f:
        f.write(full_code)

    cmd = [DSLX_INTERPRETER, x_path, '--dslx_stdlib_path', DSLX_STDLIB_PATH, '--compare=jit']
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    success = result.returncode == 0
    command = subprocess.list2cmdline(cmd)
    return RunResult(command, success, result.returncode, result.stdout, result.stderr)

def evaluate_sample(sample_path: str, model: str, reasoning_effort: Optional[str], max_retries: int) -> tuple[bool, bool]:
    """Evaluate a single sample."""
    _, sample_filename = os.path.split(sample_path)
    sample_filename, _ = os.path.splitext(sample_filename)

    sample = parse_sample(sample_path)
    prompt, signature, tests = sample["prompt"], sample["signature"], sample["tests"]
    codegen = CodeGenerator(model, reasoning_effort, SYSTEM_PROMPT)

    with tempfile.TemporaryDirectory(suffix=f'-{model}-{sample_filename}', delete=False) as tmpdir:
        print('tmpdir:', tmpdir)

        all_generated = []

        feedback_from_last_iteration = None
        first_attempt_success = False
        for attempt in range(1, max_retries + 1):
            print(f"🤖 Attempt {attempt}:")
            if feedback_from_last_iteration is not None:
                generated_code = codegen.provide_feedback('```\n' + feedback_from_last_iteration + '\n```\n')
            else:
                generated_code = codegen.generate_code(prompt, signature)

            all_generated.append(generated_code)

            termcolor.cprint('<<GENERATED', color='blue')
            print(generated_code)
            termcolor.cprint('GENERATED', color='blue')

            if len(all_generated) >= 2:
                termcolor.cprint('<<DIFF', color='blue')
                print_color_diff(all_generated[-2], all_generated[-1])
                termcolor.cprint('DIFF', color='blue')

            run_result = run_dslx_tests(generated_code, tests, f'{sample_filename}-attempt-{attempt}', tmpdir)

            # Write out results to the tmpdir as well.
            with open(os.path.join(tmpdir, f'{sample_filename}-attempt-{attempt}-result-retcode.txt'), 'w') as f:
                print(run_result.retcode, file=f)
            with open(os.path.join(tmpdir, f'{sample_filename}-attempt-{attempt}-result-stdout.txt'), 'w') as f:
                f.write(run_result.stdout)
            with open(os.path.join(tmpdir, f'{sample_filename}-attempt-{attempt}-result-stderr.txt'), 'w') as f:
                f.write(run_result.stderr)

            if run_result.success:
                print(f"✅ Success on attempt {attempt}")
                if attempt == 1:
                    first_attempt_success = True
                return True, first_attempt_success

            print(f"❌ Error on attempt {attempt}; command: {run_result.command}")

            termcolor.cprint('<<OUTPUT', color='blue')
            print(run_result.stderr, end='')
            termcolor.cprint('OUTPUT', color='blue')

            feedback_from_last_iteration = run_result.stderr

    print("❌ All attempts failed.")
    return False, first_attempt_success

def get_sample_choices() -> list[str]:
    return [os.path.splitext(filename)[0] for filename in os.listdir(SAMPLES_DIR)]

def main():
    """Main function to evaluate all samples."""
    MODEL_CHOICES = ['gpt-3.5-turbo', 'gpt-4o-mini', 'gpt-4o', 'o1-mini', 'o1-preview', 'o3-mini']

    parser = optparse.OptionParser()
    parser.add_option('--model', default=None, choices=MODEL_CHOICES, help='choose a model to query; choices: %s' % '|'.join(MODEL_CHOICES))
    parser.add_option('--sample', default=None, choices=get_sample_choices())
    parser.add_option('--max-retries', default=3, type=int)
    parser.add_option('--reasoning-effort', default=None, choices=['low', 'medium', 'high'], help='choose a reasoning effort; choices: %s' % '|'.join(['low', 'medium', 'high']))
    opts, args = parser.parse_args()

    if args:
        parser.error('No args are expected')
    if opts.model is None:
        parser.error('--model is required')

    sample_files = list(Path(SAMPLES_DIR).glob("*.md"))

    if opts.sample:
        sample_files = [os.path.join(SAMPLES_DIR, opts.sample + '.md')]

    results = {}

    for sample_file in sample_files:
        print(f"Evaluating {sample_file}...")
        success, first_attempt_success = evaluate_sample(sample_file, opts.model, opts.reasoning_effort, opts.max_retries)
        results[sample_file] = {
            "success": success,
            "first_attempt_success": first_attempt_success,
        }

    # Generate a scorecard
    total_samples = len(results)
    total_success = sum(1 for r in results.values() if r["success"])
    first_attempt_success_count = sum(1 for r in results.values() if r["first_attempt_success"])

    print("\n=== SCORECARD ===")
    for sample, result in results.items():
        if result['success']:
            status = "PASS"
            leader = "✅"
        else:
            status = "FAIL"
            leader = "❌"
        first_attempt = "FIRST ATTEMPT" if result["first_attempt_success"] else "MULTIPLE ATTEMPTS"
        print(f"{leader} {sample}: {status} ({first_attempt})")

    print("\nSummary:")
    print(f"Total Samples: {total_samples}")
    print(f"Pass Rate (First Attempt): {first_attempt_success_count / total_samples:.2%}")
    print(f"Pass Rate (All Attempts): {total_success / total_samples:.2%}")

if __name__ == "__main__":
    main()
