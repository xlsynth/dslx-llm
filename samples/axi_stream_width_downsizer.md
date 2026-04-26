# AXI Stream Width Downsizer

## Prompt

Implement one step of a fixed 32-bit to 8-bit ready/valid stream downsizer.

The input side presents one `u32` word plus an `in_last` flag. The output side
emits the word as four `u8` beats in LSB-first byte order:

- byte 0: bits `7..0`
- byte 1: bits `15..8`
- byte 2: bits `23..16`
- byte 3: bits `31..24`

The `in_last` flag associated with an input word must appear only on byte 3 of
that word.

Handshake semantics:

- `out_valid` means `out_data` and `out_last` are meaningful this cycle.
- An output beat is accepted only when `out_valid && out_ready`.
- `in_ready` is true only when the downsizer is idle and can accept a new
  `u32` word.
- When idle and `in_valid` is true, byte 0 appears at the output in the same
  cycle.
- If that byte 0 output is accepted immediately, the next state should hold
  byte index 1 of the same input word.
- If that byte 0 output is not accepted, the next state should hold byte index
  0 of the same input word, and the same byte must be presented again next
  cycle.
- While busy, do not accept a new input word. Hold `out_data` and `out_last`
  stable when `out_ready` is false.
- After byte 3 is accepted, return to the canonical idle state with
  `busy == false`, `data == 0`, `index == 0`, and `last == false`.
- When `out_valid` is false, return the canonical invalid output with
  `out_data == 0` and `out_last == false`.

The prologue will be automatically included, just implement the signature in
the output answer.

## Prologue

```dslx
struct DownsizerState {
    busy: bool,
    data: u32,
    index: u2,
    last: bool,
}

struct DownsizerStep {
    next_state: DownsizerState,
    in_ready: bool,
    out_valid: bool,
    out_data: u8,
    out_last: bool,
}
```

## Signature

```dslx-snippet
fn axis_downsizer_step(state: DownsizerState, in_valid: bool, in_data: u32, in_last: bool, out_ready: bool) -> DownsizerStep
```

## Tests

```dslx-snippet
fn idle_downsizer() -> DownsizerState {
    DownsizerState { busy: false, data: u32:0, index: u2:0, last: false }
}

#[test]
fn test_idle_no_input() {
    let got = axis_downsizer_step(idle_downsizer(), false, u32:0x11223344, true, true);
    assert_eq(got, DownsizerStep {
        next_state: idle_downsizer(),
        in_ready: true,
        out_valid: false,
        out_data: u8:0,
        out_last: false,
    });
}

#[test]
fn test_idle_input_stalled_repeats_byte_zero() {
    let got0 = axis_downsizer_step(idle_downsizer(), true, u32:0xaabbccdd, true, false);
    assert_eq(got0, DownsizerStep {
        next_state: DownsizerState { busy: true, data: u32:0xaabbccdd, index: u2:0, last: true },
        in_ready: true,
        out_valid: true,
        out_data: u8:0xdd,
        out_last: false,
    });

    let got1 = axis_downsizer_step(got0.next_state, false, u32:0, false, false);
    assert_eq(got1, DownsizerStep {
        next_state: got0.next_state,
        in_ready: false,
        out_valid: true,
        out_data: u8:0xdd,
        out_last: false,
    });
}

#[test]
fn test_idle_input_accepted_advances_to_byte_one() {
    let got = axis_downsizer_step(idle_downsizer(), true, u32:0xaabbccdd, true, true);
    assert_eq(got, DownsizerStep {
        next_state: DownsizerState { busy: true, data: u32:0xaabbccdd, index: u2:1, last: true },
        in_ready: true,
        out_valid: true,
        out_data: u8:0xdd,
        out_last: false,
    });
}

#[test]
fn test_busy_sequence_lsb_first_and_last_only_on_final_byte() {
    let st1 = DownsizerState { busy: true, data: u32:0xaabbccdd, index: u2:1, last: true };

    let got1 = axis_downsizer_step(st1, true, u32:0x01020304, false, true);
    assert_eq(got1, DownsizerStep {
        next_state: DownsizerState { busy: true, data: u32:0xaabbccdd, index: u2:2, last: true },
        in_ready: false,
        out_valid: true,
        out_data: u8:0xcc,
        out_last: false,
    });

    let got2 = axis_downsizer_step(got1.next_state, false, u32:0, false, true);
    assert_eq(got2, DownsizerStep {
        next_state: DownsizerState { busy: true, data: u32:0xaabbccdd, index: u2:3, last: true },
        in_ready: false,
        out_valid: true,
        out_data: u8:0xbb,
        out_last: false,
    });

    let got3 = axis_downsizer_step(got2.next_state, false, u32:0, false, true);
    assert_eq(got3, DownsizerStep {
        next_state: idle_downsizer(),
        in_ready: false,
        out_valid: true,
        out_data: u8:0xaa,
        out_last: true,
    });
}

#[test]
fn test_busy_final_byte_without_last_returns_idle_without_out_last() {
    let state = DownsizerState { busy: true, data: u32:0x01020304, index: u2:3, last: false };
    let got = axis_downsizer_step(state, false, u32:0, false, true);
    assert_eq(got, DownsizerStep {
        next_state: idle_downsizer(),
        in_ready: false,
        out_valid: true,
        out_data: u8:0x01,
        out_last: false,
    });
}

#[quickcheck]
fn prop_busy_stall_holds_state_and_output(data: u32, index: u2, last: bool, in_valid: bool, in_data: u32, in_last: bool) -> bool {
    let state = DownsizerState { busy: true, data, index, last };
    let got = axis_downsizer_step(state, in_valid, in_data, in_last, false);
    got.next_state == state && !got.in_ready && got.out_valid
}

#[quickcheck]
fn prop_idle_always_input_ready(in_valid: bool, in_data: u32, in_last: bool, out_ready: bool) -> bool {
    axis_downsizer_step(idle_downsizer(), in_valid, in_data, in_last, out_ready).in_ready
}

#[quickcheck]
fn prop_out_last_only_on_final_byte(data: u32, index: u2, last: bool, out_ready: bool) -> bool {
    let state = DownsizerState { busy: true, data, index, last };
    let got = axis_downsizer_step(state, false, u32:0, false, out_ready);
    got.out_last == (last && index == u2:3)
}
```
