# SPDX-License-Identifier: Apache-2.0

import pytest
import tempfile

from gen_float_tests import create_parser, generate_tests

TESTS_SQRT_NUMBERS = """\
#[test]
fn {test_name}_1() {{
    {func_name}(uN[16]:0x36F7, uN[16]:0x3947);
}}

#[test]
fn {test_name}_2() {{
    {func_name}(uN[16]:0x0000, uN[16]:0x0000);
}}

#[test]
fn {test_name}_3() {{
    {func_name}(uN[16]:0x6837, uN[16]:0x51CF);
}}

#[test]
fn {test_name}_5() {{
    {func_name}(uN[16]:0x0001, uN[16]:0x0C00);
}}
"""

TESTS_DIV = """\
#[test]
fn {test_name}_0() {{
    {func_name}(uN[32]:0xBE842000, uN[32]:0xC1F80000, uN[32]:0x3C086319);
}}

#[test]
fn {test_name}_1() {{
    {func_name}(uN[32]:0x00000000, uN[32]:0xC11FFFFE, uN[32]:0x80000000);
}}

#[test]
fn {test_name}_2() {{
    {func_name}(uN[32]:0x68801FFF, uN[32]:0x4F000087, uN[32]:0x59001F78);
}}

#[test]
fn {test_name}_3() {{
    {func_name}(uN[32]:0xF8FE001F, uN[32]:0x00000000, uN[32]:0xFF800000);
}}
"""

@pytest.mark.parametrize(
    "func,precision,tested_func,tests_name,only_numbers,expected_form",
    [
        ("sqrt", "f16", "f16_sqrt", "test_sqrt", True, TESTS_SQRT_NUMBERS),
        ("div", "f32", "f32_div", "test_div", False, TESTS_DIV),
    ]
)
def test_generate_tests(func, precision, tested_func, tests_name, only_numbers, expected_form):
    parser = create_parser()
    opts, _ = parser.parse_args([])
    # Set parameters
    opts.only_numbers = only_numbers
    opts.tested_func = tested_func
    opts.tests_name = tests_name
    opts.function = func
    opts.precision = precision
    # Generate tests
    with tempfile.NamedTemporaryFile("r") as f:
        opts.output_file = f.name
        generate_tests(opts)
        generated_tests = f.read()
    # Compare results
    expected_result = expected_form.format(test_name=tests_name, func_name=tested_func)
    assert generated_tests.startswith(expected_result)
