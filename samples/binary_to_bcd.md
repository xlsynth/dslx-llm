# Binary to BCD Converter

## Prompt

Implement an 8-bit binary to BCD converter.

The prologue will be automatically included, just implement the signature in the output answer.

## Prologue

```dslx
type BcdDigit = u4;
```

## Signature

```dslx-snippet
fn binary_to_bcd(x: u8) -> BcdDigit[3]
```

## Tests

```dslx-snippet
/// Helper for inverting the conversion so we can check round trip results.
fn bcd_to_binary(y: BcdDigit[3]) -> u8 {
    y[0] as u8 * u8:100 + y[1] as u8 * u8:10 + y[2] as u8
}

#[test]
fn test_binary_to_bcd() {
    // 0 in decimal should be 000
    assert_eq(binary_to_bcd(u8:0), u4[3]:[u4:0, u4:0, u4:0]);
    // 123 in decimal should be represented as 1, 2, 3
    assert_eq(binary_to_bcd(u8:123), u4[3]:[u4:1, u4:2, u4:3]);
    // 255 in decimal should be represented as 2, 5, 5
    assert_eq(binary_to_bcd(u8:255), u4[3]:[u4:2, u4:5, u4:5]);
}

#[quickcheck(exhaustive)]
fn prop_binary_to_bcd_value(x: u8) -> bool {
    bcd_to_binary(binary_to_bcd(x)) == x
}
```
