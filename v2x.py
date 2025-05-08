# SPDX-License-Identifier: Apache-2.0

import os
import optparse
import tempfile
from pathlib import Path
from typing import Optional

import termcolor
import tools

from eval import CodeGenerator, strip_fences

# -- Helpers to read Verilog and reference DSLX files
def read_file(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()

def extract_signature_and_tests(x_content: str):
    # Naive extraction: signature is first fn, tests are #[test]s
    lines = x_content.splitlines()
    signature = None
    tests = []
    in_test = False
    test_lines = []
    for line in lines:
        line_stripped = line.strip()
        if (line_stripped.startswith('fn ') or line_stripped.startswith('pub fn ')) and signature is None:
            signature = line_stripped
        if line_stripped.startswith('#[test]'):
            in_test = True
            test_lines = [line]
        elif in_test:
            test_lines.append(line)
            if line_stripped == '}':
                tests.append('\n'.join(test_lines))
                in_test = False
    return signature, '\n\n'.join(tests)

# -- Prompt construction
def make_prompt(verilog: str, reference_x: str, signature: str) -> str:
    return f"""
Translate the following Verilog module into a semantically identical DSLX function. The generated DSLX function MUST closely mirror the structure and logic of the Verilog module, not just its behavior. Use the provided signature. Do not include any tests or explanations.

Verilog:
```
{verilog}
```

Reference DSLX:
```
{reference_x}
```

Signature:
{signature}
"""

# -- Run DSLX interpreter to check generated code
def run_dslx_check(generated_code: str, signature: str, tests: str, tmpdir: str) -> tuple[bool, str]:
    # Compose a full .x file with the generated code and tests
    prologue_lines = []
    if 'import std;' not in generated_code:
        prologue_lines.append('import std;')
    full_code = '\n'.join(prologue_lines) + '\n\n' + strip_fences(generated_code) + "\n\n// -- tests\n\n" + strip_fences(tests)
    x_path = os.path.join(tmpdir, "candidate.x")
    with open(x_path, "w") as f:
        f.write(full_code)
    cmd = [tools.DSLX_INTERPRETER_MAIN, x_path, '--dslx_stdlib_path', tools.DSLX_STDLIB_PATH, '--compare=jit']
    result = os.popen(' '.join(cmd) + ' 2>&1').read()
    # Naive: success if 'error' not in output
    success = 'error' not in result.lower()
    return success, result

# -- Main logic
def main():
    parser = optparse.OptionParser()
    parser.add_option('--verilog', type=str, help='Path to input Verilog (.v) file')
    parser.add_option('--reference', type=str, help='Path to reference DSLX (.x) file')
    parser.add_option('--model', type=str, default='gpt-4o', help='LLM model to use')
    parser.add_option('--reasoning-effort', type=str, default='high', help='Reasoning effort for LLM')
    opts, args = parser.parse_args()

    if not opts.verilog or not opts.reference:
        parser.error('Both --verilog and --reference are required')

    verilog = read_file(opts.verilog)
    reference_x = read_file(opts.reference)
    signature, tests = extract_signature_and_tests(reference_x)
    if not signature:
        raise ValueError('Could not extract DSLX function signature from reference .x file')

    prompt = make_prompt(verilog, reference_x, signature)
    codegen = CodeGenerator(opts.model, opts.reasoning_effort, prompt)

    with tempfile.TemporaryDirectory(suffix='-v2x', delete=False) as tmpdir:
        feedback = None
        attempt = 1
        while True:
            print(f"🤖 Attempt {attempt}:")
            if feedback:
                generated_code = codegen.provide_feedback('``\n' + feedback + '\n``\n')
            else:
                generated_code = codegen.generate_code(prompt, signature)
            termcolor.cprint('<<GENERATED', color='blue')
            print(generated_code)
            termcolor.cprint('GENERATED', color='blue')
            success, result = run_dslx_check(generated_code, signature, tests, tmpdir)
            if success:
                print(f"✅ Success on attempt {attempt}")
                print(generated_code)
                return
            print(f"❌ Error on attempt {attempt}")
            termcolor.cprint('<<OUTPUT', color='blue')
            print(result)
            termcolor.cprint('OUTPUT', color='blue')
            feedback = result
            attempt += 1

if __name__ == "__main__":
    main()
