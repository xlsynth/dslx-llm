# Popcount Prefix

## Prompt

Write a DSLX function that returns the inclusive prefix population count for a
bit vector.

Use LSB-zero bit numbering: output lane `i` is the number of set bits in input
positions `0..i`, inclusive. For example, for `u4:0b1011`, the output is
`[1, 2, 2, 3]`.

The prologue will be automatically included, just implement the signature in
the output answer.

## Signature

```dslx-snippet
fn popcount_prefix<N: u32, COUNT_WIDTH: u32 = {std::clog2(N + u32:1)}>(x: bits[N]) -> uN[COUNT_WIDTH][N]
```

## Tests

```dslx-snippet
#[test]
fn test_popcount_prefix_u4_examples() {
    assert_eq(popcount_prefix<u32:4>(u4:0b0000), u3[4]:[0, 0, 0, 0]);
    assert_eq(popcount_prefix<u32:4>(u4:0b1011), u3[4]:[1, 2, 2, 3]);
    assert_eq(popcount_prefix<u32:4>(u4:0b1111), u3[4]:[1, 2, 3, 4]);
}

#[test]
fn test_popcount_prefix_u8_mixed_pattern() {
    assert_eq(popcount_prefix<u32:8>(u8:0b1011_0101), u4[8]:[1, 1, 2, 2, 3, 4, 4, 5]);
}

#[quickcheck(exhaustive)]
fn prop_u4_prefix_is_monotonic(x: u4) -> bool {
    let prefix = popcount_prefix<u32:4>(x);
    prefix[0] <= prefix[1] && prefix[1] <= prefix[2] && prefix[2] <= prefix[3]
}

#[quickcheck(exhaustive)]
fn prop_u4_prefix_steps_by_at_most_one(x: u4) -> bool {
    let prefix = popcount_prefix<u32:4>(x);
    prefix[0] <= u3:1 &&
        prefix[1] <= prefix[0] + u3:1 &&
        prefix[2] <= prefix[1] + u3:1 &&
        prefix[3] <= prefix[2] + u3:1
}

#[quickcheck(exhaustive)]
fn prop_u4_final_prefix_equals_popcount(x: u4) -> bool {
    let prefix = popcount_prefix<u32:4>(x);
    prefix[3] as u4 == std::popcount(x)
}

#[quickcheck]
fn prop_u8_final_prefix_equals_popcount(x: u8) -> bool {
    let prefix = popcount_prefix<u32:8>(x);
    prefix[7] as u8 == std::popcount(x)
}
```
