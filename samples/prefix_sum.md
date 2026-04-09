# Prefix Sum

## Prompt

Write a DSLX function that calculates the prefix sum of an array.

## Requirements

The following requirements will be checked by a separate critic model. The critic should treat
comments as claims, not proof, and decide from the actual DSLX structure.

- id: running_sum_loop_state
  requirement: The implementation must use loop-carried state that evolves the running prefix sum from one element to the next, rather than recomputing each prefix independently from scratch.

- id: output_array_built_incrementally
  requirement: The output array must be built incrementally as the loop progresses, for example via tuple accumulator state plus `update(...)` on an array accumulator, or an equivalent staged construction.

- id: not_quadratic_rescan_strategy
  requirement: The implementation must not use a nested "for each output position, rescan the prefix" strategy or another obviously quadratic recomputation approach when a linear prefix accumulation is possible.

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
