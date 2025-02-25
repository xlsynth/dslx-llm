# SPDX-License-Identifier: Apache-2.0

import dataclasses
import os
import re
import tempfile
import subprocess
import sys

import pytest
import tiktoken

PROMPT_MD_FILE = 'prompt.md'
XLSYNTH_TOOLS_DIR = os.environ['XLSYNTH_TOOLS']
DSLX_INTERPRETER_MAIN = os.path.join(XLSYNTH_TOOLS_DIR, 'dslx_interpreter_main')
TYPECHECK_MAIN = os.path.join(XLSYNTH_TOOLS_DIR, 'typecheck_main')

assert 'DSLX_STDLIB_PATH' in os.environ, 'Please add DSLX_STDLIB_PATH to your environment variables; e.g. `export DSLX_STDLIB_PATH=$HOME/opt/xlsynth/latest/xls/dslx/stdlib/`'

# Regular expression to find code fences labeled 'dslx'
CODE_FENCE_RE = re.compile(
    r'^```dslx\s*\n(.*?)^```',
    re.DOTALL | re.MULTILINE
)

def extract_dslx_code_samples(md_file):
    """Extracts all code samples labeled 'dslx' from the markdown file."""
    with open(md_file, 'r') as f:
        md_content = f.read()
    code_samples = CODE_FENCE_RE.findall(md_content)
    return code_samples


@dataclasses.dataclass
class CodeSample:
    name: str
    content: str


def create_sample_with_stub(filename: str, md_content: str) -> CodeSample:
    """Creates a sample with a stub for the DSLX code sample."""
    # Extract the signature -- it lives in the subsection called '## Signature'
    # Within a fence in that section marked '```dslx-snippet'
    signature_re = re.compile(r'^## Signature\s*\n(.*?)^##', re.DOTALL | re.MULTILINE)
    signature_match = signature_re.search(md_content)
    if not signature_match:
        raise ValueError(f'No signature found in {filename}')
    signature = signature_match.group(1)
    signature = signature.replace('```dslx-snippet', '')
    signature = signature.replace('```', '')
    signature = signature.strip()
    signatures = signature.splitlines()

    # See if there is a Prologue section, if so we extract that to include before the stubs.
    prologue_re = re.compile(r'^## Prologue\s*\n(.*?)^##', re.DOTALL | re.MULTILINE)
    prologue_match = prologue_re.search(md_content)
    if prologue_match:
        prologue = prologue_match.group(1)
        prologue = prologue.replace('```dslx', '')
        prologue = prologue.replace('```', '')
        prologue = prologue.strip()
    else:
        prologue = ''

    # Extract the tests -- they live in the subsection called '## Tests'
    # That should be the last subsection in the file.
    # The test content lives inside of a fence marked '```dslx'
    tests_re = re.compile(r'^## Tests\n(.*)', re.DOTALL | re.MULTILINE)
    tests_match = tests_re.search(md_content)
    if not tests_match:
        raise ValueError(f'No tests found in {filename}')
    tests = tests_match.group(1)
    assert 'dslx-snippet' in tests, f'No dslx-snippet found in {filename}'
    tests = tests.replace('```dslx-snippet', '')
    tests = tests.replace('```', '')
    tests = tests.strip()

    # Create a stub for the signature that looks like:
    # $SIGNATURE { fail!("unimplemented", zero!<ReturnType>()) }
    # This means we have to hackily parse the return type out of the signature, but that's not too bad because it's after the arrow.
    return_type_re = re.compile(r'->\s*(.*)')
    return_type_match = return_type_re.search(signature)
    if not return_type_match:
        raise ValueError(f'No return type found in {filename}')
    return_type = return_type_match.group(1)

    stub_lines: list[str] = []
    for signature in signatures:
        stub_lines.append(f'{signature} {{ fail!("unimplemented", zero!<{return_type}>()) }}\n')
    stubs: str = '\n'.join(stub_lines)

    return CodeSample(name=os.path.splitext(filename)[0], content=f'import std;\n{prologue}\n{stubs}\n{tests}')


def create_samples_with_stubs() -> list[CodeSample]:
    """Creates samples with stubs for each DSLX code sample."""
    results = []
    for filename in os.listdir('samples'):
        if not filename.endswith('.md'):
            continue
        with open(f'samples/{filename}', 'r') as f:
            md_content = f.read()
        results.append(create_sample_with_stub(filename, md_content))
    return results


# Extract code samples from the markdown file
PROMPT_CODE_SAMPLES = extract_dslx_code_samples(PROMPT_MD_FILE)
SAMPLES_WITH_STUBS = create_samples_with_stubs()


def run_on_single_file(binary: str, code_sample: str, more_flags: tuple[str, ...] = ()):
    with tempfile.NamedTemporaryFile('w', suffix='.x', delete=False) as tmp:
        tmp.write(code_sample)
        tmp_filename = tmp.name

    print(f'Running {binary} ({os.path.realpath(binary)} on {tmp_filename} ...')
    print('Contents:\n<<EOF\n', code_sample, '\n<<EOF\n', sep='')

    cmd = [binary]
    cmd.extend(list(more_flags))
    cmd.append(tmp_filename)
    cmd.append('--dslx_stdlib_path')
    cmd.append(os.environ['DSLX_STDLIB_PATH'])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"Non-zero exit code: {result.returncode}\n"
            f"stdout:\n<<STDOUT\n{result.stdout}\nSTDOUT\n"
            f"stderr:\n<<STDERR\n{result.stderr}\nSTDERR\n"
        )
    finally:
        os.remove(tmp_filename)


@pytest.mark.parametrize('code_sample', PROMPT_CODE_SAMPLES)
def test_prompt_code_sample(code_sample: str):
    """Tests DSLX code samples in prompt by running through the interpreter."""
    run_on_single_file(DSLX_INTERPRETER_MAIN, code_sample, more_flags=('--compare=jit',))


@pytest.mark.parametrize('sample_with_stub', SAMPLES_WITH_STUBS, ids=lambda x: x.name)
def test_samples_with_stub_typecheck(sample_with_stub: CodeSample):
    """Tests that DSLX tests pass with a stub signature."""
    run_on_single_file(TYPECHECK_MAIN, sample_with_stub.content)


def test_prompt_size():
    """Tests tokens in prompt to check fit in context window."""
    encoding = tiktoken.encoding_for_model('gpt-4-turbo')

    # Read the file
    with open(PROMPT_MD_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    token_count = len(encoding.encode(text))
    print('token count:', token_count, file=sys.stderr)

    # Check we stay comfortably within a reasonable context window.
    assert token_count <= 8 * 1024
