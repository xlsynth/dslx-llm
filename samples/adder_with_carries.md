# Adder With Carries

## Prompt

Implement a function that implements an adder function whose signature takes a "carry in" and
produces a "carry out" in addition to the operands that should be added.

## Signature

```dslx-snippet
fn adder<N: u32>(x: uN[N], y: uN[N], carry_in: bool) -> (bool, uN[N])
```

## Tests

```dslx-snippet
#[test]
fn test_1b_exhaustive() {
    let cases = [
        ((false, false, false), (false, false)),  // 0: 0 + 0 + 0 => 0b00
        ((false, false, true), (false, true)),  // 1: 0 + 0 + 1 => 0b01
        ((false, true, false), (false, true)),  // 2: 0 + 1 + 0 => 0b01
        ((false, true, true), (true, false)),  // 3: 0 + 1 + 1 => 0b10
        ((true, false, false), (false, true)),  // 4: 1 + 0 + 0 => 0b01
        ((true, false, true), (true, false)),  // 5: 1 + 0 + 1 => 0b10
        ((true, true, false), (true, false)),  // 6: 1 + 1 + 0 => 0b10
        ((true, true, true), (true, true)),  // 7: 1 + 1 + 1 => 0b11
    ];
    for ((args, want), ()) in cases {
        let (x, y, carry_in) = args;
        let got = adder(x, y, carry_in);
        assert_eq(want, got);
    }(());
}

#[quickcheck(exhaustive)]
fn quickcheck_compare_vs_std(x: u4, y: u4) -> bool {
    let (overflow, sum) = std::uadd_with_overflow<u32:4>(x, y);
    let (got_carry, got_sum) = adder(x, y, false);
    got_carry == overflow && got_sum == sum
}
```
