# SPDX-License-Identifier: Apache-2.0
"""Validate the DSLX acceptance predicate with independent Python arithmetic.

No implementation of the target DSLX function is embedded or generated here.
The temporary expected-value data is used only to validate the checker itself.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from itertools import product
from pathlib import Path
import random
import re
import subprocess

from eval_shared import parse_sample
import tools

SAMPLE = Path(__file__).resolve().parent / 'samples/fixed_point_mac.md'


def oracle(a: int, b: int, acc: int, w: int, f: int) -> int:
    """Exact rational expression, Python's specified ties-to-even rounding."""
    rounded = round(Fraction(a * b, 1 << f) + acc)
    return max(-(1 << (w - 1)), min((1 << (w - 1)) - 1, rounded))


def decimal_oracle(a: int, b: int, acc: int, w: int, f: int) -> int:
    """Independent arithmetic/rounding implementation, no binary floating point."""
    with localcontext() as ctx:
        ctx.prec = 100
        scale = Decimal(2) ** f
        real_value = (Decimal(a) / scale) * (Decimal(b) / scale) + Decimal(acc) / scale
        code = int((real_value * scale).to_integral_value(rounding=ROUND_HALF_EVEN))
    lo, hi = -(2 ** (w - 1)), 2 ** (w - 1) - 1
    return min(hi, max(lo, code))


def signed(raw: int, w: int) -> int:
    return raw if raw < (1 << (w - 1)) else raw - (1 << w)


def checker_source() -> str:
    tests = parse_sample(SAMPLE).tests
    match = re.search(r'(?ms)^fn mac_result_is_nearest_even\(.*?^}\n', tests)
    assert match is not None
    return match.group(0)


def run_dslx(code: str, tmp_path: Path, name: str) -> subprocess.CompletedProcess[str]:
    path = tmp_path / (name + '.x')
    path.write_text(code)
    return subprocess.run([tools.DSLX_INTERPRETER_MAIN, str(path), '--dslx_stdlib_path',
                           tools.DSLX_STDLIB_PATH, '--compare=jit', '--seed=12345'],
                          capture_output=True, text=True, timeout=120)


def test_oracles_agree_exhaustively() -> None:
    for w in range(2, 6):
        for f in range(w):
            for a, b, acc in product(range(-(1 << (w-1)), 1 << (w-1)), repeat=3):
                assert oracle(a, b, acc, w, f) == decimal_oracle(a, b, acc, w, f)


def test_checker_accepts_exactly_the_oracle_result(tmp_path: Path) -> None:
    # Up to 16 input bits, including the proposed result: test every possible
    # correct AND incorrect claim, not merely the reference's positive cases.
    tests = []
    for w in range(2, 5):
        for f in range(w):
            values = [oracle(signed(a, w), signed(b, w), signed(c, w), w, f)
                      for a, b, c in product(range(1 << w), repeat=3)]
            lines = [', '.join(map(str, values[i:i+16])) for i in range(0, len(values), 16)]
            data = ',\n        '.join(lines)
            tests.append(f"""#[quickcheck(exhaustive)]
fn check_w{w}_f{f}(a: sN[{w}], b: sN[{w}], acc: sN[{w}], proposed: sN[{w}]) -> bool {{
    let expected = sN[{w}][{len(values)}]:[
        {data}
    ];
    let index = (((a as uN[{w}]) as u32) << u32:{2*w})
              | (((b as uN[{w}]) as u32) << u32:{w})
              | ((acc as uN[{w}]) as u32);
    let numerator = (a as sN[128]) * (b as sN[128]) + (acc as sN[128]) * sN[128]:{1<<f};
    mac_result_is_nearest_even(numerator, sN[128]:{1<<f}, proposed as sN[128],
                              sN[128]:{-(1<<(w-1))}, sN[128]:{(1<<(w-1))-1}) ==
    (proposed == expected[index])
}}""")
    result = run_dslx(checker_source() + '\n' + '\n'.join(tests), tmp_path, 'checker_exhaustive')
    assert result.returncode == 0, result.stderr
    assert '9 quickcheck(s) ran' in result.stderr


def test_checker_wide_independent_vectors(tmp_path: Path) -> None:
    rng = random.Random(12345)
    lines = ['#[test]', 'fn wide_claims() {']
    for w, f in ((5, 0), (5, 4), (8, 3), (16, 0), (16, 8), (16, 15), (32, 0), (32, 16), (32, 31)):
        lo, hi = -(1 << (w-1)), (1 << (w-1))-1
        for _ in range(128):
            a, b, acc = [rng.randrange(lo, hi+1) for _ in range(3)]
            expected = decimal_oracle(a, b, acc, w, f)
            assert expected == oracle(a, b, acc, w, f)
            numerator = a*b + acc*(1<<f)
            for proposed in sorted({expected, expected-1, expected+1, lo, hi, lo-1, hi+1}):
                correct = str(proposed == expected).lower()
                lines.append(f'    assert_eq(mac_result_is_nearest_even(sN[128]:{numerator}, '
                             f'sN[128]:{1<<f}, sN[128]:{proposed}, sN[128]:{lo}, sN[128]:{hi}), {correct});')
    result = run_dslx(checker_source() + '\n' + '\n'.join(lines + ['}']), tmp_path, 'checker_wide')
    assert result.returncode == 0, result.stderr
