# Floating-point adder

## Prompt

Write a function that takes a square root of floating-point number with SIG_WIDTH significand bits
and EXP_WIDTH exponent bits.

The following functions don't exist: `apfloat::sqrt`, `apfloat::div`.

The prologue will be automatically included, just implement the signature in the output answer.

## Prologue

```dslx
import apfloat;
```

## Signature
```dslx-snippet
fn fp_sqrt<SIG_WIDTH: u32 = {u32:23}, EXP_WIDTH: u32 = {u32:8}>(a: apfloat::APFloat<EXP_WIDTH, SIG_WIDTH>) -> apfloat::APFloat<EXP_WIDTH, SIG_WIDTH>
```

## Tests

```dslx-snippet
fn test_fp16_sqrt(a: u16, b: u16) {
    let b = apfloat::unflatten<u32:5, u32:10>(b);
    let sqrt = fp_sqrt<u32:10, u32:5>(apfloat::unflatten<u32:5, u32:10>(a));
    if sqrt != b {
        trace_fmt!("result:   {:0b}", sqrt);
        trace_fmt!("expected: {:0b}", b);
    } else {};
    assert_eq(sqrt, b);
}
```
