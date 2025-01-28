# Sliding Window Min/Max

## Prompt

Compute the minimum or maximum value for every sliding window of size K in an input array.

## Signature

```dslx-snippet
fn sliding_window_minmax<S: bool, N: u32, M: u32, K: u32, O: u32 = {M - K + u32:1}>(array: xN[S][N][M], find_max: bool) -> xN[S][N][O]
```

## Tests

```dslx-snippet
#[test]
fn test_sliding_window_max() {
    let array = bits[4][5]:[3, 1, 4, 2, 5];
    let k = u32:3;
    let result = sliding_window_minmax(array, true);

    // Expected result: max([3, 1, 4]) -> 4, max([1, 4, 2]) -> 4, max([4, 2, 5]) -> 5
    assert_eq(result, bits[4][3]:[4, 4, 5]);
}

#[test]
fn test_sliding_window_min() {
    let array = bits[4][5]:[3, 1, 4, 2, 5];
    let k = u32:3;
    let result = sliding_window_minmax(array, false);

    // Expected result: min([3, 1, 4]) -> 1, min([1, 4, 2]) -> 1, min([4, 2, 5]) -> 2
    assert_eq(result, bits[4][3]:[1, 1, 2]);
}

#[test]
fn test_single_element_array() {
    let array = bits[4][1]:[7];
    let k = u32:1;
    let result_max = sliding_window_minmax(array, true);
    let result_min = sliding_window_minmax(array, false);

    // Both max and min should return the single element.
    assert_eq(result_max, bits[4][1]:[7]);
    assert_eq(result_min, bits[4][1]:[7]);
}

#[test]
fn test_window_equals_array_length() {
    let array = bits[4][4]:[3, 1, 4, 2];
    let k = u32:4;
    let result_max = sliding_window_minmax(array, true);
    let result_min = sliding_window_minmax(array, false);

    // Max of the whole array is 4; min is 1.
    assert_eq(result_max, bits[4][1]:[4]);
    assert_eq(result_min, bits[4][1]:[1]);
}

fn array_max<N: u32, M: u32>(array: bits[N][M]) -> bits[N] {
    let initial = array[0];
    let max_value = for (element, accum) in array {
        if element > accum {
            element
        } else {
            accum
        }
    }(initial);
    max_value
}

fn array_min<N: u32, M: u32>(array: bits[N][M]) -> bits[N] {
    let initial = array[0];
    let min_value = for (element, accum) in array {
        if element < accum {
            element
        } else {
            accum
        }
    }(initial);
    min_value
}

#[quickcheck]
fn prop_window_property(array: bits[4][6], find_max: bool) -> bool {
    let result = sliding_window_minmax<false, 4, 6, 3>(array, find_max);

    // Verify each output is the min/max of its respective window
    for (i, acc) in range(u32:0, 6 - 3 + 1) {
        let window = array[i:i + 3];  // Extract the 3-element window
        let expected = if find_max {
            array_max(window)
        } else {
            array_min(window)
        };
        acc && result[i] == expected
    }(true)
}

#[quickcheck]
fn prop_monotonicity_property(find_max: bool) -> bool {
    let array = if find_max {
        bits[4][6]:[1, 2, 3, 4, 5, 6]  // Increasing input
    } else {
        bits[4][6]:[6, 5, 4, 3, 2, 1]  // Decreasing input
    };
    let result = sliding_window_minmax(array, find_max);

    for (i, acc) in range(u32:0, 6 - 3 + 1) {
        acc && result[i] == array[i + 2]  // Last element of the window
    }(true)
}

#[quickcheck]
fn prop_permutation_property(array: bits[4][6], find_max: bool) -> bool {
    let result = sliding_window_minmax(array, find_max);

    for (i, acc) in range(u32:0, 6 - 3 + 1) {
        let window = array[i:i + 3];  // Extract the 3-element window
        let valid_value = result[i] == array_max(window) || result[i] == array_min(window);
        acc && valid_value
    }(true)
}

#[quickcheck]
fn prop_single_element_window(array: bits[4][6], find_max: bool) -> bool {
    let result = sliding_window_minmax(array, find_max);
    result == array  // Output must match input
}
```
