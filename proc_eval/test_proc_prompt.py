# SPDX-License-Identifier: Apache-2.0

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools
from dslx_run_flags import split_dslx_run_flags_from_code
from eval_shared import build_full_code, parse_sample

PROC_PROMPT_MD_FILE = 'proc_eval/prompt.md'
PROC_SAMPLES_DIR = Path('proc_eval/samples')

CODE_FENCE_RE = re.compile(
    r'^```dslx\s*\n(.*?)^```',
    re.DOTALL | re.MULTILINE
)

REFERENCE_IMPLEMENTATIONS = {
    'counter': """
proc Counter {
    out_ch: chan<u32> out;

    config(out_ch: chan<u32> out) {
        (out_ch,)
    }

    init { u32:0 }

    next(state: u32) {
        let tok = join();
        let tok = send(tok, out_ch, state);
        state + u32:1
    }
}
""".strip(),
}


def extract_dslx_code_samples(md_file: str) -> list[str]:
    with open(md_file, 'r') as f:
        md_content = f.read()
    return CODE_FENCE_RE.findall(md_content)


def run_on_single_file(code_sample: str):
    cleaned, extra_flags = split_dslx_run_flags_from_code(code_sample)
    with tempfile.NamedTemporaryFile('w', suffix='.x', delete=False) as tmp:
        tmp.write(cleaned)
        tmp_filename = tmp.name

    cmd = [
        tools.DSLX_INTERPRETER_MAIN,
        tmp_filename,
        '--dslx_stdlib_path',
        tools.DSLX_STDLIB_PATH,
        '--type_inference_v2=true',
        *extra_flags,
        '--compare=none',
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"Non-zero exit code: {result.returncode}\n"
            f"stdout:\n<<STDOUT\n{result.stdout}\nSTDOUT\n"
            f"stderr:\n<<STDERR\n{result.stderr}\nSTDERR\n"
        )
    finally:
        os.remove(tmp_filename)


PROMPT_CODE_SAMPLES = extract_dslx_code_samples(PROC_PROMPT_MD_FILE)
PROC_SAMPLE_FILES = sorted(PROC_SAMPLES_DIR.glob('*.md'))


@pytest.mark.parametrize('code_sample', PROMPT_CODE_SAMPLES)
def test_proc_prompt_code_sample(code_sample: str):
    run_on_single_file(code_sample)


@pytest.mark.parametrize('sample_path', PROC_SAMPLE_FILES, ids=lambda path: path.stem)
def test_proc_sample_with_reference_implementation(sample_path: Path):
    sample = parse_sample(sample_path)
    assert sample_path.stem in REFERENCE_IMPLEMENTATIONS, (
        f'Add a reference implementation for proc sample: {sample_path.stem}'
    )
    reference = REFERENCE_IMPLEMENTATIONS[sample_path.stem]
    full_code = build_full_code(reference, sample, test_file=None)
    run_on_single_file(full_code)
