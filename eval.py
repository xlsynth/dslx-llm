# SPDX-License-Identifier: Apache-2.0

import optparse
import os
import subprocess
import tempfile
from pathlib import Path

import openai
import termcolor

PROMPT_FILE = "prompt.md"
SAMPLES_DIR = "samples/"
DSLX_INTERPRETER = "dslx_interpreter_main"
DSLX_STDLIB_PATH = os.environ['DSLX_STDLIB_PATH']

assert os.path.exists(os.path.join(DSLX_STDLIB_PATH, 'std.x'))

def load_system_prompt():
    # Load the system prompt
    with open(PROMPT_FILE, "r") as f:
        system_prompt = f.read()

    system_prompt += '\n\n**Important:** reply **only** with the DSLX code text that solves this problem, it will be piped **directly** to a DSLX interpreter! Do **not** apologize or explain! Do not write any tests as they may interfere with the (hidden) acceptance test suite. I will respond with any error text that might occur when running an acceptance test suite.\n'
    return system_prompt

SYSTEM_PROMPT = load_system_prompt()

def parse_sample(file_path):
    """Parse the sample file to extract the prompt, signature, and tests."""
    with open(file_path, "r") as f:
        content = f.read()
    sections = {}
    current_section = None
    for line in content.splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip().lower()
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}

class CodeGenerator:
    def __init__(self, model, system_prompt):
        """Initialize the CodeGenerator with a persistent OpenAI connection."""
        self.client = openai.Client()
        self.model = model
        self.messages = [
            {"role": "user", "content": system_prompt}
        ]

    def generate_code(self, prompt, signature):
        """Generate code using the OpenAI API and retain context for follow-ups."""
        # Add user prompt to the message history
        self.messages.append({"role": "user", "content": f"{prompt}\n\nSignature:\n{signature}"})

        # Make the API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
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
            model=self.model,
            messages=self.messages,
        )

        # Capture assistant response and add it to the message history
        assistant_response = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response

def strip_fences(text):
    text = text.strip()
    if text.startswith('```'):
        text = '\n'.join(text.splitlines()[1:-1])
    return text

def run_dslx_tests(generated_code, test_cases, sample_filename, tmpdir):
    """Run DSLX tests using the interpreter."""
    prologue_lines = []
    if 'import std;' not in generated_code:
        prologue_lines.append('import std;')

    full_code = '\n'.join(prologue_lines) + '\n\n' + strip_fences(generated_code) + "\n\n// -- tests\n\n" + strip_fences(test_cases)
    x_path = os.path.join(tmpdir, sample_filename + ".x")
    with open(x_path, "w") as f:
        f.write(full_code)

    result = subprocess.run(
        [DSLX_INTERPRETER, x_path, '--dslx_stdlib_path', DSLX_STDLIB_PATH, '--compare=jit'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    success = result.returncode == 0
    return success, result.stdout if success else result.stderr

def evaluate_sample(sample_path, model, max_retries):
    """Evaluate a single sample."""
    _, sample_filename = os.path.split(sample_path)
    sample_filename, _ = os.path.splitext(sample_filename)

    sample = parse_sample(sample_path)
    prompt, signature, tests = sample["prompt"], sample["signature"], sample["tests"]
    codegen = CodeGenerator(model, SYSTEM_PROMPT)

    with tempfile.TemporaryDirectory(suffix=f'-{model}-{sample_filename}', delete=False) as tmpdir:
        print('tmpdir:', tmpdir)

        feedback_from_last_iteration = None
        first_attempt_success = False
        for attempt in range(1, max_retries + 1):
            print(f"🤖 Attempt {attempt}:")
            if feedback_from_last_iteration is not None:
                generated_code = codegen.provide_feedback('```\n' + feedback_from_last_iteration + '\n```\n')
            else:
                generated_code = codegen.generate_code(prompt, signature)

            termcolor.cprint('<<EOF', color='blue')
            print(generated_code)
            termcolor.cprint('EOF', color='blue')
            success, result = run_dslx_tests(generated_code, tests, f'{sample_filename}-attempt-{attempt}', tmpdir)

            # Write out results to the tmpdir as well.
            with open(os.path.join(tmpdir, f'{sample_filename}-attempt-{attempt}-result-success-{success}.txt'), 'w') as f:
                f.write(result)

            if success:
                print(f"✅ Success on attempt {attempt}")
                if attempt == 1:
                    first_attempt_success = True
                return True, first_attempt_success

            print(f"❌ Error on attempt {attempt}: {result}")
            feedback_from_last_iteration = result

    print("❌ All attempts failed.")
    return False, first_attempt_success

def get_sample_choices():
    return [os.path.splitext(filename)[0] for filename in os.listdir(SAMPLES_DIR)]

def main():
    """Main function to evaluate all samples."""
    parser = optparse.OptionParser()
    parser.add_option('--model', default=None, choices=['gpt-3.5-turbo', 'gpt-4o-mini', 'gpt-4o', 'o1-mini', 'o1-preview'])
    parser.add_option('--sample', default=None, choices=get_sample_choices())
    parser.add_option('--max-retries', default=3, type=int)
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
        success, first_attempt_success = evaluate_sample(sample_file, opts.model, opts.max_retries)
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
