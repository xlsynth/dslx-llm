# Shift-Add Multiplier

## Prompt

Implement a truly staged unsigned shift-add multiplier API with explicit state.

You must define `MulState<N: u32>` yourself and implement:

- `mul_init`
- `mul_step`
- `get_product`

Usage model:

- Inputs are provided once via `mul_init`.
- Each call to `mul_step` processes exactly one multiplier bit.
- After exactly `N` calls to `mul_step`, `get_product` returns the full
  `2*N`-bit unsigned product.
- It is acceptable for `mul_step` calls after completion to leave the state
  unchanged.

The prologue will be automatically included, so implement only what is
requested in the signature.

## Requirements

The following requirements will be checked by a separate critic model. The
critic should treat comments as claims, not proof, and decide from actual DSLX
structure.

- id: one_multiplier_bit_per_step
  requirement: `mul_step` must process one multiplier bit per call, not all bits at once.

- id: explicit_progress_state
  requirement: The implementation must carry explicit progress state, such as a step counter, shifted multiplier, shifted multiplicand, or equivalent state that evolves across calls.

- id: no_full_width_multiply
  requirement: The implementation must not compute the final product with a direct multiply expression, `std::umul`, or any equivalent full-width multiply shortcut.

## Prologue

```dslx
```

## Signature

```dslx-snippet
fn mul_init<N: u32>(x: uN[N], y: uN[N]) -> MulState<N>
fn mul_step<N: u32>(st: MulState<N>) -> MulState<N>
fn get_product<N: u32>(st: MulState<N>) -> uN[N + N]
```

## Tests

```dslx-snippet
fn run_mul<N: u32>(x: uN[N], y: uN[N]) -> MulState<N> {
    let st0 = mul_init<N>(x, y);
    for (_, st): (u32, MulState<N>) in u32:0..N {
        mul_step<N>(st)
    }(st0)
}

#[test]
fn test_shift_add_multiplier_u8_examples() {
    assert_eq(get_product<u32:8>(run_mul<u32:8>(u8:13, u8:11)), u16:143);
    assert_eq(get_product<u32:8>(run_mul<u32:8>(u8:255, u8:2)), u16:510);
    assert_eq(get_product<u32:8>(run_mul<u32:8>(u8:0, u8:200)), u16:0);
}

#[test]
fn test_shift_add_multiplier_u16_examples() {
    assert_eq(get_product<u32:16>(run_mul<u32:16>(u16:0x1234, u16:0x0003)), u32:0x0000369c);
    assert_eq(get_product<u32:16>(run_mul<u32:16>(u16:0xffff, u16:0xffff)), u32:0xfffe0001);
}

#[quickcheck(exhaustive)]
fn quickcheck_compare_u4(x: u4, y: u4) -> bool {
    get_product<u32:4>(run_mul<u32:4>(x, y)) == std::umul(x, y)
}

#[quickcheck]
fn quickcheck_compare_u8(x: u8, y: u8) -> bool {
    get_product<u32:8>(run_mul<u32:8>(x, y)) == std::umul(x, y)
}
```
