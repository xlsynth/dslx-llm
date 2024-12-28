# Modular Exponentiation Unit

## Prompt

Implement a modular exponentiation unit. Given `base`, `exponent`, and
`modulus`, compute `(base^exponent) mod modulus`. This is often needed in
cryptographic computations and is much more involved than built-in operations.

Your function should be parameterized by the bit-width `N` of the inputs, and
it should handle large inputs efficiently using a method such as "square-and-
multiply" (also known as "exponentiation by squaring").

### Key Points

- Parameterized on bit-width `N`.
- Inputs and output are `uN[N]`.
- Use an algorithm that performs repeated squaring and modular reductions.
- Should handle large exponents by iterative or recursive decomposition.

## Signature

```dslx-snippet
fn modexp<N: u32>(base: uN[N], exponent: uN[N], modulus: uN[N]) -> uN[N]
```

## Tests

```dslx
#[test]
fn test_modexp_simple() {
    // Test a known result: 2^10 = 1024, 1024 % 1000 = 24
    assert_eq(modexp<u32:32>(u32:2, u32:10, u32:1000), u32:24);

    // Check another case: 3^7 = 2187, 2187 % 13 = 2187 % 13 = 2187 / 13 = 168 remainder 3
    assert_eq(modexp<u32:32>(u32:3, u32:7, u32:13), u32:3);

    // And a trivial case:
    // (base^0) % modulus should be 1 for any base, given modulus != 0
    assert_eq(modexp<u32:32>(u32:5, u32:0, u32:17), u32:1);
}

fn modexp_naive<N: u32>(base: uN[N], exponent: uN[N], modulus: uN[N]) -> uN[N] {
    // Naive (slow) implementation just for verification:
    // result = 1
    // for i in [0 .. exponent):
    //    result = (result * base) % modulus
    //
    // This will be very slow for large exponents, so we use small N for quickcheck.
    //
    // If modulus == 0, the operation doesn't make sense, return zero for that degenerate case.
    if modulus == uN[N]:0 {
        uN[N]:0
    } else {
        let result = for (i, accum) in range(u32:0, exponent as u32) {
            (accum * base) % modulus
        }(uN[N]:1);
        result
    }
}

// Quickcheck test for modexp using small width for exhaustive testing
#[quickcheck]
fn modexp_quickcheck(base: u8, exponent: u8, modulus: u8) -> bool {
    // If modulus is zero, let's just say the property is trivially true since mod 0 is undefined.
    if modulus == u8:0 {
        true
    } else {
        let ref_val = modexp_naive<u32:8>(base, exponent, modulus);
        let dut_val = modexp<u32:8>(base, exponent, modulus);
        ref_val == dut_val
    }
}
```
