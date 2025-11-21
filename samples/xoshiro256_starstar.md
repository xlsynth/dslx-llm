# Xoshiro256** ("xoshiro two-star")

## Prompt

Implement the 64-bit variant of the xoshiro family of pseudorandom number generators: `xoshiro256**` (pronounced “xoshiro two-star”). The generator maintains four 64-bit words of state. Each call produces a 64-bit random value **and** updates the internal state so that the next call yields the next value in the sequence.

---
The generator uses four 64-bit words of internal state. One *step* produces a 64-bit random value and advances the state as follows:

1. Multiply the **second** word of state by 5.
2. Rotate that product to the left by 7 bits.
3. Multiply the rotated value by 9 – the result is the random output for this step.
4. Create a temporary value `t` by shifting the **second** state word left by 17 bits.
5. Mix the state with a chain of XOR operations:
   • word₂ ← word₂ XOR word₀
   • word₃ ← word₃ XOR word₁
   • word₁ ← word₁ XOR word₂
   • word₀ ← word₀ XOR word₃
6. Incorporate `t` by XOR-ing it into word₂.
7. Rotate word₃ to the left by 45 bits.

After step 7 the four modified words become the new state, ready for the next call.

---

Notes:
1. `rotl` is a left rotate by `k` bits in the 64-bit word.
2. All arithmetic is performed modulo 2⁶⁴ (i.e. natural wrap-around of unsigned 64-bit integers).
3. The state **must** be non-zero as a *whole* (individual words may be zero).
4. After the update, the new state is `[s₀, s₁, s₂, s₃]` as modified above.

Your task is to translate the steps above into DSLX.

## Prologue

```dslx
struct XoshiroState {
    s: u64[4]
}
```

## Signature

```dslx-snippet
// Returns (random_value, next_state)
fn xoshiro256_ss_step(state: XoshiroState) -> (u64, XoshiroState)
```

## Tests

```dslx-snippet
// Helper: 64-bit rotate-left.
fn reference_rotl64(x: u64, k: u32) -> u64 {
    ((x << k) | (x >> (u32:64 - k)))  // automatic truncation to 64 bits
}

// One reference step lifted directly from the specification.
fn reference_step(st: XoshiroState) -> (u64, XoshiroState) {
    let result = reference_rotl64(st.s[1] * u64:5, u32:7) * u64:9;
    let t = st.s[1] << u64:17;

    let s_2 = st.s[2] ^ st.s[0];
    let s_3 = st.s[3] ^ st.s[1];
    let s_1 = st.s[1] ^ s_2;
    let s_0 = st.s[0] ^ s_3;
    let s_2 = s_2 ^ t;
    let s_3 = reference_rotl64(s_3, u32:45);

    let next = XoshiroState { s: [s_0, s_1, s_2, s_3] };
    (result, next)
}

// -- Tests

#[test]
fn test_known_sequence() {
    // Seed: {1,2,3,4}
    let st = XoshiroState { s: u64[4]:[1, 2, 3, 4] };
    let (v0, st) = reference_step(st);
    assert_eq(v0, u64:0x0000000000002d00);
    let (v1, st) = reference_step(st);
    assert_eq(v1, u64:0x0000000000000000);
    let (v2, st) = reference_step(st);
    assert_eq(v2, u64:0x000000005a007080);
    let (v3, _st) = reference_step(st);
    assert_eq(v3, u64:0x10e0000000009d80);
}

// Quick-check: our implementation matches the reference for one step.
#[quickcheck]
fn prop_step_matches_reference(seed0: u64, seed1: u64, seed2: u64, seed3: u64) -> bool {
    // Disallow the all-zero state per algorithm requirements.
    if (seed0 | seed1 | seed2 | seed3) == u64:0 {
        // Skip this input – quickcheck will try another.
        true
    } else {
        let st = XoshiroState { s: [seed0, seed1, seed2, seed3] };
        let (v_ref, st_ref) = reference_step(st);
        let (v_impl, st_impl) = xoshiro256_ss_step(st);
        v_ref == v_impl && st_ref == st_impl
    }
}
```
