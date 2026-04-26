# Thermometer to Binary

## Prompt

Write a DSLX function that decodes a thermometer-coded bit vector into a binary
count and reports whether the input is a valid thermometer code.

Use LSB-zero orientation. A valid input has contiguous one bits from the LSB
side followed by zero bits, so `0b0000`, `0b0001`, `0b0011`, and `0b1111` are
valid for a 4-bit input. Inputs with holes or ones above zeroes, such as
`0b0101` or `0b1110`, are invalid.

Always return the number of set bits as the count. The validity flag reports
whether the input had the contiguous-LSB-ones thermometer shape.

The prologue will be automatically included, just implement the signature in
the output answer.

## Signature

```dslx-snippet
fn thermometer_to_binary<N: u32, COUNT_WIDTH: u32 = {std::clog2(N + u32:1)}>(x: bits[N]) -> (bool, uN[COUNT_WIDTH])
```

## Tests

```dslx-snippet
#[test]
fn test_thermometer_to_binary_valid_u4_table() {
    assert_eq(thermometer_to_binary<u32:4>(u4:0b0000), (true, u3:0));
    assert_eq(thermometer_to_binary<u32:4>(u4:0b0001), (true, u3:1));
    assert_eq(thermometer_to_binary<u32:4>(u4:0b0011), (true, u3:2));
    assert_eq(thermometer_to_binary<u32:4>(u4:0b0111), (true, u3:3));
    assert_eq(thermometer_to_binary<u32:4>(u4:0b1111), (true, u3:4));
}

#[test]
fn test_thermometer_to_binary_invalid_u4_examples() {
    assert_eq(thermometer_to_binary<u32:4>(u4:0b0010), (false, u3:1));
    assert_eq(thermometer_to_binary<u32:4>(u4:0b0101), (false, u3:2));
    assert_eq(thermometer_to_binary<u32:4>(u4:0b1011), (false, u3:3));
    assert_eq(thermometer_to_binary<u32:4>(u4:0b1110), (false, u3:3));
}

#[test]
fn test_thermometer_to_binary_u8_examples() {
    assert_eq(thermometer_to_binary<u32:8>(u8:0b0000_1111), (true, u4:4));
    assert_eq(thermometer_to_binary<u32:8>(u8:0b0010_1111), (false, u4:5));
    assert_eq(thermometer_to_binary<u32:8>(u8:0b1111_1111), (true, u4:8));
}

#[quickcheck(exhaustive)]
fn prop_u4_count_equals_popcount(x: u4) -> bool {
    let (_, count) = thermometer_to_binary<u32:4>(x);
    count as u4 == std::popcount(x)
}

#[quickcheck(exhaustive)]
fn prop_u4_valid_matches_table(x: u4) -> bool {
    let (valid, _) = thermometer_to_binary<u32:4>(x);
    let expected_valid = x == u4:0b0000 ||
        x == u4:0b0001 ||
        x == u4:0b0011 ||
        x == u4:0b0111 ||
        x == u4:0b1111;
    valid == expected_valid
}

#[quickcheck(exhaustive)]
fn prop_u4_valid_implies_contiguous_shape(x: u4) -> bool {
    let (valid, count) = thermometer_to_binary<u32:4>(x);
    let expected_shape = match count {
        u3:0 => u4:0b0000,
        u3:1 => u4:0b0001,
        u3:2 => u4:0b0011,
        u3:3 => u4:0b0111,
        _ => u4:0b1111,
    };
    if valid { x == expected_shape } else { true }
}
```
