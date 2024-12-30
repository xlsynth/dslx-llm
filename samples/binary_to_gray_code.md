# Binary to Gray Code

## Prompt

Write a DSLX function that converts an unsigned binary number to its Gray code representation and another function to reverse the conversion, converting Gray code back to binary.

## Signature

```dslx-snippet
fn binary_to_gray<N: u32>(binary: uN[N]) -> uN[N]
fn gray_to_binary<N: u32>(gray: uN[N]) -> uN[N]
```

## Tests

```dslx
#[test]
fn test_binary_to_gray_simple() {
    assert_eq(binary_to_gray(u3:0b000), u3:0b000);
    assert_eq(binary_to_gray(u3:0b001), u3:0b001);
    assert_eq(binary_to_gray(u3:0b010), u3:0b011);
    assert_eq(binary_to_gray(u3:0b011), u3:0b010);
    assert_eq(binary_to_gray(u3:0b100), u3:0b110);
    assert_eq(binary_to_gray(u3:0b101), u3:0b111);
    assert_eq(binary_to_gray(u3:0b110), u3:0b101);
    assert_eq(binary_to_gray(u3:0b111), u3:0b100);
}

#[test]
fn test_binary_to_gray_and_back() {
    assert_eq(gray_to_binary(binary_to_gray(u8:0x00)), u8:0x00);
    assert_eq(gray_to_binary(binary_to_gray(u8:0x01)), u8:0x01);
    assert_eq(gray_to_binary(binary_to_gray(u8:0xFF)), u8:0xFF);
    assert_eq(gray_to_binary(binary_to_gray(u8:0xAB)), u8:0xAB);
}

#[test]
fn test_gray_to_binary_simple() {
    assert_eq(gray_to_binary(u3:0b000), u3:0b000);
    assert_eq(gray_to_binary(u3:0b001), u3:0b001);
    assert_eq(gray_to_binary(u3:0b011), u3:0b010);
    assert_eq(gray_to_binary(u3:0b010), u3:0b011);
    assert_eq(gray_to_binary(u3:0b110), u3:0b100);
    assert_eq(gray_to_binary(u3:0b111), u3:0b101);
    assert_eq(gray_to_binary(u3:0b101), u3:0b110);
    assert_eq(gray_to_binary(u3:0b100), u3:0b111);
}

#[quickcheck]
fn quickcheck_binary_to_gray_is_reversible(binary: u8) -> bool {
    let gray = binary_to_gray(binary);
    let binary_reconstructed = gray_to_binary(gray);
    binary_reconstructed == binary
}

#[quickcheck]
fn quickcheck_gray_code_is_unique(a: u8, b: u8) -> bool {
    if a == b {
        true
    } else {
        binary_to_gray(a) != binary_to_gray(b)
    }
}

import std;

// 1) Round-trip binary → gray → binary
#[quickcheck]
fn qc_roundtrip_binary_gray(x: u8) -> bool {
    gray_to_binary(binary_to_gray(x)) == x
}

// 2) Round-trip gray → binary → gray
#[quickcheck]
fn qc_roundtrip_gray_binary(g: u8) -> bool {
    binary_to_gray(gray_to_binary(g)) == g
}

// 3) Consecutive integer values differ by exactly one bit in Gray code
#[quickcheck]
fn qc_gray_neighbors_differ_by_one_bit(x: u8) -> bool {
    if x == u8:255 {
        // skip boundary
        true
    } else {
        let x_next = x + u8:1;
        let g_x     = binary_to_gray(x);
        let g_xnext = binary_to_gray(x_next);
        std::popcount(g_x ^ g_xnext) == u8:1
    }
}

// 4) Highest bit in Gray code equals highest bit in the original binary
#[quickcheck]
fn qc_gray_highest_bit_matches_binary(x: u8) -> bool {
    let g = binary_to_gray(x);
    let msb_binary = (x >> 7) & u8:1;  // highest bit of x
    let msb_gray   = (g >> 7) & u8:1;  // highest bit of Gray code
    msb_binary == msb_gray
}
```
