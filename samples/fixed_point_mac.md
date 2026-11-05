# Signed Fixed-Point Multiply-Accumulate

## Prompt

Implement a pure, stateless fixed-point multiply-accumulate. Each call computes
one complete MAC from its three explicit inputs; `acc` is an input value, not
hidden state. There are no pipeline stages or cycle-by-cycle updates.

The parameters satisfy `2 <= W <= 32` and `0 <= F < W`. Each input and the
output is a signed two's-complement W-bit code with F fractional bits: a raw
integer code x represents the real number x / 2^F. Every input bit pattern is
valid. Direct multiplication is permitted.

Let a, b, and acc denote the signed integer input codes. The required output
code is exactly:

    clamp(round_to_nearest_even((a*b + acc*2^F) / 2^F), -2^(W-1), 2^(W-1)-1)

All arithmetic in this mathematical definition is exact. Round to the nearest
integer, with an exact halfway value choosing the even integer, for either
sign. Include the accumulator before the single rounding step, and saturate
the rounded result to the signed W-bit range last. Intermediate products and
sums must not wrap or saturate. F=0 means integer arithmetic with saturation.

For example, W=16, F=8 and raw inputs (384, -320, 512) represent
(1.5, -1.25, 2.0); their MAC is 0.125, so the output code is 32.
With W=8, F=3, raw inputs (1, 4, 1) give 1.5 and output 2, while
(1, 4, 0) give 0.5 and output 0. Rounding the product before adding acc
would therefore be incorrect. Raw inputs (64, 16, -127) give output 1;
saturating the product before accumulation would also be incorrect.

Implement the function with the signature below.

## Signature

```dslx-snippet
fn fixed_point_mac<W: u32, F: u32>(a: sN[W], b: sN[W], acc: sN[W]) -> sN[W]
```

## Tests

```dslx-snippet
#[test]
fn fixed_point_mac_edge_cases() {
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:1, sN[8]:4, sN[8]:0), sN[8]:0);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:1, sN[8]:4, sN[8]:1), sN[8]:2);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:3, sN[8]:4, sN[8]:0), sN[8]:2);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-1, sN[8]:4, sN[8]:0), sN[8]:0);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-1, sN[8]:4, sN[8]:-1), sN[8]:-2);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-3, sN[8]:4, sN[8]:0), sN[8]:-2);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:1, sN[8]:3, sN[8]:0), sN[8]:0);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:1, sN[8]:5, sN[8]:0), sN[8]:1);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-1, sN[8]:3, sN[8]:0), sN[8]:0);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-1, sN[8]:5, sN[8]:0), sN[8]:-1);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-3, sN[8]:-4, sN[8]:-1), sN[8]:0);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-8, sN[8]:16, sN[8]:16), sN[8]:0);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:8, sN[8]:16, sN[8]:-16), sN[8]:0);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:64, sN[8]:16, sN[8]:-127), sN[8]:1);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-64, sN[8]:16, sN[8]:127), sN[8]:-1);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:127, sN[8]:127, sN[8]:-128), sN[8]:127);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-128, sN[8]:127, sN[8]:127), sN[8]:-128);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-128, sN[8]:-128, sN[8]:-128), sN[8]:127);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:1, sN[8]:4, sN[8]:127), sN[8]:127);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-1, sN[8]:4, sN[8]:-128), sN[8]:-128);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:1, sN[8]:4, sN[8]:126), sN[8]:126);
    assert_eq(fixed_point_mac<u32:8, u32:3>(sN[8]:-1, sN[8]:4, sN[8]:-127), sN[8]:-128);
    assert_eq(fixed_point_mac<u32:8, u32:0>(sN[8]:-128, sN[8]:-1, sN[8]:-1), sN[8]:127);
    assert_eq(fixed_point_mac<u32:8, u32:0>(sN[8]:-128, sN[8]:1, sN[8]:127), sN[8]:-1);
    assert_eq(fixed_point_mac<u32:8, u32:0>(sN[8]:127, sN[8]:2, sN[8]:-128), sN[8]:126);
    assert_eq(fixed_point_mac<u32:8, u32:7>(sN[8]:-128, sN[8]:-128, sN[8]:-128), sN[8]:0);
    assert_eq(fixed_point_mac<u32:8, u32:7>(sN[8]:-128, sN[8]:127, sN[8]:127), sN[8]:0);
    assert_eq(fixed_point_mac<u32:5, u32:2>(sN[5]:3, sN[5]:-7, sN[5]:4), sN[5]:-1);
    assert_eq(fixed_point_mac<u32:5, u32:2>(sN[5]:-16, sN[5]:-16, sN[5]:-16), sN[5]:15);
    assert_eq(fixed_point_mac<u32:16, u32:8>(sN[16]:384, sN[16]:-320, sN[16]:512), sN[16]:32);
    assert_eq(fixed_point_mac<u32:16, u32:8>(sN[16]:-32768, sN[16]:-32768, sN[16]:-32768), sN[16]:32767);
    assert_eq(fixed_point_mac<u32:16, u32:8>(sN[16]:128, sN[16]:1, sN[16]:1), sN[16]:2);
    assert_eq(fixed_point_mac<u32:16, u32:8>(sN[16]:-128, sN[16]:1, sN[16]:-1), sN[16]:-2);
    assert_eq(fixed_point_mac<u32:16, u32:8>(sN[16]:32767, sN[16]:256, sN[16]:-32768), sN[16]:-1);
    assert_eq(fixed_point_mac<u32:16, u32:8>(sN[16]:-32768, sN[16]:256, sN[16]:32767), sN[16]:-1);
    assert_eq(fixed_point_mac<u32:32, u32:0>(sN[32]:-2147483648, sN[32]:-1, sN[32]:-1), sN[32]:2147483647);
    assert_eq(fixed_point_mac<u32:32, u32:0>(sN[32]:2147483647, sN[32]:2, sN[32]:-2147483648), sN[32]:2147483646);
    assert_eq(fixed_point_mac<u32:32, u32:16>(sN[32]:-2147483648, sN[32]:-1, sN[32]:0), sN[32]:32768);
    assert_eq(fixed_point_mac<u32:32, u32:16>(sN[32]:2147483647, sN[32]:65536, sN[32]:-2147483648), sN[32]:-1);
    assert_eq(fixed_point_mac<u32:32, u32:31>(sN[32]:-2147483648, sN[32]:-2147483648, sN[32]:-2147483648), sN[32]:0);
    assert_eq(fixed_point_mac<u32:32, u32:31>(sN[32]:-2147483648, sN[32]:2147483647, sN[32]:2147483647), sN[32]:0);
    assert_eq(fixed_point_mac<u32:32, u32:31>(sN[32]:1073741824, sN[32]:1, sN[32]:1), sN[32]:2);
    assert_eq(fixed_point_mac<u32:32, u32:31>(sN[32]:-1073741824, sN[32]:1, sN[32]:-1), sN[32]:-2);
}

#[quickcheck]
fn zero_product_identity(a: s16, acc: s16) -> bool {
    fixed_point_mac<u32:16, u32:8>(a, s16:0, acc) == acc &&
    fixed_point_mac<u32:16, u32:8>(s16:0, a, acc) == acc
}

#[quickcheck]
fn multiplicands_commute(a: s16, b: s16, acc: s16) -> bool {
    fixed_point_mac<u32:16, u32:8>(a, b, acc) ==
    fixed_point_mac<u32:16, u32:8>(b, a, acc)
}

#[quickcheck]
fn unsaturated_sign_symmetry(a: s8, b: s8, acc: s8) -> bool {
    let aw = a as s16;
    let bw = b as s16;
    let cw = acc as s16;
    fixed_point_mac<u32:16, u32:8>(-aw, bw, -cw) ==
    -fixed_point_mac<u32:16, u32:8>(aw, bw, cw)
}


// Check a proposed result against its representable neighbors. This predicate
// does not construct a rounded or saturated answer. All callers use W <= 32,
// so sN[128] distances and adjacent scaled values cannot overflow.
fn mac_result_is_nearest_even(numerator: sN[128], scale: sN[128], actual: sN[128], lower: sN[128], upper: sN[128]) -> bool {
    let error = numerator - actual * scale;
    let lower_error = error + scale;
    let upper_error = error - scale;
    let distance = if error < sN[128]:0 { -error } else { error };
    let lower_distance = if lower_error < sN[128]:0 { -lower_error } else { lower_error };
    let upper_distance = if upper_error < sN[128]:0 { -upper_error } else { upper_error };
    let even = (actual & sN[128]:1) == sN[128]:0;
    actual >= lower && actual <= upper &&
    (actual == lower || distance < lower_distance || (distance == lower_distance && even)) &&
    (actual == upper || distance < upper_distance || (distance == upper_distance && even))
}

fn mac_obeys_contract<W: u32, F: u32>(a: sN[W], b: sN[W], acc: sN[W]) -> bool {
    let scale = sN[128]:1 << F;
    let numerator = (a as sN[128]) * (b as sN[128]) + (acc as sN[128]) * scale;
    let lower = -(sN[128]:1 << (W - u32:1));
    let upper = -lower - sN[128]:1;
    let actual = fixed_point_mac<W, F>(a, b, acc) as sN[128];
    mac_result_is_nearest_even(numerator, scale, actual, lower, upper)
}


#[quickcheck(exhaustive)]
fn all_scales_w2(a: sN[2], b: sN[2], acc: sN[2]) -> bool {
    mac_obeys_contract<u32:2, u32:0>(a, b, acc) &&
    mac_obeys_contract<u32:2, u32:1>(a, b, acc)
}

#[quickcheck(exhaustive)]
fn all_scales_w3(a: sN[3], b: sN[3], acc: sN[3]) -> bool {
    mac_obeys_contract<u32:3, u32:0>(a, b, acc) &&
    mac_obeys_contract<u32:3, u32:1>(a, b, acc) &&
    mac_obeys_contract<u32:3, u32:2>(a, b, acc)
}

#[quickcheck(exhaustive)]
fn all_scales_w4(a: sN[4], b: sN[4], acc: sN[4]) -> bool {
    mac_obeys_contract<u32:4, u32:0>(a, b, acc) &&
    mac_obeys_contract<u32:4, u32:1>(a, b, acc) &&
    mac_obeys_contract<u32:4, u32:2>(a, b, acc) &&
    mac_obeys_contract<u32:4, u32:3>(a, b, acc)
}

#[quickcheck]
fn representative_scales_w5(a: sN[5], b: sN[5], acc: sN[5]) -> bool {
    mac_obeys_contract<u32:5, u32:0>(a, b, acc) &&
    mac_obeys_contract<u32:5, u32:4>(a, b, acc)
}

#[quickcheck]
fn representative_scales_w8(a: sN[8], b: sN[8], acc: sN[8]) -> bool {
    mac_obeys_contract<u32:8, u32:3>(a, b, acc) &&
    mac_obeys_contract<u32:8, u32:7>(a, b, acc)
}

#[quickcheck]
fn representative_scales_w16(a: sN[16], b: sN[16], acc: sN[16]) -> bool {
    mac_obeys_contract<u32:16, u32:0>(a, b, acc) &&
    mac_obeys_contract<u32:16, u32:8>(a, b, acc) &&
    mac_obeys_contract<u32:16, u32:15>(a, b, acc)
}

#[quickcheck]
fn representative_scales_w32(a: sN[32], b: sN[32], acc: sN[32]) -> bool {
    mac_obeys_contract<u32:32, u32:0>(a, b, acc) &&
    mac_obeys_contract<u32:32, u32:16>(a, b, acc) &&
    mac_obeys_contract<u32:32, u32:31>(a, b, acc)
}
// Constrain operand magnitudes so these checks exercise fractional arithmetic
// throughout the result range instead of overwhelmingly exercising saturation.
#[quickcheck]
fn nonsaturating_w16_f8(a: s10, b: s10, acc: s14) -> bool {
    mac_obeys_contract<u32:16, u32:8>(a as s16, b as s16, acc as s16)
}

#[quickcheck]
fn nonsaturating_w32_f16(a: s24, b: s24, acc: s30) -> bool {
    mac_obeys_contract<u32:32, u32:16>(a as s32, b as s32, acc as s32)
}
```
