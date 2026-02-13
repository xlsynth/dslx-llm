# Single-Port Stack Step

## Prompt

Implement one cycle of a stack datapath backed by a single-ported memory.

The memory array is provided as input and should be treated as read-only in this function.
Your function must return the next stack count, an operation response, and exactly one write-port intent.

Operations:

- `NOOP`: no state change, no write.
- `PUSH`: if `count < DEPTH`, write `push_data` at address `count` and increment count.
- `POP`: if `count > 0`, decrement count and return the value at address `count - 1`; no write.

Overflow and underflow behavior:

- `PUSH` when full (`count >= DEPTH`) sets `overflow = true`, does not write, and does not change count.
- `POP` when empty (`count == 0`) sets `underflow = true`, does not write, and does not change count.

Single-port contract:

- At most one memory write may be requested per cycle.

The prologue will be automatically included, so implement only the functions listed in the signature section.

## Requirements

The following requirements will be checked by a separate critic model. The critic should treat comments as claims, not proof, and decide from the actual DSLX structure.

- id: single_write_port_only
  requirement: The implementation must produce at most one memory write intent per step. For `POP`, `NOOP`, overflow, and underflow cases, it must not request a write.

- id: no_full_array_rebuild
  requirement: The implementation must not rebuild or map over the full memory array to emulate writes. It should compute the write-port output directly from control conditions and indices.

## Prologue

```dslx
enum StackOp : u2 {
    NOOP = 0,
    PUSH = 1,
    POP = 2,
}

struct StackResp<W: u32> {
    pop_valid: bool,
    pop_data: uN[W],
    overflow: bool,
    underflow: bool,
}

struct StackWrite<W: u32, AW: u32> {
    we: bool,
    addr: uN[AW],
    data: uN[W],
}
```

## Signature

```dslx-snippet
fn stack_step<DEPTH: u32, W: u32, AW: u32 = {std::clog2(DEPTH)}>(mem: uN[W][DEPTH], count: u32, op: StackOp, push_data: uN[W]) -> (u32, StackResp<W>, StackWrite<W, AW>)
```

## Tests

```dslx-snippet
fn default_resp<W: u32>() -> StackResp<W> {
    StackResp<W> { pop_valid: false, pop_data: uN[W]:0, overflow: false, underflow: false }
}

fn default_write<W: u32, AW: u32>() -> StackWrite<W, AW> {
    StackWrite<W, AW> { we: false, addr: uN[AW]:0, data: uN[W]:0 }
}

fn apply_write<W: u32, DEPTH: u32, AW: u32>(mem: uN[W][DEPTH], wr: StackWrite<W, AW>) -> uN[W][DEPTH] {
    if wr.we {
        update(mem, wr.addr as u32, wr.data)
    } else {
        mem
    }
}

#[test]
fn test_stack_step_selected_sequence() {
    type Word = u8;
    const DEPTH = u32:4;
    const AW = std::clog2(DEPTH);

    let mem0 = Word[DEPTH]:[0, 0, 0, 0];
    let count0 = u32:0;

    let (count1, resp1, wr1) = stack_step<DEPTH, u32:8, AW>(mem0, count0, StackOp::PUSH, Word:11);
    assert_eq(count1, u32:1);
    assert_eq(resp1, default_resp<u32:8>());
    assert_eq(wr1, StackWrite<u32:8, AW> { we: true, addr: uN[AW]:0, data: Word:11 });
    let mem1 = apply_write<u32:8, DEPTH, AW>(mem0, wr1);

    let (count2, resp2, wr2) = stack_step<DEPTH, u32:8, AW>(mem1, count1, StackOp::PUSH, Word:22);
    assert_eq(count2, u32:2);
    assert_eq(resp2, default_resp<u32:8>());
    assert_eq(wr2, StackWrite<u32:8, AW> { we: true, addr: uN[AW]:1, data: Word:22 });
    let mem2 = apply_write<u32:8, DEPTH, AW>(mem1, wr2);

    let (count3, resp3, wr3) = stack_step<DEPTH, u32:8, AW>(mem2, count2, StackOp::POP, Word:0);
    assert_eq(count3, u32:1);
    assert_eq(resp3, StackResp<u32:8> { pop_valid: true, pop_data: Word:22, overflow: false, underflow: false });
    assert_eq(wr3, default_write<u32:8, AW>());

    let (count4, resp4, wr4) = stack_step<DEPTH, u32:8, AW>(mem2, count3, StackOp::POP, Word:0);
    assert_eq(count4, u32:0);
    assert_eq(resp4, StackResp<u32:8> { pop_valid: true, pop_data: Word:11, overflow: false, underflow: false });
    assert_eq(wr4, default_write<u32:8, AW>());

    let (count5, resp5, wr5) = stack_step<DEPTH, u32:8, AW>(mem2, count4, StackOp::POP, Word:0);
    assert_eq(count5, u32:0);
    assert_eq(resp5, StackResp<u32:8> { pop_valid: false, pop_data: Word:0, overflow: false, underflow: true });
    assert_eq(wr5, default_write<u32:8, AW>());
}

#[test]
fn test_stack_step_overflow() {
    type Word = u8;
    const DEPTH = u32:4;
    const AW = std::clog2(DEPTH);

    let mem = Word[DEPTH]:[1, 2, 3, 4];
    let count = u32:4;
    let (next_count, resp, wr) = stack_step<DEPTH, u32:8, AW>(mem, count, StackOp::PUSH, Word:99);

    assert_eq(next_count, count);
    assert_eq(resp, StackResp<u32:8> { pop_valid: false, pop_data: Word:0, overflow: true, underflow: false });
    assert_eq(wr, default_write<u32:8, AW>());
}
```
