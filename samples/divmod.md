# Division and Modulus (divmod)

## Prompt

Write a divide unit implementation in DSLX as a function that provides both
division and modulus results efficiently -- make it parameterized on bit count
`N`.

Describe in a comment which division algorithm you used for implementation.

## Sub-Prompts

* Attempt to implement via a restoring division algorithm.
* Attempt to implement via a non-restoring division algorithm.
* Attempt to implement via an SRT division algorithm (radix-16). In this
  implementation give a real estimation of quotient digit, not a placeholder.
* Attempt to implement via Goldschmidt's algorithm.
* Attempt to implement via Newton-Raphson.

## Signature

```dslx-snippet
fn divide<N: u32>(dividend: uN[N], divisor: uN[N]) -> (uN[N], uN[N])
```

## Tests

```dslx-snippet
#[test]
fn test_divide() {
    // Test with N = 4.
    let dividend = u4:13;
    let divisor = u4:3;
    let (quotient, remainder) = divide(dividend, divisor);
    assert_eq(quotient, u4:4);
    assert_eq(remainder, u4:1);

    // Test with N = 8.
    let dividend = u8:200;
    let divisor = u8:15;
    let (quotient, remainder) = divide(dividend, divisor);
    assert_eq(quotient, u8:13);
    assert_eq(remainder, u8:5);

    // Test division by one.
    let dividend = u8:123;
    let divisor = u8:1;
    let (quotient, remainder) = divide(dividend, divisor);
    assert_eq(quotient, u8:123);
    assert_eq(remainder, u8:0);
}

// Quickcheck test to verify the division properties for u32.
#[quickcheck]
fn test_divide_u32(dividend: u32, divisor: u32) -> bool {
    // Skip division by zero cases.
    if divisor == u32:0 {
        true
    } else {
        const N = u32:32;
        let (quotient, remainder) = divide<N>(dividend, divisor);

        // Reconstruct the dividend.
        let reconstructed_dividend = (divisor * quotient) + remainder;

        // Check that the reconstructed dividend matches the original dividend.
        let property1 = reconstructed_dividend == dividend;

        // Check that the remainder is less than the divisor.
        let property2 = remainder < divisor;

        // Check that the quotient and remainder are within the valid range.
        let property3 = quotient <= dividend;

        property1 && property2 && property3
    }
}

fn golden_reference<N: u32>(dividend: uN[N], divisor: uN[N]) -> (uN[N], uN[N]) {
    let q = dividend / divisor;
    let r = dividend % divisor;
    (q, r)
}

#[quickcheck]
fn test_vs_grm(dividend: u16, divisor: u16) -> bool {
    let (want_q, want_r) = golden_reference(dividend, divisor);
    let (got_q, got_r) = divide(dividend, divisor);
    got_q == want_q && got_r == want_r
}
```
