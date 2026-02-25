# Time-Multiplexed Adder

## Prompt

Implement a truly time-multiplexed adder API with explicit state.

You must define `AddState<N: u32, S: u32>` yourself and implement:

- `add_init`
- `add_step`
- `get_result`
- `get_carry_out`

Interface:

```dslx-snippet
fn add_init<N: u32, S: u32>(x: bits[N], y: bits[N], c_in: bool) -> AddState<N, S>
fn add_step<N: u32, S: u32>(st: AddState<N, S>) -> AddState<N, S>
fn get_result<N: u32, S: u32>(st: AddState<N, S>) -> bits[N]
fn get_carry_out<N: u32, S: u32>(st: AddState<N, S>) -> bool
```

Semantics:

- Assume `N % S == 0`; each stage handles one `N/S`-bit chunk.
- `add_init` loads inputs/state for a fresh operation.
- `add_step` performs exactly one chunk stage and advances the internal stage index.
- After exactly `S` calls to `add_step`, `get_result`/`get_carry_out` must match `x + y + c_in`.
- It is acceptable to keep outputs stable if `add_step` is called after completion.

Usage model:

- This API is intentionally stateful: inputs are provided once via `add_init`.
- Tests will pump the state with a loop of exactly `S` steps before checking outputs.

The prologue will be automatically included, so implement only what is requested in the signature.

## Requirements

The following requirements will be checked by a separate critic model. The critic should treat comments as claims, not proof, and decide from actual DSLX structure.

- id: one_chunk_per_step
  requirement: `add_step` must compute one chunk (`N/S` bits) per call, not all chunks at once.

- id: staged_chunk_decomposition
  requirement: The datapath must propagate carry stage-to-stage across chunk updates and use an explicit internal stage index or equivalent state.

- id: no_single_full_width_add
  requirement: The implementation must not compute the final result via a single direct full-width add expression like `x + y`, `x + y + ...`, or equivalent on `uN[N]`/`bits[N]`. Small-width per-chunk arithmetic is allowed.

## Prologue

```dslx
```

## Signature

```dslx-snippet
fn add_init<N: u32, S: u32>(x: bits[N], y: bits[N], c_in: bool) -> AddState<N, S>
fn add_step<N: u32, S: u32>(st: AddState<N, S>) -> AddState<N, S>
fn get_result<N: u32, S: u32>(st: AddState<N, S>) -> bits[N]
fn get_carry_out<N: u32, S: u32>(st: AddState<N, S>) -> bool
```

## Tests

```dslx-snippet
fn add_reference<N: u32>(x: bits[N], y: bits[N], c_in: bool) -> (bool, bits[N]) {
    let x_u = x as uN[N];
    let y_u = y as uN[N];
    let (carry0, sum0) = std::uadd_with_overflow<N, N, N>(x_u, y_u);
    let cin_u = if c_in { uN[N]:1 } else { uN[N]:0 };
    let (carry1, sum1) = std::uadd_with_overflow<N, N, N>(sum0, cin_u);
    (carry0 || carry1, sum1 as bits[N])
}

fn run_steps<N: u32, S: u32>(x: bits[N], y: bits[N], c_in: bool) -> AddState<N, S> {
    let st0 = add_init<N, S>(x, y, c_in);
    let st_final: AddState<N, S> = for (_, st): (u32, AddState<N, S>) in u32:0..S {
        add_step<N, S>(st)
    }(st0);
    st_final
}

#[test]
fn test_time_multiplexed_adder_n256_s4() {
    const N = u32:256;
    const S = u32:4;
    let x = bits[N]:0x123456789abcdef00112233445566778899aabbccddeeff00fedcba987654321;
    let y = bits[N]:0x0f0e0d0c0b0a09080706050403020100ffeeddccbbaa99887766554433221100;
    let st = run_steps<N, S>(x, y, true);
    let got = (get_carry_out<N, S>(st), get_result<N, S>(st));
    let want = add_reference<N>(x, y, true);
    assert_eq(got, want);
}

#[quickcheck(exhaustive)]
fn quickcheck_compare_reference_u4_s2(x: u4, y: u4, c_in: bool) -> bool {
    let st = run_steps<u32:4, u32:2>(x as bits[4], y as bits[4], c_in);
    let got = (get_carry_out<u32:4, u32:2>(st), get_result<u32:4, u32:2>(st));
    let want = add_reference<u32:4>(x as bits[4], y as bits[4], c_in);
    got == want
}

#[quickcheck]
fn quickcheck_compare_reference_u16_s4(x: u16, y: u16, c_in: bool) -> bool {
    let st = run_steps<u32:16, u32:4>(x as bits[16], y as bits[16], c_in);
    let got = (get_carry_out<u32:16, u32:4>(st), get_result<u32:16, u32:4>(st));
    let want = add_reference<u32:16>(x as bits[16], y as bits[16], c_in);
    got == want
}

#[quickcheck]
fn quickcheck_compare_reference_u32_s8(x: u32, y: u32, c_in: bool) -> bool {
    let st = run_steps<u32:32, u32:8>(x as bits[32], y as bits[32], c_in);
    let got = (get_carry_out<u32:32, u32:8>(st), get_result<u32:32, u32:8>(st));
    let want = add_reference<u32:32>(x as bits[32], y as bits[32], c_in);
    got == want
}

#[quickcheck]
fn quickcheck_compare_reference_u64_s2(x: u64, y: u64, c_in: bool) -> bool {
    let st = run_steps<u32:64, u32:2>(x as bits[64], y as bits[64], c_in);
    let got = (get_carry_out<u32:64, u32:2>(st), get_result<u32:64, u32:2>(st));
    let want = add_reference<u32:64>(x as bits[64], y as bits[64], c_in);
    got == want
}

#[quickcheck]
fn quickcheck_compare_reference_u64_s4(x: u64, y: u64, c_in: bool) -> bool {
    let st = run_steps<u32:64, u32:4>(x as bits[64], y as bits[64], c_in);
    let got = (get_carry_out<u32:64, u32:4>(st), get_result<u32:64, u32:4>(st));
    let want = add_reference<u32:64>(x as bits[64], y as bits[64], c_in);
    got == want
}

#[quickcheck]
fn quickcheck_compare_reference_u64_s8(x: u64, y: u64, c_in: bool) -> bool {
    let st = run_steps<u32:64, u32:8>(x as bits[64], y as bits[64], c_in);
    let got = (get_carry_out<u32:64, u32:8>(st), get_result<u32:64, u32:8>(st));
    let want = add_reference<u32:64>(x as bits[64], y as bits[64], c_in);
    got == want
}

#[quickcheck]
fn quickcheck_compare_reference_u64_s16(x: u64, y: u64, c_in: bool) -> bool {
    let st = run_steps<u32:64, u32:16>(x as bits[64], y as bits[64], c_in);
    let got = (get_carry_out<u32:64, u32:16>(st), get_result<u32:64, u32:16>(st));
    let want = add_reference<u32:64>(x as bits[64], y as bits[64], c_in);
    got == want
}

#[quickcheck]
fn quickcheck_compare_reference_u64_s32(x: u64, y: u64, c_in: bool) -> bool {
    let st = run_steps<u32:64, u32:32>(x as bits[64], y as bits[64], c_in);
    let got = (get_carry_out<u32:64, u32:32>(st), get_result<u32:64, u32:32>(st));
    let want = add_reference<u32:64>(x as bits[64], y as bits[64], c_in);
    got == want
}
```
