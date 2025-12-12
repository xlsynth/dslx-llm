# Prefix Sum

## Prompt

Write a DSLX function that calculates the prefix sum of an array.

## Signature

```dslx-snippet
fn prefix_sum<S: bool, N: u32, COUNT: u32>(items: xN[S][N][COUNT]) -> xN[S][N][COUNT]
```

## Tests

```dslx-snippet
#[test]
fn test_prefix_sum_simple() {
    assert_eq(prefix_sum(u3[3]:[1, 2, 3]), u3[3]:[1, 3, 6]);
}

#[test]
fn test_prefix_sum_signed() {
    assert_eq(prefix_sum(s4[3]:[-1, -2, -3]), s4[3]:[-1, -3, -6]);
}

#[quickcheck]
fn prop_prefix_sum_commutative(xs: u3[4]) -> bool {
    let prefix_sum_xs = prefix_sum(xs);
    let prefix_sum_reverse_xs = prefix_sum(array_rev(xs));
    // the last element is the cumulative sum and so should always be the same
    prefix_sum_xs[3] == prefix_sum_reverse_xs[3]
}

#[quickcheck]
fn prop_prefix_sum_padded(xs: u3[4]) -> bool {
    // If we take the original array and pad it with a leading zero, all the elements except for the first should be the same.
    let padded_xs = u3[5]:[u3:0, xs[0], xs[1], xs[2], xs[3]];
    let prefix_sum_padded_xs = prefix_sum(padded_xs);
    let prefix_sum_xs = prefix_sum(xs);
    array_slice(prefix_sum_padded_xs, u32:1, zero!<u3[4]>()) == prefix_sum_xs
}
```
