# Bitonic Sort

## Prompt

Implement a full bitonic sort function, which takes an array and returns a fully sorted array in ascending order. Use the standard bitonic sort algorithm (i.e., building bitonic sequences and performing bitonic merges).

## Signature

```dslx-snippet
fn bitonic_sort<S: bool, N: u32, M: u32>(array: xN[S][N][M]) -> xN[S][N][M]
```

## Tests

```dslx-snippet
fn sum_reduce<S: bool, N: u32, ITEMS: u32>(a: xN[S][N][ITEMS]) -> xN[S][N] {
    for (item, accum) in a {
        accum + item
    }(xN[S][N]:0)
}

#[quickcheck(exhaustive)]
fn prop_bitonic_sort(array: s3[4]) -> bool {
    let sorted = bitonic_sort(array);

    // 1) Check sorted
    let is_sorted = for (i, acc) in range(u32:0, u32:4 - u32:1) {
        acc && (sorted[i] <= sorted[i + 1])
    }(true);

    // 2) Check permutation
    let in_sum = sum_reduce(array);
    let out_sum = sum_reduce(sorted);
    let is_permutation = in_sum == out_sum;

    // 3) Check idempotence
    let double_sorted = bitonic_sort(sorted);
    let is_idempotent = (sorted == double_sorted);

    // Combined property
    is_sorted && is_permutation && is_idempotent
}
```
