# Masked Popcount

## Prompt

Given a bit vector and a mask, give the population count for only the bits whose mask is enabled.

## Signature

```dslx-snippet
fn masked_popcount<N: u32>(value: bits[N], mask: bits[N]) -> bits[N]
```

## Tests

```dslx-snippet
#[test]
fn test_masked_popcount() {
    let value = u6:0b101101;
    let mask = u6:0b110011;
    let result = masked_popcount(value, mask);
    assert_eq(result, u6:2);  // 2 bits are set in the masked positions.
}

#[quickcheck(exhaustive)]
fn prop_all_ones_mask_same_as_popcount(x: u4) -> bool {
    std::popcount(x) == masked_popcount(x, all_ones!<u4>())
}

#[quickcheck(exhaustive)]
fn prop_all_zeros_mask_always_zero(x: u4) -> bool {
    masked_popcount(x, zero!<u4>()) == u4:0
}

#[quickcheck(exhaustive)]
fn prop_additive_masking(x: u4, mask1: u4, mask2: u4) -> bool {
    // Ensure the masks are disjoint.
    let disjoint_masks = mask1 & mask2 == u4:0;

    // Compute sparse_popcount for each mask individually and combined.
    let combined_mask = mask1 | mask2;
    let count_combined = masked_popcount(x, combined_mask);
    let count_separate = masked_popcount(x, mask1) + masked_popcount(x, mask2);

    // Property: combined sparse_popcount equals the sum of separate counts.
    if disjoint_masks { count_combined == count_separate } else { true }
}
```
