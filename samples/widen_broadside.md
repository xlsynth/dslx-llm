# Widen Broadside

## Prompt

Sometimes we get data in a "packed form" but we want to spread (or "widen") the
values so that each can be handled in an independent SIMD lane.

Implement a function that widens a sequence of packed `IN` byte values to an
`OUT` byte value by zero-filling on the high bytes. Let's consider our byte
array big-endian in the sense byte index `0` is the most significant byte.

## Signature

```dslx-snippet
fn widen_broadside<OUT: u32, IN: u32, N: u32>(x: u8[IN][N]) -> u8[OUT][N]
```

## Tests

```dslx
fn pad_bytes_left<OUT: u32, IN: u32>(x: u8[IN]) -> u8[OUT] {
    const_assert!(OUT >= IN);
    const INIT = u8[OUT]:[0, ...];
    for (i, accum) in u32:0..IN {
        update(accum, i+(OUT-IN), x[i])
    }(INIT)
}

#[test]
fn test_pad_bytes_left() {
    let x = u8[2]:[0xab, 0xcd];
    assert_eq(pad_bytes_left<u32:4>(x), u8[4]:[0, 0, 0xab, 0xcd])
}

const ELEMS = u32:1;
#[quickcheck]
fn quickcheck_widen_broadside(x: u8[2][ELEMS]) -> bool {
    const OUT = u32:4;
    let y: u8[4][ELEMS] = widen_broadside<OUT>(x);
    //trace_fmt!("x: {} y: {}", x, y);
    for (i, accum) in u32:0..ELEMS {
        if accum {
            y[i] == pad_bytes_left<OUT>(x[i])
        } else {
            false
        }
    }(true)
}
```
