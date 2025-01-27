# Integer Comparator

## Prompt

Write an integer comparator that supports:

* sgt: signed greater-than
* sge: signed greater-than-or-equal-to
* sle: signed less-than-or-equal-to
* slt: signed less-than
* ugt: unsigned greater-than
* uge: unsigned greater-than-or-equal-to
* ule: unsigned less-than-or-equal-to
* ult: unsigned less-than
* eq: equal
* ne: not-equal

## Prologue

```dslx
enum Cmp: u4 {
    SGT = 0,
    SGE = 1,
    SLE = 2,
    SLT = 3,
    UGT = 4,
    UGE = 5,
    ULE = 6,
    ULT = 7,
    EQ = 8,
    NE = 9,
}
```

## Signature

```dslx-snippet
fn run_cmp<N: u32>(lhs: bits[N], rhs: bits[N], cmp: Cmp) -> bool
```

## Tests

```dslx-snippet
#[test]
fn test_run_cmp() {
    // Unsigned comparisons
    assert_eq(run_cmp(u8:0x10, u8:0x08, Cmp::UGT), true);
    assert_eq(run_cmp(u8:0x08, u8:0x10, Cmp::ULT), true);
    assert_eq(run_cmp(u8:0xff, u8:0xff, Cmp::UGE), true);
    assert_eq(run_cmp(u8:0x00, u8:0x01, Cmp::ULE), true);

    // Signed comparisons
    assert_eq(run_cmp(u8:0x80, u8:0x00, Cmp::SGT), false);
    assert_eq(run_cmp(u8:0x80, u8:0x00, Cmp::SLT), true);
    assert_eq(run_cmp(u8:0xff, u8:0x7f, Cmp::SLE), true);
    assert_eq(run_cmp(u8:0x7f, u8:0xff, Cmp::SGE), true);

    // Equality comparisons
    assert_eq(run_cmp(u8:0xff, u8:0xff, Cmp::EQ), true);
    assert_eq(run_cmp(u8:0xff, u8:0x00, Cmp::NE), true);
    assert_eq(run_cmp(u8:0xaa, u8:0xaa, Cmp::NE), false);
}
```
