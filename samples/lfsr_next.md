# LFSR Next State Generator

## Prompt

Implement an 8-bit linear feedback shift register (LFSR) that produces the next pseudo-random number from a given state using a Fibonacci LFSR mechanism. The LFSR uses taps at bit positions 7, 5, 4, and 3 (with bit 7 being the most significant bit). For a nonzero input, these tapped bits are XOR'd together to form a feedback bit. The new state is computed by shifting the input left by one (keeping only the lower 8 bits) and inserting the feedback bit at the least-significant position. If the input is zero, the function returns zero, as this is the degenerate state of the LFSR. This design is often used in hardware to produce pseudo-random sequences for testing or simulation.

## Signature

```dslx-snippet
fn lfsr_next(x: u8) -> u8
```

## Tests

```dslx-snippet
#[test]
fn test_lfsr_fixed() {
    // Fixed test cases for known seeds
    // 0 should map to 0
    assert_eq(lfsr_next(u8:0), u8:0);
    // For seed 0x01 (0000_0001): tapped bits are all 0, so feedback = 0, result = 0x02
    assert_eq(lfsr_next(u8:0x01), u8:0x02);
    // For seed 0x10 (0001_0000): bit4 is 1, others are 0, feedback = 1, result = (0x10 << 1 = 0x20) | 1 = 0x21
    assert_eq(lfsr_next(u8:0x10), u8:0x21);
    // For seed 0x80 (1000_0000): bit7 is 1, feedback = 1, result = ((0x80 << 1) & 0xff = 0x00) | 1 = 0x01
    assert_eq(lfsr_next(u8:0x80), u8:0x01);
    // For seed 0xFF (1111_1111): tapped bits (bit7, bit5, bit4, bit3) are all 1,
    // so feedback = 1^1^1^1 = 0, result = (0xFF << 1 = 0xFE) & 0xff
    assert_eq(lfsr_next(u8:0xFF), u8:0xFE);
}

#[quickcheck(exhaustive)]
fn prop_nonzero_preservation(x: u8) -> bool {
    // For any nonzero seed, the next state should also be nonzero.
    if x == u8:0 {
        lfsr_next(x) == u8:0
    } else {
        lfsr_next(x) != u8:0
    }
}

#[quickcheck(exhaustive)]
fn prop_no_fixed_point(x: u8) -> bool {
    // For any nonzero seed, the LFSR should not produce the same state (i.e. no fixed point).
    if x == u8:0 {
        lfsr_next(x) == u8:0
    } else {
        lfsr_next(x) != x
    }
}
```
