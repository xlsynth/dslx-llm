# Reverse Chunks

## Prompt

It can be useful to group a sequence of bits into "chunks" of `N` bits, and
then reverse those chunks. e.g. when `N=4` we're doing nibble reversal, when
`N=8` we're doing byte reversal.

Implement a function that reverses chunks of `N` bits from an originally flat
sequence of bits size `FLAT`, and emits those reversed chunks in flattened
form.

Please check the invariant that the `FLAT` count is a multiple of the chunk
size `N`.

## Signature

```dslx-snippet
fn reverse_chunks<N: u32, FLAT: u32>(x: bits[FLAT]) -> bits[FLAT]
```

## Tests

```dslx
#[test]
fn test_one_nibble() {
    let x = u4:0b1111;
    assert_eq(reverse_chunks<u32:4>(x), x);
}

#[test]
fn test_two_nibbles() {
    let x = u8:0b1001_0110;
    assert_eq(reverse_chunks<u32:4>(x), u8:0b0110_1001);
}

fn golden_reference<N: u32, FLAT: u32>(x: bits[FLAT]) -> bits[FLAT] {
    const_assert!(FLAT % N == u32:0);
    const ITEMS = FLAT / N;
    let a = x as uN[N][ITEMS];
    let r = array_rev(a);
    r as bits[FLAT]
}

#[quickcheck]
fn quickcheck_reverse_chunks_twice_u8(x: bits[24]) -> bool {
    const N = u32:8;
    reverse_chunks<N>(reverse_chunks<N>(x)) == x
}

#[quickcheck]
fn quickcheck_reverse_chunks_u8(x: bits[24]) -> bool {
    const N = u32:8;
    golden_reference<N>(x) == reverse_chunks<N>(x)
}

#[quickcheck]
fn quickcheck_reverse_chunks_u4(x: bits[20]) -> bool {
    const N = u32:4;
    golden_reference<N>(x) == reverse_chunks<N>(x)
}

#[quickcheck]
fn quickcheck_reverse_chunks_u2(x: bits[14]) -> bool {
    const N = u32:2;
    golden_reference<N>(x) == reverse_chunks<N>(x)
}
```
