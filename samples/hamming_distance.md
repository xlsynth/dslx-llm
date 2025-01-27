# Hamming Distance

## Prompt

Write a DSLX function that calculates the Hamming distance between two binary numbers of the same bit width. The Hamming distance is defined as the number of positions at which the corresponding bits are different.

## Signature

```dslx-snippet
fn hamming_distance<N: u32>(a: uN[N], b: uN[N]) -> uN[N]
```

## Tests

```dslx-snippet
#[test]
fn test_hamming_distance_simple() {
    assert_eq(hamming_distance(u3:0b000, u3:0b000), u3:0);
    assert_eq(hamming_distance(u3:0b000, u3:0b111), u3:3);
    assert_eq(hamming_distance(u3:0b101, u3:0b010), u3:3);
    assert_eq(hamming_distance(u3:0b110, u3:0b011), u3:2);
    assert_eq(hamming_distance(u3:0b111, u3:0b111), u3:0);
}

#[test]
fn test_hamming_distance_large() {
    assert_eq(hamming_distance(u8:0b00000000, u8:0b11111111), u8:8);
    assert_eq(hamming_distance(u8:0b10101010, u8:0b01010101), u8:8);
    assert_eq(hamming_distance(u8:0b11110000, u8:0b00001111), u8:8);
    assert_eq(hamming_distance(u8:0b11111111, u8:0b11111111), u8:0);
}

#[test]
fn test_hamming_distance_edge_cases() {
    assert_eq(hamming_distance(u1:0b0, u1:0b1), u1:1);
    assert_eq(hamming_distance(u1:0b1, u1:0b1), u1:0);
    assert_eq(hamming_distance(u16:0xFFFF, u16:0x0000), u16:16);
    assert_eq(hamming_distance(u16:0xAAAA, u16:0x5555), u16:16);
}

#[quickcheck]
fn quickcheck_hamming_distance_symmetry(a: u8, b: u8) -> bool {
    hamming_distance(a, b) == hamming_distance(b, a)
}

#[quickcheck]
fn quickcheck_hamming_distance_self(a: u8) -> bool {
    hamming_distance(a, a) == u8:0
}

#[quickcheck]
fn quickcheck_hamming_distance_max(a: u8, b: u8) -> bool {
    hamming_distance(a, b) <= u8:8
}
```
