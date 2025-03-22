# Count Leading Zeros

## Prompt

Implement a function that computes the number of leading zeros in an N-bit unsigned integer.

Count the number of consecutive `0`-bits starting from the most-significant bit, until the first
`1`-bit is encountered. If the input is `0`, the function should return `N`.

## Signature

```dslx-snippet
fn count_leading_zeros<N: u32>(x: uN[N]) -> uN[N]
```

## Tests

```dslx-snippet
fn naive_reference<N: u32>(x: uN[N]) -> uN[N] {
    let (count, _) = for (i, (acc, done)) in u32:0..N {
        let bit_index = N - u32:1 - i;
        // If we have already seen a 1, carry forward the current accumulator.
        if done {
            (acc, done)
        } else {
            if (((x >> bit_index) as u1)) {
                // Found the first 1; mark "done" so that subsequent iterations leave `acc` unchanged.
                (acc, true)
            } else {
                // Bit is 0, so increment the count.
                (acc + uN[N]:1, false)
            }
        }
    } ((uN[N]:0, false));
    count
}

#[test]
fn test_count_leading_zeros_all_zeros() {
  // If the value is 0, all 32 bits are zero.
  assert_eq(count_leading_zeros(u32:0), u32:32);
}

#[test]
fn test_count_leading_zeros_no_leading_zeros() {
  // If the most-significant bit is 1, there are no leading zeros.
  assert_eq(count_leading_zeros(u32:0x80000000), u32:0);
}

#[test]
fn test_count_leading_zeros_example() {
  // For a typical value, e.g. 0x00F00000 has 8 leading zeros.
  assert_eq(count_leading_zeros(u32:0x00F00000), u32:8);
}

#[quickcheck]
fn prop_equals_naive_u16(x: u16) -> bool {
    naive_reference(x) == count_leading_zeros(x)
}

#[quickcheck]
fn prop_equals_naive_u32(x: u32) -> bool {
    naive_reference(x) == count_leading_zeros(x)
}
```
