# Absolute Difference & Order

## Prompt

Implement a function that computes:

- The absolute difference between two numbers
- Whether the left hand side is >= the right hand side

The prologue will be automatically included, just implement the signature in the output answer.

## Prologue

```dslx
struct AbsDiffResult<N: u32> {
    value: uN[N],
    lhs_is_ge: bool,
}
```

## Signature

```dslx-snippet
fn abs_diff<N: u32>(lhs: uN[N], rhs: uN[N]) -> AbsDiffResult<N>
```

## Tests

```dslx-snippet
fn naive_reference<N: u32>(lhs: uN[N], rhs: uN[N]) -> AbsDiffResult<N> {
    let (value, lhs_is_ge) = if lhs >= rhs {
        (lhs - rhs, true)
    } else {
        (rhs - lhs, false)
    };
    AbsDiffResult { value, lhs_is_ge }
}

#[test]
fn test_abs_diff_examples() {
    assert_eq(abs_diff(u8:0, u8:0), AbsDiffResult { value: u8:0, lhs_is_ge: true });
    assert_eq(abs_diff(u8:1, u8:0), AbsDiffResult { value: u8:1, lhs_is_ge: true });
    assert_eq(abs_diff(u8:0, u8:1), AbsDiffResult { value: u8:1, lhs_is_ge: false });
    assert_eq(abs_diff(u8:3, u8:1), AbsDiffResult { value: u8:2, lhs_is_ge: true });
    assert_eq(abs_diff(u8:1, u8:3), AbsDiffResult { value: u8:2, lhs_is_ge: false });
    assert_eq(abs_diff(u8:255, u8:0), AbsDiffResult { value: u8:255, lhs_is_ge: true });
    assert_eq(abs_diff(u8:0, u8:255), AbsDiffResult { value: u8:255, lhs_is_ge: false });
}

#[quickcheck(exhaustive)]
fn prop_equals_naive_u16(lhs: u8, rhs: u8) -> bool {
    naive_reference(lhs, rhs) == abs_diff(lhs, rhs)
}
```
