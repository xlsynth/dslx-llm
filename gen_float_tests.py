# SPDX-License-Identifier: Apache-2.0

import sys
import optparse
import subprocess
from pathlib import Path


# Functions supported by testfloat_gen
TESTFLOAT_GEN_FUNCTIONS = (
    "add",
    "eq",
    "sub",
    "le",
    "mul",
    "lt",
    "mulAdd",
    "eq_signaling",
    "div",
    "le_quiet",
    "rem",
    "lt_quiet",
    "sqrt",
)

# Mapping of rounding modes to u3 space
TESTFLOAT_GEN_ROUNDING = {
    "near_even": 0,
    "minMag": 1,
    "max": 2,
    "min": 3,
    "near_maxMag": 4,
}

TESTFLOAT_GEN_FLAGS = {
    0x10: "invalid",
    0x04: "huge",  # overflow
    0x02: "tiny",  # underflow
    0x01: "inexact",
    # 0x08: "pass_a_div_zero",  # marked as infinite but used for div by 0
}

FLAGS_IEEE_STATUS = {
    "invalid": 0x04,
    "infinite": 0x02,
    "huge": 0x10,
    "tiny": 0x08,
    "inexact": 0x20,
    "zero": 0x01,
}

# Precisions supported by testfloat_gen
PRECISION_TO_DSLX_TYPE = {
    "f16": 16,
    "f32": 32,
    "f64": 64,
    "f128": 128,
}
PRECISION_TO_EXP_SIZE = {
    "f16": 5,
    "f32": 8,
    "f64": 11,
    "f128": 15,
}

def run_testfloat_gen(args):
    """
    Runs testfloat_gen with provided parameters and yields tuples with inputs, output and status.
    """
    command = [
        args.testfloat_gen,
        "-seed", str(args.seed),
    ]
    if args.n_cases is not None:
        command.extend(["-n", str(args.n_cases)])
    if args.rounding is not None:
        command.append(f"-r{args.rounding}")
    command.append(f"{args.precision}_{args.function}")

    gen = subprocess.run(command, capture_output=True, text=True)

    try:
        gen.check_returncode()
    except subprocess.CalledProcessError:
        print(f"testfloat_gen failed: {gen.stderr}", file=sys.stderr)
        return

    for line in gen.stdout.splitlines():
        data = line.split(" ")
        inp, out, status = data[:-2], data[-2], data[-1]
        yield inp, out, status

def create_test(args, inp, out, flags, i):
    # Calculate status
    status_int = 0
    if args.include_status:
        flags = int(flags, base=16)
        status = [v for k, v in TESTFLOAT_GEN_FLAGS.items() if flags & k]
        out_bin = f"{int(out, base=16):b}".zfill(PRECISION_TO_DSLX_TYPE[args.precision])
        # +/-Zero
        if set(out_bin[1:]) == {"0"}:
            status.append("zero")
        if set(out_bin[1:1 + PRECISION_TO_EXP_SIZE[args.precision]]) == {"1"} and set(out_bin[1 + PRECISION_TO_EXP_SIZE[args.precision]:]) == {"0"}:
            status.append("infinite")
        for st in status:
            status_int |= FLAGS_IEEE_STATUS[st]
    # Prepare test definition
    rnd_suffix = ""
    if args.rounding is not None:
        rnd_suffix = f"_{args.rounding}"
    code = (
        "#[test]\n"
        f"fn {args.tests_name}{rnd_suffix}_{i}() {{\n"
        f"    {args.tested_func}("
    )
    # Add args
    for j, v in enumerate(inp + [out]):
        if j != 0:
            code += ", "
        code += f"uN[{PRECISION_TO_DSLX_TYPE[args.precision]}]:0x{v}"
    if args.rounding is not None:
        code += f", u3:{TESTFLOAT_GEN_ROUNDING[args.rounding]}"
    if args.include_status:
        code += f", u6:0x{status_int:x}"
    # Close test body
    code += ");\n}\n"
    return code

def generate_tests(args):
    exp_size = PRECISION_TO_EXP_SIZE[args.precision]
    size = PRECISION_TO_DSLX_TYPE[args.precision]
    first_test = True

    output_file = Path(args.output_file)
    output_file.parent.mkdir(exist_ok=True)
    output_fd = output_file.open("w")
    try:
        for i, (inp, out, flags) in enumerate(run_testfloat_gen(args)):
            if args.only_numbers:
                # Skip cases with NaNs or Infs
                bits = [f"{int(h, base=16):b}".zfill(size) for h in inp + [out]]
                not_numbers = [b[1:].startswith('1' * exp_size) for b in bits]
                if any(not_numbers):
                    continue

            code = "" if first_test else "\n"
            # Generate test and add write to the file
            code += create_test(args, inp, out, flags, i)
            output_fd.write(code)
            first_test = False
    except Exception:
        output_fd.close()
        raise


def create_parser():
    parser = optparse.OptionParser()
    parser.add_option("--testfloat-gen", type=str, default="testfloat_gen", help="Path to a testfloat_gen")
    parser.add_option("--only-numbers", action="store_true", help="Whether tests should include only numbers, Inf/NaN will not be present")
    parser.add_option("--function", choices=TESTFLOAT_GEN_FUNCTIONS, default=TESTFLOAT_GEN_FUNCTIONS[0], help="Generate tests for a given function")
    parser.add_option("--precision", choices=list(PRECISION_TO_DSLX_TYPE.keys()), default=list(PRECISION_TO_DSLX_TYPE.keys())[0], help="Generate tests for a given precision")
    parser.add_option("--tested-func", type=str, default="test_fp_add", help="Function called by tests")
    parser.add_option("--tests-name", type=str, default="generated_test", help="Name of generated tests")
    parser.add_option("--n-cases", type=int, default=None, help="Number of N cases to generate")
    parser.add_option("--seed", type=int, default=12345, help="Seed for testfloat_gen")
    parser.add_option("--rounding", choices=list(TESTFLOAT_GEN_ROUNDING.keys()), default=None, help="Used rounding mode")
    parser.add_option("--include-status", action="store_true", help="Use generated flags as IEEE status")
    parser.add_option("--output-file", type=str, default=None, help="Path where generated tests will be saved")
    return parser


def main():
    parser = create_parser()
    opts, args = parser.parse_args()

    generate_tests(opts)

if __name__ == "__main__":
    main()
