# Skid Buffer Step

## Prompt

Implement one step of a one-entry ready/valid skid buffer.

The buffer sits between an upstream producer and a downstream consumer. The
state stores one word only when `state.full` is true. The step function returns
the next state and the combinational ready/valid/data signals for this cycle.

Semantics:

- If the buffer is empty, `in_ready` is true.
- If the buffer is empty and `in_valid` is true, the input appears at the
  output in the same cycle.
- If that empty-buffer output is not accepted because `out_ready` is false,
  the input word is captured into the buffer for the next cycle.
- If the buffer is full, the output is the buffered word.
- If the buffer is full and `out_ready` is false, the state must hold and
  `in_ready` is false.
- If the buffer is full and `out_ready` is true, the buffered word is consumed;
  a simultaneous valid input is accepted and becomes the next buffered word.
- Whenever the next state is empty, return the canonical empty state with
  `next_state.full == false` and `next_state.data == 0`.

The prologue will be automatically included, just implement the signature in
the output answer.

## Prologue

```dslx
struct SkidState<W: u32> {
    full: bool,
    data: uN[W],
}

struct SkidStep<W: u32> {
    next_state: SkidState<W>,
    in_ready: bool,
    out_valid: bool,
    out_data: uN[W],
}
```

## Signature

```dslx-snippet
fn skid_buffer_step<W: u32>(state: SkidState<W>, in_valid: bool, in_data: uN[W], out_ready: bool) -> SkidStep<W>
```

## Tests

```dslx-snippet
fn empty_skid<W: u32>() -> SkidState<W> {
    SkidState<W> { full: false, data: uN[W]:0 }
}

#[test]
fn test_empty_bypass_when_output_ready() {
    let state = empty_skid<u32:8>();
    let got = skid_buffer_step<u32:8>(state, true, u8:0x42, true);
    assert_eq(got, SkidStep<u32:8> {
        next_state: empty_skid<u32:8>(),
        in_ready: true,
        out_valid: true,
        out_data: u8:0x42,
    });
}

#[test]
fn test_empty_captures_when_output_stalled() {
    let state = empty_skid<u32:8>();
    let got = skid_buffer_step<u32:8>(state, true, u8:0x5a, false);
    assert_eq(got, SkidStep<u32:8> {
        next_state: SkidState<u32:8> { full: true, data: u8:0x5a },
        in_ready: true,
        out_valid: true,
        out_data: u8:0x5a,
    });
}

#[test]
fn test_full_holds_when_output_stalled() {
    let state = SkidState<u32:8> { full: true, data: u8:0xa5 };
    let got = skid_buffer_step<u32:8>(state, true, u8:0x11, false);
    assert_eq(got, SkidStep<u32:8> {
        next_state: state,
        in_ready: false,
        out_valid: true,
        out_data: u8:0xa5,
    });
}

#[test]
fn test_full_drains_or_replaces_when_output_ready() {
    let state = SkidState<u32:8> { full: true, data: u8:0xc3 };
    let drained = skid_buffer_step<u32:8>(state, false, u8:0x00, true);
    assert_eq(drained, SkidStep<u32:8> {
        next_state: empty_skid<u32:8>(),
        in_ready: true,
        out_valid: true,
        out_data: u8:0xc3,
    });

    let replaced = skid_buffer_step<u32:8>(state, true, u8:0x3c, true);
    assert_eq(replaced, SkidStep<u32:8> {
        next_state: SkidState<u32:8> { full: true, data: u8:0x3c },
        in_ready: true,
        out_valid: true,
        out_data: u8:0xc3,
    });
}

#[quickcheck]
fn prop_full_stall_holds_state(buffered: u8, incoming: u8, in_valid: bool) -> bool {
    let state = SkidState<u32:8> { full: true, data: buffered };
    let got = skid_buffer_step<u32:8>(state, in_valid, incoming, false);
    got.next_state == state && !got.in_ready && got.out_valid && got.out_data == buffered
}

#[quickcheck]
fn prop_empty_is_always_input_ready(in_valid: bool, in_data: u8, out_ready: bool) -> bool {
    let got = skid_buffer_step<u32:8>(empty_skid<u32:8>(), in_valid, in_data, out_ready);
    got.in_ready
}

#[quickcheck]
fn prop_output_valid_when_buffered_or_input_valid(full: bool, data: u8, in_valid: bool, in_data: u8, out_ready: bool) -> bool {
    let state = SkidState<u32:8> { full, data };
    let got = skid_buffer_step<u32:8>(state, in_valid, in_data, out_ready);
    got.out_valid == (full || in_valid)
}
```
