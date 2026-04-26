# Binary to One-hot Masked

## Prompt

Write a DSLX function that converts a binary index into a one-hot bit vector,
with an explicit valid input and a per-lane mask.

The input `index` uses LSB-zero bit numbering. The result should have exactly
one bit set at `index` only when all of these are true:

- `valid` is true
- `index < N`
- the corresponding bit in `mask` is set

Otherwise, return all zeroes. This should work for non-power-of-two widths,
where some binary index values are out of range.

The prologue will be automatically included, just implement the signature in
the output answer.

## Signature

```dslx-snippet
fn binary_to_onehot_masked<N: u32, INDEX_WIDTH: u32 = {std::clog2(N)}>(index: uN[INDEX_WIDTH], valid: bool, mask: bits[N]) -> bits[N]
```

## Tests

```dslx-snippet
#[test]
fn test_binary_to_onehot_masked_u4_examples() {
    assert_eq(binary_to_onehot_masked<u32:4>(u2:0, true, u4:0b1111), u4:0b0001);
    assert_eq(binary_to_onehot_masked<u32:4>(u2:1, true, u4:0b1111), u4:0b0010);
    assert_eq(binary_to_onehot_masked<u32:4>(u2:2, true, u4:0b1111), u4:0b0100);
    assert_eq(binary_to_onehot_masked<u32:4>(u2:3, true, u4:0b1111), u4:0b1000);
}

#[test]
fn test_binary_to_onehot_masked_disabled_or_masked_off() {
    assert_eq(binary_to_onehot_masked<u32:4>(u2:2, false, u4:0b1111), u4:0b0000);
    assert_eq(binary_to_onehot_masked<u32:4>(u2:2, true, u4:0b1011), u4:0b0000);
    assert_eq(binary_to_onehot_masked<u32:4>(u2:3, true, u4:0b1000), u4:0b1000);
    assert_eq(binary_to_onehot_masked<u32:4>(u2:1, true, u4:0b0000), u4:0b0000);
}

#[test]
fn test_binary_to_onehot_masked_non_power_of_two() {
    assert_eq(binary_to_onehot_masked<u32:5>(u3:0, true, u5:0b1_1111), u5:0b0_0001);
    assert_eq(binary_to_onehot_masked<u32:5>(u3:4, true, u5:0b1_1111), u5:0b1_0000);
    assert_eq(binary_to_onehot_masked<u32:5>(u3:4, true, u5:0b0_1111), u5:0b0_0000);
    assert_eq(binary_to_onehot_masked<u32:5>(u3:5, true, u5:0b1_1111), u5:0b0_0000);
    assert_eq(binary_to_onehot_masked<u32:5>(u3:7, true, u5:0b1_1111), u5:0b0_0000);
}

#[quickcheck(exhaustive)]
fn prop_u4_output_is_zero_or_onehot(index: u2, valid: bool, mask: u4) -> bool {
    let output = binary_to_onehot_masked<u32:4>(index, valid, mask);
    std::popcount(output) <= u4:1
}

#[quickcheck(exhaustive)]
fn prop_u4_output_never_uses_masked_lane(index: u2, valid: bool, mask: u4) -> bool {
    let output = binary_to_onehot_masked<u32:4>(index, valid, mask);
    (output & !mask) == u4:0
}

#[quickcheck(exhaustive)]
fn prop_u4_invalid_always_zero(index: u2, mask: u4) -> bool {
    binary_to_onehot_masked<u32:4>(index, false, mask) == u4:0
}

#[quickcheck(exhaustive)]
fn prop_u5_out_of_range_always_zero(index: u3, valid: bool, mask: u5) -> bool {
    if index >= u3:5 {
        binary_to_onehot_masked<u32:5>(index, valid, mask) == u5:0
    } else {
        true
    }
}
```
