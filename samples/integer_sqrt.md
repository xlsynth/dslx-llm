# Integer Square Root Calculator

## Prompt

Write a DSLX function that computes the integer square root of a given non-negative integer. Use the **non-restoring algorithm**. The function should be parameterizable for different bit widths. The function should return the floor of the square root of the input value.

## Signature

```dslx-snippet
fn integer_sqrt<N: u32, O: u32 = {(N + u32:1) / u32:2}>(value: uN[N]) -> uN[O]
```

## Tests

```dslx-snippet
#[test]
fn test_integer_sqrt_simple() {
    assert_eq(integer_sqrt(u4:0), u2:0);
    assert_eq(integer_sqrt(u4:1), u2:1);
    assert_eq(integer_sqrt(u4:4), u2:2);
    assert_eq(integer_sqrt(u4:9), u2:3);
    assert_eq(integer_sqrt(u4:15), u2:3);
}

#[test]
fn test_integer_sqrt_edge_cases() {
    assert_eq(integer_sqrt(u1:0b0), u1:0b0);
    assert_eq(integer_sqrt(u1:0b1), u1:0b1);
}

#[test]
fn test_integer_sqrt_large_numbers() {
    assert_eq(integer_sqrt(u8:255), u4:15);
    assert_eq(integer_sqrt(u16:1024), u8:32);
    assert_eq(integer_sqrt(u16:10000), u8:100);
    assert_eq(integer_sqrt(u16:65535), u8:255);
}

#[quickcheck]
fn prop_integer_sqrt_monotonic(a: u16, b: u16) -> bool {
    let sqrt_a = integer_sqrt(a);
    let sqrt_b = integer_sqrt(b);
    if a <= b {
        sqrt_a <= sqrt_b
    } else {
        sqrt_a >= sqrt_b
    }
}
```
