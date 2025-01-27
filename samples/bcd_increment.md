# BCD Increment

## Prompt

A BCD digit represents the values from 0 (0b0000) to 9 (0b1001). Implement a
function that increments an N-digit BCD number and returns:

- whether the result was an overflow
- what the incremented value is -- in the case of overflow, this should be zero

The prologue will be automatically included, just implement the signature in the output answer.

## Prologue

```dslx
type BcdDigit = u4;
```

## Signature

```dslx-snippet
fn bcd_increment<N: u32>(x: BcdDigit[N]) -> (bool, BcdDigit[N])
```

## Tests

```dslx-snippet
const BCD0 = BcdDigit:0b0000;
const BCD9 = BcdDigit:0b1001;

fn bcd_valid(x: BcdDigit) -> bool { x <= BCD9 }

enum Cmp: s2 {
    LT = -1,
    EQ = 0,
    GT = 1,
}

fn bcd_cmp(lhs: BcdDigit, rhs: BcdDigit) -> Cmp {
    if lhs < rhs { Cmp::LT }
    else if lhs == rhs { Cmp::EQ }
    else { Cmp::GT }
}

fn bcd_cmp_N<N: u32>(lhs: BcdDigit[N], rhs: BcdDigit[N]) -> Cmp {
    for (i, accum) in u32:0..N {
        match accum {
            Cmp::EQ => bcd_cmp(lhs[i], rhs[i]),
            _ => accum,
        }
    }(Cmp::EQ)
}

#[test]
fn test_bcd_cmp_3() {
    assert_eq(bcd_cmp_N(BcdDigit[3]:[BCD0, BCD0, BCD0], BcdDigit[3]:[BCD0, BCD0, BCD0]), Cmp::EQ)
}

fn bcd_gt_N<N: u32>(lhs: BcdDigit[N], rhs: BcdDigit[N]) -> bool {
    bcd_cmp_N(lhs, rhs) == Cmp::GT
}

fn is_bcd_max(x: BcdDigit) -> bool { x == BCD9 }

fn is_bcd_max_N<N: u32>(x: BcdDigit[N]) -> bool {
    and_reduce(map(x, is_bcd_max) as uN[N])
}

#[quickcheck]
fn quickcheck_bcd_increment(x: BcdDigit[3]) -> bool {
    let values_valid = and_reduce(map(x, bcd_valid) as u3);
    if !values_valid {
        true
    } else {
        let (overflow, y) = bcd_increment(x);
        if overflow {
            is_bcd_max_N(x)
        } else {
            bcd_gt_N(y, x)
        }
    }
}
```
