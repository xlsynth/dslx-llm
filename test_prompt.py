# SPDX-License-Identifier: Apache-2.0

import os
import re
import tempfile
import subprocess
import sys

import pytest
import tiktoken

MD_FILE = 'prompt.md'

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

# Extract code samples from the markdown file
code_samples = extract_dslx_code_samples(MD_FILE)

@pytest.mark.parametrize('code_sample', code_samples)
def test_dslx_code_sample(code_sample):
    """Test each DSLX code sample by running it through the interpreter."""
    with tempfile.NamedTemporaryFile('w', suffix='.x', delete=False) as tmp:
        tmp.write(code_sample)
        tmp_filename = tmp.name

    cmd = ['dslx_interpreter_main', '--compare=jit', tmp_filename]
    cmd.append('--dslx_stdlib_path')
    cmd.append(os.environ['DSLX_STDLIB_PATH'])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"Non-zero exit code: {result.returncode}\n"
            f"Output: {result.stdout}\nError: {result.stderr}"
        )
    finally:
        os.remove(tmp_filename)


def test_prompt_size():
    """Tests tokens in prompt to check fit in context window."""
    encoding = tiktoken.encoding_for_model('gpt-4-turbo')

    # Read the file
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    token_count = len(encoding.encode(text))
    print('token count:', token_count, file=sys.stderr)

    # Check we stay comfortably within a reasonable context window.
    assert token_count <= 8 * 1024
