# Dynamic Mask Generator

## Prompt

Implement a routine that makes a mask with a dynamic range of bits set.

## Signature

```dslx-snippet
fn dynamic_mask<N: u32, WIDTH: u32 = {std::clog2(N) + u32:1}>(start: uN[WIDTH], width: uN[WIDTH]) -> uN[N]
```

## Tests

```dslx-snippet
#[test]
fn test_dynamic_mask_one_bit() {
    assert_eq(u1:1, dynamic_mask<u32:1>(u1:0, u1:1));
    assert_eq(u1:0, dynamic_mask<u32:1>(u1:0, u1:0));
}

#[test]
fn test_dynamic_mask_two_bit() {
    assert_eq(u2:0b00, dynamic_mask<u32:2>(u2:0, u2:0));
    assert_eq(u2:0b01, dynamic_mask<u32:2>(u2:0, u2:1));
    assert_eq(u2:0b10, dynamic_mask<u32:2>(u2:1, u2:1));
    assert_eq(u2:0b11, dynamic_mask<u32:2>(u2:0, u2:2));
}

#[quickcheck]
fn quickcheck_width_popcount(width: u3) -> bool {
    if width <= u3:4 {
        let x = dynamic_mask<u32:4>(u3:0, width);
        std::popcount(x) == width as u4
    } else {
        true
    }
}
```
