# Array Slice

## Prompt

Write a DSLX function that returns a slice of an array given a constexpr start and width -- if `start+width` is greater than the length of the array, the funciton should zero-fill the remaining elements.

## Signature

```dslx-snippet
fn array_slice<START: u32, WIDTH: u32, S: bool, BITS: u32, COUNT: u32>(items: xN[S][BITS][COUNT]) -> xN[S][BITS][WIDTH]
```

## Tests

```dslx-snippet
#[test]
fn test_array_slice_simple() {
    assert_eq(array_slice<u32:1, u32:3>(u3[5]:[1, 2, 3, 4, 5]), u3[3]:[2, 3, 4]);
}

#[test]
fn test_array_slice_width_1() {
    assert_eq(array_slice<u32:0, u32:1>(u3[5]:[1, 2, 3, 4, 5]), u3[1]:[1]);
    assert_eq(array_slice<u32:1, u32:1>(u3[5]:[1, 2, 3, 4, 5]), u3[1]:[2]);
    assert_eq(array_slice<u32:2, u32:1>(u3[5]:[1, 2, 3, 4, 5]), u3[1]:[3]);
    assert_eq(array_slice<u32:3, u32:1>(u3[5]:[1, 2, 3, 4, 5]), u3[1]:[4]);
    assert_eq(array_slice<u32:4, u32:1>(u3[5]:[1, 2, 3, 4, 5]), u3[1]:[5]);
    assert_eq(array_slice<u32:5, u32:1>(u3[5]:[1, 2, 3, 4, 5]), u3[1]:[0]);
}

#[test]
fn test_array_slice_width_2() {
    assert_eq(array_slice<u32:0, u32:2>(u3[5]:[1, 2, 3, 4, 5]), u3[2]:[1, 2]);
    assert_eq(array_slice<u32:1, u32:2>(u3[5]:[1, 2, 3, 4, 5]), u3[2]:[2, 3]);
    assert_eq(array_slice<u32:2, u32:2>(u3[5]:[1, 2, 3, 4, 5]), u3[2]:[3, 4]);
    assert_eq(array_slice<u32:3, u32:2>(u3[5]:[1, 2, 3, 4, 5]), u3[2]:[4, 5]);
    assert_eq(array_slice<u32:4, u32:2>(u3[5]:[1, 2, 3, 4, 5]), u3[2]:[5, 0]);
    assert_eq(array_slice<u32:5, u32:2>(u3[5]:[1, 2, 3, 4, 5]), u3[2]:[0, 0]);
}

#[test]
fn test_array_slice_width_0() {
    assert_eq(array_slice<u32:0, u32:0>(u3[5]:[1, 2, 3, 4, 5]), u3[0]:[]);
    assert_eq(array_slice<u32:1, u32:0>(u3[5]:[1, 2, 3, 4, 5]), u3[0]:[]);
    assert_eq(array_slice<u32:2, u32:0>(u3[5]:[1, 2, 3, 4, 5]), u3[0]:[]);
    assert_eq(array_slice<u32:3, u32:0>(u3[5]:[1, 2, 3, 4, 5]), u3[0]:[]);
    assert_eq(array_slice<u32:4, u32:0>(u3[5]:[1, 2, 3, 4, 5]), u3[0]:[]);
    assert_eq(array_slice<u32:5, u32:0>(u3[5]:[1, 2, 3, 4, 5]), u3[0]:[]);
}
```
