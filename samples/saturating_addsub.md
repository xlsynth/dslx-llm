# Saturating Add/Sub

## Prompt

Write a function that performs saturating add/subtract of N-bit values and
returns a boolean indicating if saturation occurred.

The prologue will be automatically included, just implement the signature in the output answer.

## Prologue

```dslx
enum Mode : u1 {
    ADD = 0,
    SUB = 1,
}
```

## Signature

```dslx-snippet
fn sat_addsub<N: u32>(mode: Mode, x: uN[N], y: uN[N]) -> (bool, uN[N])
```

## Tests

```dslx-snippet
#[test]
fn test_sat_addsub_add_no_saturate() {
    // 10 + 5 = 15 fits in u8 with no saturation.
    let (did_sat, result) = sat_addsub<u32:8>(Mode::ADD, u8:10, u8:5);
    assert_eq(did_sat, false);
    assert_eq(result, u8:15);
}

#[test]
fn test_sat_addsub_add_saturates() {
    // 15 + 3 = 18 in decimal but max u4 = 15 (0xF).
    let (did_sat, result) = sat_addsub<u32:4>(Mode::ADD, u4:15, u4:3);
    assert_eq(did_sat, true);
    assert_eq(result, u4:15);  // saturated
}

#[test]
fn test_sat_addsub_sub_no_saturate() {
    // 10 - 3 = 7 fits in u8 with no saturation.
    let (did_sat, result) = sat_addsub<u32:8>(Mode::SUB, u8:10, u8:3);
    assert_eq(did_sat, false);
    assert_eq(result, u8:7);
}

#[test]
fn test_sat_addsub_sub_saturates() {
    // 2 - 5 = -3 is below 0, so saturate to 0 in u4.
    let (did_sat, result) = sat_addsub<u32:4>(Mode::SUB, u4:2, u4:5);
    assert_eq(did_sat, true);
    assert_eq(result, u4:0);  // saturated
}

// Quickcheck property: for ADD we never exceed the max; for SUB we never go below 0.
#[quickcheck]
fn prop_sat_addsub_does_not_go_out_of_range(mode: Mode, x: u8, y: u8) -> bool {
    let (did_sat, result) = sat_addsub(mode, x, y);
    match mode {
        Mode::ADD => {
            // The result must be <= 0xff for u8. (Which DSLX ensures by construction.)
            // We also can check that "did_sat" is correct if (x + y) > 255.
            let wide_sum = (x as u16) + (y as u16);
            let expect_saturate = wide_sum > u16:0xff;
            let expected_result = if expect_saturate {
                u8::MAX
            } else {
                (wide_sum as u8)
            };
            (result == expected_result) && (did_sat == expect_saturate)
        },
        _ => {
            // The result must be >= 0 for u8, i.e. saturate to 0 if underflow.
            let wide_sub = (x as s16) - (y as s16);
            let expect_saturate = wide_sub < s16:0;
            let expected_result = if expect_saturate {
                u8:0
            } else {
                (wide_sub as u8)
            };
            (result == expected_result) && (did_sat == expect_saturate)
        },
    }
}
```
