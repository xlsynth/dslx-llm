# Integer Square Root Calculator

## Prompt

Write a DSLX function that computes the integer square root of a given non-negative integer. Use the **non-restoring algorithm**. The function should be parameterizable for different bit widths. The function should return the floor of the square root of the input value.

## Requirements

The following requirements will be checked by a separate critic model. The critic should treat
comments as claims, not proof, and decide from the actual DSLX structure.

- id: bounded_iterative_algorithm
  requirement: The implementation must use a bounded iterative formulation, such as a counted DSLX `for` loop over root-digit or bit-pair steps, rather than a `while` loop, brute-force search over candidates, or a direct closed-form expression.

- id: non_restoring_state_update
  requirement: The implementation must maintain explicit step-to-step algorithm state consistent with a non-restoring square-root method, such as partial remainder and partial root (or equivalent state variables), and update that state each iteration.

- id: not_builtin_or_linear_search
  requirement: The implementation must not call a built-in square-root helper, convert through floating-point to compute the answer, or linearly search candidate roots by checking `r * r <= value`.

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
