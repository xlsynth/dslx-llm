# Repeat Multi-bit Value

## Prompt

Implement a function that repeats a multi-bit value a given number of times.

## Signature

```dslx-snippet
fn repeat<TIMES: u32, VALUE_BITS: u32, OUT_BITS: u32 = {TIMES * VALUE_BITS}>(x: uN[VALUE_BITS]) -> uN[OUT_BITS]
```

## Tests

```dslx-snippet
#[test]
fn test_repeat_1b_1_1x() {
    let x = u1:1;
    let y = repeat<u32:1>(x);
    assert_eq(y, u1:1);
}

#[test]
fn test_repeat_1b_0b0_1x() {
    let x = u1:0;
    let y = repeat<u32:1>(x);
    assert_eq(y, u1:0);
}

#[test]
fn test_repeat_1b_2x() {
    let x = u1:1;
    let y = repeat<u32:2>(x);
    assert_eq(y, u2:0b11);
}

#[test]
fn test_repeat_2b_0b10_2x() {
    let x = u2:0b10;
    let y = repeat<u32:2>(x);
    assert_eq(y, u4:0b10_10);
}

#[test]
fn test_repeat_2b_0b01_2x() {
    let x = u2:0b01;
    let y = repeat<u32:2>(x);
    assert_eq(y, u4:0b01_01);
}

#[test]
fn test_repeat_16b_2x() {
    let x = u16:0xabab;
    let y = repeat<u32:2>(x);
    assert_eq(y, u32:0xabab_abab);
}

#[test]
fn test_repeat_16b_3x() {
    let x = u16:0xcdcd;
    let y = repeat<u32:3>(x);
    assert_eq(y, u48:0xcdcd_cdcd_cdcd);
}

#[quickcheck(exhaustive)]
fn quickcheck_repeat_2b_3x(x: u2) -> bool {
    let y = repeat<u32:3>(x);
    y as u2[3] == u2[3]:[x, ...]
}
```
