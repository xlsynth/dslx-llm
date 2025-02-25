# Any 2D Routine

## Prompt

Implement an "any" routine that says whether any boolean is set in a 2D array.

## Signature

```dslx-snippet
fn any_2d<OUTER: u32, INNER: u32>(a: bool[INNER][OUTER]) -> bool
```

## Tests

```dslx-snippet
#[test]
fn test_simple_one_element() {
    assert_eq(true, any_2d(bool[1][1]:[
        [true]
    ]));
    assert_eq(false, any_2d(bool[1][1]:[
        [false]
    ]));
}

#[test]
fn test_simple_two_outer_arrays() {
    assert_eq(true, any_2d([
        [false],
        [true],
    ]));
    assert_eq(false, any_2d([
        [false],
        [false],
    ]));
}

#[quickcheck]
fn quickcheck_one_set(inner: u2, outer: u3) -> bool {
    const INNER = u32:4;
    const OUTER = u32:8;
    let a = zero!<bool[INNER][OUTER]>();
    let a = update(a, (outer, inner), true);
    any_2d(a)
}
```
