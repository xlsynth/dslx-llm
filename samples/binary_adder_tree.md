# Binary Adder Tree

## Prompt

Implement a binary adder tree that either takes 8 `s16` values (the add-reduction of which produces an `s19` value) or two arrays of 8 `s4` values (which produces two `s7` values). Both inputs should feed the same underlying binary adder tree structure, **do not** create distinct trees.

## Signature

```dslx-snippet
fn binary_adder_tree(x: s8[8], y: (s4[8], s4[8]), use_s8s: bool) -> (s11, (s7, s7))
```

## Tests

```dslx-snippet
#[test]
fn test_s8s_m1s() {
    let x = s8[8]:[-1, ...];
    let y: (s4[8], s4[8]) = zero!<(s4[8], s4[8])>();
    let (got, _) = binary_adder_tree(x, y, true);
    assert_eq(got, s11:-8);
}

#[test]
fn test_s4s_1s_and_m1s() {
    let x = zero!<s8[8]>();
    let y = (s4[8]:[-1, ...], s4[8]:[1, ...]);
    let (_, (got_m1, got_1)) = binary_adder_tree(x, y, false);
    assert_eq(got_m1, s7:-8);
    assert_eq(got_1, s7:8);
}

#[test]
fn test_s4_max_and_min() {
    let x = zero!<s8[8]>();
    let y = (s4[8]:[s4::MAX, ...], s4[8]:[s4::MIN, ...]);
    let (_, (got_max, got_min)) = binary_adder_tree(x, y, false);
    assert_eq(got_max, s7:7 * s7:8);
    assert_eq(got_min, s7:-8 * s7:8);
}

#[quickcheck]
fn prop_same_s4s_in_both_elements(a: s4[8]) -> bool {
    let (_wide, (narrow_a, narrow_b)) = binary_adder_tree(zero!<s8[8]>(), (a, a), false);
    narrow_a == narrow_b
}
```
