# Carry-Save Adder Tree (CSA Tree)

## Prompt

Implement a carry-save adder (CSA) reduction tree that reduces `K` `N`-bit operands into two `N`-bit operands `(sum, carry)` such that:

`sum + (carry << 1)` equals the naive sum of the `K` operands (modulo \(2^N\)).

Use 3:2 compressors (bitwise full-adder slices) as the primitive. Do not compute the full reduction by folding with `+` across the `K` operands.

Briefly describe (in a short comment) the reduction schedule you used (e.g. Wallace/Dadda-style rounds that group operands in triples each round).

## Requirements

The following requirements will be checked by a separate "critic" model. The critic should treat comments as claims, not proof, and it should decide based on the actual structure of the DSLX code.

- id: has_3_2_compressor
  requirement: The solution must implement a 3:2 compressor on same-width operands (a carry-save adder primitive) that produces `(sum, carry)` with bitwise equations equivalent to `sum = a ^ b ^ c` and `carry = (a & b) | (a & c) | (b & c)` (carry intended to be left-shifted by 1 when forming a conventional sum).

- id: uses_csa_tree_reduction
  requirement: The reduction from `K` operands to two operands must be performed by repeatedly applying the 3:2 compressor (or an equivalent CSA primitive) in rounds/levels until only two operands remain. It is not sufficient to implement a single compressor and then use `+` to combine everything.

- id: no_linear_plus_fold
  requirement: The implementation must not compute the final answer by folding with `+` across all `K` operands (e.g. `for (...) { acc + x }`). Using a single final carry-propagate addition to combine the final `(sum, carry << 1)` is allowed.

- id: works_for_non_pow2_k
  requirement: The implementation must handle `K` values that are not powers of two (e.g. `K = 3`, `K = 5`, `K = 7`). It may assume `K >= 1` and should clearly document any additional constraints it requires.

## Signature

```dslx-snippet
fn csa3<N: u32>(a: uN[N], b: uN[N], c: uN[N]) -> (uN[N], uN[N])

fn csa_tree<N: u32, K: u32>(xs: uN[N][K]) -> (uN[N], uN[N])
```

## Tests

```dslx-snippet
fn combine_csa<N: u32>(sum: uN[N], carry: uN[N]) -> uN[N] {
    sum + (carry << u32:1)
}

#[test]
fn test_csa3_public_api() {
    let (sum, carry) = csa3<u32:4>(u4:1, u4:2, u4:3);
    assert_eq(sum, u4:0);
    assert_eq(carry, u4:3);
}

#[test]
fn test_small_handpicked() {
    // K = 1, N = 4
    let xs1 = u4[1]:[u4:9];
    let (sum1, carry1) = csa_tree<u32:4, u32:1>(xs1);
    assert_eq(combine_csa(sum1, carry1), u4:9);

    // K = 2, N = 4
    let xs2 = u4[2]:[u4:15, u4:1];
    let (sum2, carry2) = csa_tree<u32:4, u32:2>(xs2);
    assert_eq(combine_csa(sum2, carry2), u4:0);

    // K = 3, N = 4
    let xs3 = u4[3]:[u4:1, u4:2, u4:3];
    let (sum3, carry3) = csa_tree<u32:4, u32:3>(xs3);
    assert_eq(combine_csa(sum3, carry3), u4:6);

    // K = 5, N = 4 (non power-of-two K)
    let xs5 = u4[5]:[u4:15, u4:1, u4:2, u4:3, u4:4];
    let (sum5, carry5) = csa_tree<u32:4, u32:5>(xs5);
    assert_eq(combine_csa(sum5, carry5), u4:9);
}

#[quickcheck(exhaustive)]
fn prop_csa3_u3(a: u3, b: u3, c: u3) -> bool {
    let (sum, carry) = csa3<u32:3>(a, b, c);
    sum == (a ^ b ^ c) && carry == ((a & b) | (a & c) | (b & c))
}

#[quickcheck(exhaustive)]
fn prop_csa_tree_u4_k1(a: u4) -> bool {
    let xs = u4[1]:[a];
    let (sum, carry) = csa_tree<u32:4, u32:1>(xs);
    combine_csa(sum, carry) == a
}

#[quickcheck(exhaustive)]
fn prop_csa_tree_u4_k2(a: u4, b: u4) -> bool {
    let xs = u4[2]:[a, b];
    let (sum, carry) = csa_tree<u32:4, u32:2>(xs);
    combine_csa(sum, carry) == a + b
}

#[quickcheck(exhaustive)]
fn prop_csa_tree_u3_k3(a: u3, b: u3, c: u3) -> bool {
    let xs = u3[3]:[a, b, c];
    let (sum, carry) = csa_tree<u32:3, u32:3>(xs);
    combine_csa(sum, carry) == a + b + c
}

#[quickcheck]
fn prop_csa_tree_u4_k5(a: u4, b: u4, c: u4, d: u4, e: u4) -> bool {
    let xs = u4[5]:[a, b, c, d, e];
    let (sum, carry) = csa_tree<u32:4, u32:5>(xs);
    combine_csa(sum, carry) == a + b + c + d + e
}

#[quickcheck]
fn prop_csa_tree_u5_k7(a: u5, b: u5, c: u5, d: u5, e: u5, f: u5, g: u5) -> bool {
    let xs = u5[7]:[a, b, c, d, e, f, g];
    let (sum, carry) = csa_tree<u32:5, u32:7>(xs);
    combine_csa(sum, carry) == a + b + c + d + e + f + g
}
```
