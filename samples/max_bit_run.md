# Maximum Run of Bits

## Prompt

Given a bits value (i.e. a fixed-width input bit string), write a function that tells the longest run of set bits in that provided string.

## Signature

```dslx-snippet
fn max_bit_run<N: u32, CLOG2P1: u32 = {std::clog2(N) + u32:1}>(x: bits[N]) -> uN[CLOG2P1]
```

## Tests

```dslx-snippet
#[test]
fn test_two_bit_exhaustive() {
    const CASES = [
        (u2:0b00, u2:0),
        (u2:0b01, u2:1),
        (u2:0b10, u2:1),
        (u2:0b11, u2:2),
    ];
    for ((input, want), ()) in CASES {
        assert_eq(want, max_bit_run(input));
    }(());
}

#[test]
fn test_three_bit_exhaustive() {
    const CASES = [
        (u3:0b000, u3:0),  // 0
        (u3:0b001, u3:1),  // 1
        (u3:0b010, u3:1),  // 2
        (u3:0b011, u3:2),  // 3
        (u3:0b100, u3:1),  // 4
        (u3:0b101, u3:1),  // 5
        (u3:0b110, u3:2),  // 6
        (u3:0b111, u3:3),  // 7
    ];
    for ((input, want), ()) in CASES {
        assert_eq(want, max_bit_run(input));
    }(());
}

#[quickcheck]
fn prop_split(x: u6) -> bool {
    let lo_run: u3 = max_bit_run(x[0 +: u3]);
    let hi_run: u3 = max_bit_run(x[3 +: u3]);
    let overall_run: u4 = max_bit_run(x);
    // The overall run must be at least as long as the runs of the two halves,
    // and at most the sum of the runs of the two halves.
    overall_run >= lo_run as u4 && overall_run >= hi_run as u4 && overall_run <= (lo_run as u4 + hi_run as u4)
}

#[quickcheck]
fn prop_run_le_popcount(x: u8) -> bool {
    max_bit_run(x) as u8 <= std::popcount(x)
}
```
