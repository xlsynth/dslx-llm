# Bitwise Majority

## Prompt

Compute the bitwise majority or minority of three inputs. For each bit
position, the result is ‘1’ if at least two inputs have a ‘1’ (majority), or
for minority the opposite. The mode determines which you do.

Please emit the `Mode` enum provided into the output answer.

## Signature

```dslx-snippet
enum Mode : u1 {
    MAJ = 0,
    MIN = 1,
}
fn bitwise_maj_min<N: u32>(a: bits[N], b: bits[N], c: bits[N],
                           mode: Mode) -> bits[N]
```

## Tests

```dslx-snippet
#[test]
fn test_bitwise_maj_min() {
    let a = bits[4]:0b1100;
    let b = bits[4]:0b1010;
    let c = bits[4]:0b1001;

    let maj_result = bitwise_maj_min(a, b, c, Mode::MAJ);
    let min_result = bitwise_maj_min(a, b, c, Mode::MIN);

    // Majority: 1100 & 1010 = 1000; 1010 & 1001 = 1000; 1100 & 1001 = 1000
    // Result = 1000
    assert_eq(maj_result, bits[4]:0b1000);

    // Minority: NOT(Majority)
    assert_eq(min_result, bits[4]:0b0111);
}

#[quickcheck(exhaustive)]
fn prop_bitwise_maj_min(a: bits[4], b: bits[4], c: bits[4], mode: Mode) -> bool {
    let result = bitwise_maj_min(a, b, c, mode);

    // Property 1: For mode == MAJ, result matches the bitwise majority condition.
    let majority_condition = if mode == Mode::MAJ {
        let maj = (a & b) | (b & c) | (a & c);
        result == maj
    } else {
        true  // Skip this condition for minority mode
    };

    // Property 2: For mode == MIN, result matches the bitwise minority condition.
    let minority_condition = if mode == Mode::MIN {
        let maj = (a & b) | (b & c) | (a & c);
        let min = !(maj);
        result == min
    } else {
        true  // Skip this condition for majority mode
    };

    majority_condition && minority_condition
}

#[quickcheck(exhaustive)]
fn prop_symmetry(a: bits[4], b: bits[4], c: bits[4], mode: Mode) -> bool {
    let result_abc = bitwise_maj_min(a, b, c, mode);
    let result_cba = bitwise_maj_min(c, b, a, mode);
    result_abc == result_cba
}

#[quickcheck(exhaustive)]
fn prop_idempotency(a: bits[4], mode: Mode) -> bool {
    let result = bitwise_maj_min(a, a, a, mode);
    match mode {
        Mode::MAJ => result == a,
        _ => result == !a,
    }
}

#[quickcheck(exhaustive)]
fn prop_complementarity(a: bits[4], b: bits[4], c: bits[4]) -> bool {
    let majority = bitwise_maj_min(a, b, c, Mode::MAJ);
    let minority = bitwise_maj_min(a, b, c, Mode::MIN);
    majority == !minority
}
```
