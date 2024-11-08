# SPDX-License-Identifier: Apache-2.0

import os
import re
import tempfile
import subprocess
import pytest

MD_FILE = 'prompt.md'

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
    with tempfile.NamedTemporaryFile('w', suffix='.dslx', delete=False) as tmp:
        tmp.write(code_sample)
        tmp_filename = tmp.name

    cmd = ['dslx_interpreter_main', '--compare=jit', tmp_filename]
    if 'DSLX_STDLIB_PATH' in os.environ:
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
