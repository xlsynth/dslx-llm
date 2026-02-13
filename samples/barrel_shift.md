# Barrel Shifter

## Prompt

Implement a parameterized logical barrel shifter.

The function takes an input value, a shift amount, and a direction bit:

- if `right == false`, shift left logically;
- if `right == true`, shift right logically.

Bit positions shifted past the edge should be filled with zeros.
Overshift behavior is part of the contract: if `amt >= N`, the result must be all zeros.

The implementation should be structurally similar to a hardware barrel shifter:
compose a logarithmic number of power-of-two stages controlled by bits of `amt`.

## Requirements

The following requirements will be checked by a separate critic model. The critic should treat comments as claims, not proof, and decide from the actual DSLX structure.

- id: logarithmic_stage_structure
  requirement: The implementation must realize shifting via stage composition, where stage `k` conditionally shifts by `2^k` based on `amt[k]` (or an equivalent expression). Evidence should show multiple staged intermediates (or a loop over stage index) whose data dependencies correspond to power-of-two shifts.

- id: not_single_dynamic_shift_expression
  requirement: The implementation must not implement the whole operation as a single direct shift by `amt` (e.g. `value << amt` or `value >> amt`) in the main datapath. A direct shift may appear in tests or helper/reference code, but the `barrel_shift` implementation itself should be stage-based.

- id: direction_select_in_datapath
  requirement: Direction control must be part of the datapath behavior for each stage (or an equivalent unified formulation), such that both left and right shifting are supported by the same staged design.

## Signature

```dslx-snippet
fn barrel_shift<N: u32, AMT_SZ: u32>(value: bits[N], amt: bits[AMT_SZ], right: bool) -> bits[N]
```

## Tests

```dslx-snippet
fn barrel_shift_reference<N: u32, AMT_SZ: u32>(value: bits[N], amt: bits[AMT_SZ], right: bool) -> bits[N] {
    if (amt as u32) >= N {
        bits[N]:0
    } else if right {
        value >> amt
    } else {
        value << amt
    }
}

#[test]
fn test_barrel_shift_selected_u8() {
    // Left shifts.
    assert_eq(barrel_shift<u32:8, u32:3>(u8:0b0001_0011, u3:0, false), u8:0b0001_0011);
    assert_eq(barrel_shift<u32:8, u32:3>(u8:0b0001_0011, u3:1, false), u8:0b0010_0110);
    assert_eq(barrel_shift<u32:8, u32:3>(u8:0b0001_0011, u3:4, false), u8:0b0011_0000);
    assert_eq(barrel_shift<u32:8, u32:3>(u8:0b1111_0000, u3:7, false), u8:0b0000_0000);

    // Right shifts.
    assert_eq(barrel_shift<u32:8, u32:3>(u8:0b1001_0110, u3:0, true), u8:0b1001_0110);
    assert_eq(barrel_shift<u32:8, u32:3>(u8:0b1001_0110, u3:1, true), u8:0b0100_1011);
    assert_eq(barrel_shift<u32:8, u32:3>(u8:0b1001_0110, u3:4, true), u8:0b0000_1001);
    assert_eq(barrel_shift<u32:8, u32:3>(u8:0b0000_1111, u3:7, true), u8:0b0000_0000);
}

#[test]
fn test_barrel_shift_overshift_u5() {
    assert_eq(barrel_shift<u32:5, u32:3>(u5:0b10101, u3:5, false), u5:0);
    assert_eq(barrel_shift<u32:5, u32:3>(u5:0b10101, u3:6, false), u5:0);
    assert_eq(barrel_shift<u32:5, u32:3>(u5:0b10101, u3:7, false), u5:0);

    assert_eq(barrel_shift<u32:5, u32:3>(u5:0b10101, u3:5, true), u5:0);
    assert_eq(barrel_shift<u32:5, u32:3>(u5:0b10101, u3:6, true), u5:0);
    assert_eq(barrel_shift<u32:5, u32:3>(u5:0b10101, u3:7, true), u5:0);
}

#[quickcheck(exhaustive)]
fn quickcheck_compare_reference_u8(value: u8, amt: u3, right: bool) -> bool {
    let got = barrel_shift<u32:8, u32:3>(value, amt, right);
    let want = barrel_shift_reference<u32:8, u32:3>(value, amt, right);
    got == want
}

#[quickcheck(exhaustive)]
fn quickcheck_compare_reference_u5(value: u5, amt: u3, right: bool) -> bool {
    let got = barrel_shift<u32:5, u32:3>(value, amt, right);
    let want = barrel_shift_reference<u32:5, u32:3>(value, amt, right);
    got == want
}
```
