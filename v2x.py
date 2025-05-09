# SPDX-License-Identifier: Apache-2.0

import os
import optparse
import tempfile
from pathlib import Path
from typing import Optional
import re
import subprocess

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

def extract_fn_name_and_args(signature: str):
    # Matches: pub fn name(args...) -> ... {
    m = re.match(r'(?:pub\s+)?fn\s+(\w+)\s*\(([^)]*)\)', signature)
    if not m:
        raise ValueError(f'Could not parse function signature: {signature}')
    fn_name = m.group(1)
    args = m.group(2).strip()
    return fn_name, args

def make_equiv_quickcheck_modular(ref_mod: str, cand_mod: str, fn_name: str, args: str) -> str:
    # args: 'a: u32, b: u32' -> 'a, b'
    arg_names = [a.split(':')[0].strip() for a in args.split(',') if a.strip()]
    arglist = ', '.join(arg_names)
    return f"""
#[quickcheck]
fn prop_equiv({args}) -> bool {{
    {ref_mod}::{fn_name}({arglist}) == {cand_mod}::{fn_name}({arglist})
}}
"""

def run_prove_quickcheck(dslx_path: str, quickcheck_name: str, cwd: Optional[str] = None) -> tuple[bool, str, str]:
    cmd = [
        os.path.join(os.environ['XLSYNTH_TOOLS'], 'prove_quickcheck_main'),
        dslx_path,
        '--dslx_stdlib_path', tools.DSLX_STDLIB_PATH,
        '--test_filter', quickcheck_name
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)
    success = result.returncode == 0
    return success, result.stdout + result.stderr, ' '.join(cmd)

# -- Prompt construction
def make_prompt(verilog: str, reference_x: str, signature: str, suggestion: Optional[str] = None) -> str:
    suggestion_block = f"""
Suggestion (previous best attempt):
```
{suggestion}
```
""" if suggestion else ""
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
{suggestion_block}
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

def extract_imports_and_types(dslx_code: str) -> str:
    lines = dslx_code.splitlines()
    relevant = [line for line in lines if line.strip().startswith('import ') or line.strip().startswith('type ')]
    return '\n'.join(relevant)

# -- Main logic
def main():
    parser = optparse.OptionParser()
    parser.add_option('--verilog', type=str, help='Path to input Verilog (.v) file')
    parser.add_option('--reference', type=str, help='Path to reference DSLX (.x) file')
    parser.add_option('--model', type=str, default='gpt-4o', help='LLM model to use')
    parser.add_option('--max-retries', type=int, default=3, help='(ignored)')
    parser.add_option('--reasoning-effort', type=str, default='high', help='Reasoning effort for LLM')
    parser.add_option('--suggest', type=str, default=None, help='Path to a previous best result to suggest to the LLM')
    parser.add_option('--prove', action='store_true', default=True, help='Require equivalence proof via quickcheck (default: on)')
    parser.add_option('--no-prove', action='store_false', dest='prove', help='Disable equivalence proof')
    opts, args = parser.parse_args()

    if not opts.verilog or not opts.reference:
        parser.error('Both --verilog and --reference are required')

    verilog = read_file(opts.verilog)
    reference_x = read_file(opts.reference)
    suggestion = read_file(opts.suggest) if opts.suggest else None
    signature, tests = extract_signature_and_tests(reference_x)
    if not signature:
        raise ValueError('Could not extract DSLX function signature from reference .x file')

    prompt = make_prompt(verilog, reference_x, signature, suggestion)
    codegen = CodeGenerator(opts.model, opts.reasoning_effort, prompt)

    ref_fn_name, ref_args = extract_fn_name_and_args(signature)
    cand_fn_name = ref_fn_name  # Use the same name for candidate for modular import

    with tempfile.TemporaryDirectory(suffix='-v2x', delete=False) as tmpdir:
        feedback_history = []
        attempt = 1
        while True:
            print(f"🤖 Attempt {attempt}:")
            if feedback_history:
                feedback_text = ''
                for idx, (proposal, error) in enumerate(feedback_history, 1):
                    feedback_text += f"\n--- Attempt {idx} proposal ---\n{proposal}\n\n--- Attempt {idx} error ---\n{error}\n"
                generated_code = codegen.provide_feedback(feedback_text)
            else:
                generated_code = codegen.generate_code(prompt, signature)
            # Write candidate.x (rename function to match reference)
            cand_code = strip_fences(generated_code)
            cand_code_renamed = re.sub(r'(?:pub\s+)?fn\s+\w+', f'pub fn {cand_fn_name}', cand_code, count=1)
            cand_path = os.path.join(tmpdir, 'candidate.x')
            with open(cand_path, 'w') as f:
                f.write(cand_code_renamed)
            termcolor.cprint(f'<<GENERATED > {cand_path}', color='blue')
            print(generated_code)
            termcolor.cprint('GENERATED', color='blue')
            success, result = run_dslx_check(generated_code, signature, tests, tmpdir)
            if not success:
                print(f"❌ Error on attempt {attempt}")
                termcolor.cprint('<<OUTPUT', color='blue')
                print(result)
                termcolor.cprint('OUTPUT', color='blue')
                feedback_history.append((generated_code, result))
                attempt += 1
                continue
            if opts.prove:
                # Write reference.x
                ref_path = os.path.join(tmpdir, 'reference.x')
                ref_code = strip_fences(reference_x)
                with open(ref_path, 'w') as f:
                    f.write(ref_code)
                # Write candidate.x (rename function to match reference)
                cand_code = strip_fences(generated_code)
                cand_code_renamed = re.sub(r'(?:pub\s+)?fn\s+\w+', f'pub fn {cand_fn_name}', cand_code, count=1)
                cand_path = os.path.join(tmpdir, 'candidate.x')
                with open(cand_path, 'w') as f:
                    f.write(cand_code_renamed)
                # Extract imports/types from reference for scaffolding
                ref_imports_types = extract_imports_and_types(ref_code)
                # Write prove_equiv.x
                quickcheck = make_equiv_quickcheck_modular('reference', 'candidate', cand_fn_name, ref_args)
                combined = f"import std;\n{ref_imports_types}\nimport reference;\nimport candidate;\n\n{quickcheck}"
                combined_path = os.path.join(tmpdir, 'prove_equiv.x')
                with open(combined_path, 'w') as f:
                    f.write(combined)
                print('Running equivalence proof...')
                proof_success, proof_output, proof_cmd = run_prove_quickcheck(combined_path, 'prop_equiv', cwd=tmpdir)
                print(f"Prover command: {proof_cmd}")
                if proof_success:
                    print(f"✅ Equivalence proof succeeded on attempt {attempt}")
                    print(generated_code)
                    # Save the final proof file as the result
                    final_path = combined_path
                    print(f"Final accepted (proved) candidate written to: {final_path}")
                    print("Proof output confirming equivalence:")
                    print(proof_output)
                    return
                else:
                    print(f"❌ Equivalence proof failed on attempt {attempt}")
                    print(f"Prover command: {proof_cmd}")
                    termcolor.cprint('<<PROOF OUTPUT', color='blue')
                    print(proof_output)
                    termcolor.cprint('PROOF OUTPUT', color='blue')
                    feedback_history.append((generated_code, proof_output))
                    attempt += 1
                    continue
            print(f"✅ Success on attempt {attempt}")
            print(generated_code)
            final_path = os.path.join(tmpdir, 'final_candidate.x')
            with open(final_path, 'w') as f:
                f.write(strip_fences(generated_code))
            print(f"Final accepted candidate written to: {final_path}")
            return

if __name__ == "__main__":
    main()
