# Kogge-Stone Adder

## Prompt

Implement a parameterized Kogge-Stone parallel-prefix adder in DSLX.

The implementation must compute the full Kogge-Stone carry structure (dense prefix network), not a ripple-carry adder, not a Brent-Kung adder, and not by using the built-in `+` operator to directly add `x` and `y`.

## Requirements

The following requirements will be checked by a separate "critic" model. The critic should treat comments as claims, not proof, and it should decide based on the actual structure of the DSLX code.

- id: kogge_stone_dense_prefix
  requirement: The carry computation must implement a Kogge-Stone parallel-prefix structure (dense prefix network). Evidence should include that in each stage with stride \(2^k\) (for \(k = 0, 1, 2, ...\)), for every index `i` where `i >= 2^k`, the code computes updated prefix signals at `i` using prefix signals from the previous stage at both `i` and `i - 2^k` (or an equivalent formulation). It is not sufficient to merely iterate over all indices; the data dependencies must match the dense Kogge-Stone combine pattern.

- id: not_brent_kung_or_ripple
  requirement: The implementation must not be a sparse prefix network (e.g. Brent-Kung) and must not be a linear ripple-carry chain. Evidence should address the computation graph: show that the code performs the combine operator for essentially every `i >= 2^k` in each stage \(k\), and that the carries are derived from the final prefix results, not propagated bit-by-bit through a single sequential carry variable.

- id: uses_generate_propagate_prefix_op
  requirement: The implementation must compute per-bit generate/propagate signals and use a prefix-combine operator across stages to compute carries. Evidence should include the definition of `g`/`p` (or equivalent) and a stage-wise combine rule that matches a standard prefix adder formulation.

- id: no_builtin_full_add
  requirement: The implementation must not compute the sum via a direct `x + y` (or `x + y + ...`) expression on the full-width operands. It is OK to use small-width arithmetic for loop indices and constant expressions, but the adder itself must be structurally realized via generate/propagate and prefix combination.

## Signature

```dslx-snippet
fn kogge_stone_add<N: u32>(x: uN[N], y: uN[N], carry_in: bool) -> (bool, uN[N])
```

## Prologue

```dslx-snippet
// dslx_run_options: --warnings_as_errors=false
```

## Tests

```dslx-snippet
#[test]
fn test_4b_selected() {
    const N = u32:4;
    let (c0, sum0) = kogge_stone_add<N>(u4:0, u4:0, false);
    assert_eq((c0, sum0), (false, u4:0));

    let (c1, sum1) = kogge_stone_add<N>(u4:1, u4:2, false);
    assert_eq((c1, sum1), (false, u4:3));

    let (c2, sum2) = kogge_stone_add<N>(u4:0xf, u4:1, false);
    assert_eq((c2, sum2), (true, u4:0));

    let (c3, sum3) = kogge_stone_add<N>(u4:0xf, u4:0, true);
    assert_eq((c3, sum3), (true, u4:0));
}

#[quickcheck(exhaustive)]
fn quickcheck_compare_vs_std_with_cin(x: u4, y: u4, carry_in: bool) -> bool {
    let (overflow1, sum1) = std::uadd_with_overflow<u32:4>(x, y);
    let cin_as_u4 = if carry_in { u4:1 } else { u4:0 };
    let (overflow2, sum2) = std::uadd_with_overflow<u32:4>(sum1, cin_as_u4);
    let want_carry = overflow1 || overflow2;
    let want_sum = sum2;

    let (got_carry, got_sum) = kogge_stone_add<u32:4>(x, y, carry_in);
    got_carry == want_carry && got_sum == want_sum
}

#[quickcheck(exhaustive)]
fn quickcheck_compare_vs_std_with_cin_u1(x: u1, y: u1, carry_in: bool) -> bool {
    let (overflow1, sum1) = std::uadd_with_overflow<u32:1>(x, y);
    let cin_as_u1 = if carry_in { u1:1 } else { u1:0 };
    let (overflow2, sum2) = std::uadd_with_overflow<u32:1>(sum1, cin_as_u1);
    let want_carry = overflow1 || overflow2;
    let want_sum = sum2;

    let (got_carry, got_sum) = kogge_stone_add<u32:1>(x, y, carry_in);
    got_carry == want_carry && got_sum == want_sum
}

#[quickcheck(exhaustive)]
fn quickcheck_compare_vs_std_with_cin_u2(x: u2, y: u2, carry_in: bool) -> bool {
    let (overflow1, sum1) = std::uadd_with_overflow<u32:2>(x, y);
    let cin_as_u2 = if carry_in { u2:1 } else { u2:0 };
    let (overflow2, sum2) = std::uadd_with_overflow<u32:2>(sum1, cin_as_u2);
    let want_carry = overflow1 || overflow2;
    let want_sum = sum2;

    let (got_carry, got_sum) = kogge_stone_add<u32:2>(x, y, carry_in);
    got_carry == want_carry && got_sum == want_sum
}

#[quickcheck(exhaustive)]
fn quickcheck_compare_vs_std_with_cin_u3(x: u3, y: u3, carry_in: bool) -> bool {
    let (overflow1, sum1) = std::uadd_with_overflow<u32:3>(x, y);
    let cin_as_u3 = if carry_in { u3:1 } else { u3:0 };
    let (overflow2, sum2) = std::uadd_with_overflow<u32:3>(sum1, cin_as_u3);
    let want_carry = overflow1 || overflow2;
    let want_sum = sum2;

    let (got_carry, got_sum) = kogge_stone_add<u32:3>(x, y, carry_in);
    got_carry == want_carry && got_sum == want_sum
}
```
