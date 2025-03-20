# Bit Interleaver

## Prompt

Interleaves the bits of two 16-bit numbers. In many digital designs, it is useful to combine two signals in an alternating fashion. The function defined here, `bit_interleave`, takes two inputs, `x` and `y`, both 16-bit wide, and returns a 32-bit number composed of bits from `x` and `y` interleaved. Specifically, the bits from `x` occupy the even bit positions of the output (starting at position 0), while the bits from `y` occupy the odd positions. This interleaving means that you can uniquely recover the original two inputs by separating the even and odd bits of the result.

Tests will verify the correct placement of each bit by deinterleaving the output and comparing it to the expected original inputs.

## Signature

```dslx-snippet
fn bit_interleave<N: u32, O: u32 = {N + N}>(x: uN[N], y: uN[N]) -> uN[O]
```

## Tests

```dslx-snippet
#[test]
fn test_two_bit() {
    let cases = [
        (u2:0b00, u2:0b00, u4:0b0000),
        (u2:0b00, u2:0b01, u4:0b0010),
    ];
    for ((x, y, want), ()) in cases {
        assert_eq(want, bit_interleave(x, y));
    }(())
}

#[quickcheck]
fn prop_interleave_bit_consistency(x: u16, y: u16) -> bool {
    // Property: The count of 1 bits in the interleaved result should equal
    // the sum of the 1 bits in x and y.
    let result = bit_interleave(x, y);
    std::popcount(result) == (std::popcount(x) as u32 + std::popcount(y) as u32)
}

#[quickcheck]
fn prop_interleave_decomposition(x: u16, y: u16) -> bool {
    // Property: Verify that for each bit position i,
    // the bit from x is at position 2*i and the bit from y is at position 2*i+1.
    let result = bit_interleave(x, y);
    for (i, ok) in u32:0..u32:16 {
        if (((result >> (u32:2 * i)) & u32:1) as u16) != ((x >> i) & u16:1) {
            false
        } else if (((result >> ((u32:2 * i) + u32:1)) & u32:1) as u16) != ((y >> i) & u16:1) {
            false
        } else {
            ok
        }
    }(true)
}
```
