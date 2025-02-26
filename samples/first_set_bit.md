# Find First Set Bit

## Prompt

Write a routine that finds the first set bit in a bit vector -- it supports giving a relative
bit index from either the most significant bit side -- in which case the most significant bit is
numbered 0 -- or from the last significant bit side -- in which case the least significant bit
is numbered 0.

The return value indicates `(any_bit_set, which_bit_set)` -- when no bit is set the second value
can be arbitrarily chosen, i.e. it should not be looked at by the caller by contract.

The prologue will be automatically included, just implement the signature in the output answer.

## Prologue

```dslx
enum Direction : u1 {
    MSB_IS_0 = 0,
    LSB_IS_0 = 1,
}
```

## Signature

```dslx-snippet
fn find_first_set_bit<N: u32, N_LOG2: u32 = {std::clog2(N + u32:1)}>(x: uN[N], direction: Direction) -> (bool, uN[N_LOG2])
```

## Tests

```dslx-snippet
#[test]
fn test_simple_lsb_set() {
    let x = u8:1;
    assert_eq(find_first_set_bit(x, Direction::LSB_IS_0), (true, u4:0));
    assert_eq(find_first_set_bit(x, Direction::MSB_IS_0), (true, u4:7));
}

#[test]
fn test_simple_msb_set() {
    let x = u8:0x80;
    assert_eq(find_first_set_bit(x, Direction::LSB_IS_0), (true, u4:7));
    assert_eq(find_first_set_bit(x, Direction::MSB_IS_0), (true, u4:0));
}

#[quickcheck(exhaustive)]
fn quickcheck_set_one_index_lsb(i: u3) -> bool {
    let x = bit_slice_update(u8:0, i, true);
    find_first_set_bit(x, Direction::LSB_IS_0) == (true, i as u4)
}

#[quickcheck(exhaustive)]
fn quickcheck_set_one_index_msb(i: u3) -> bool {
    let x = bit_slice_update(u8:0, u32:8 - i as u32 - u32:1, true);
    find_first_set_bit(x, Direction::MSB_IS_0) == (true, i as u4)
}
```
