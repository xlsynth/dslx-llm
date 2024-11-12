# Distinct Predicate

## Prompt

Write a DSLX predicate function that takes an array of items and a valid mask
and outputs whether all valid items are all distinct.

## Signature

```dslx-snippet
fn distinct<COUNT: u32, N: u32, S: bool>(items: xN[S][N][COUNT], valid: bool[COUNT]) -> bool
```

## Tests

```dslx
#[test]
fn test_simple_nondistinct() {
    assert_eq(distinct(u2[2]:[1, 1], bool[2]:[true, true]), false)
}

#[test]
fn test_distinct_unsigned() {
    let items = u8[4]:[1, 2, 3, 2];
    let valid = bool[4]:[true, true, true, true];
    assert_eq(distinct<4, 8, false>(items, valid), false);
}

#[test]
fn test_distinct_signed() {
    let items = s8[3]:[-1, 0, 1];
    let valid = bool[3]:[true, true, true];
    assert_eq(distinct<3, 8, true>(items as bits[8][3], valid), true);
}

#[test]
fn test_distinct_with_invalid() {
    let items = u8[4]:[1, 2, 3, 1];
    let valid = bool[4]:[true, true, true, false];
    assert_eq(distinct<4, 8, false>(items, valid), true);
}

#[quickcheck]
fn quickcheck_forced_duplicate(xs: u4[4], to_dupe: u2) -> bool {
    const ALL_VALID = bool[4]:[true, ...];
    let forced_dupe = update(xs, (to_dupe as u32+u32:1) % u32:4, xs[to_dupe]);
    distinct(forced_dupe, ALL_VALID) == false
}

#[quickcheck]
fn quickcheck_distinct_all_valid_items_same(value: u4, valid: bool[4]) -> bool {
    let items = u4[4]:[value, ...];  // All items are the same.
    let num_valid = std::popcount(valid as u4) as u32;

    if num_valid <= u32:1 {
        // With 0 or 1 valid items, they are trivially distinct.
        distinct(items, valid) == true
    } else {
        // Since all valid items are the same, 'distinct' should return false.
        distinct(items, valid) == false
    }
}
```
