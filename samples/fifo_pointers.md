# FIFO Pointers

## Prompt

Implement one step of FIFO pointer and occupancy-count update logic.

This sample models only the read pointer, write pointer, and occupancy count;
it does not model the FIFO storage array. The input state is assumed valid:
`count <= DEPTH`, and both pointers are in the range `0..DEPTH-1`. Assume
`DEPTH > 1`.

Semantics:

- `push` requests writing one element.
- `pop` requests reading one element.
- A push is accepted when the FIFO is not full, or when the FIFO is full and a
  pop is accepted in the same cycle.
- A pop is accepted when the FIFO is not empty.
- A push and pop may both be accepted in the same cycle.
- Accepted pushes advance the write pointer; accepted pops advance the read
  pointer.
- Pointer advancement wraps from `DEPTH - 1` back to zero.
- `next_full` and `next_empty` describe the next state after the step.

The prologue will be automatically included, just implement the signature in
the output answer.

## Prologue

```dslx
struct FifoPtrState<AW: u32, CW: u32> {
    rd: uN[AW],
    wr: uN[AW],
    count: uN[CW],
}

struct FifoPtrStep<AW: u32, CW: u32> {
    next_state: FifoPtrState<AW, CW>,
    push_accepted: bool,
    pop_accepted: bool,
    next_full: bool,
    next_empty: bool,
}
```

## Signature

```dslx-snippet
fn fifo_pointers<DEPTH: u32, AW: u32 = {std::clog2(DEPTH)}, CW: u32 = {std::clog2(DEPTH + u32:1)}>(state: FifoPtrState<AW, CW>, push: bool, pop: bool) -> FifoPtrStep<AW, CW>
```

## Tests

```dslx-snippet
#[test]
fn test_empty_pop_is_ignored() {
    let state = FifoPtrState<u32:2, u32:3> { rd: u2:0, wr: u2:0, count: u3:0 };
    let got = fifo_pointers<u32:4>(state, false, true);
    assert_eq(got, FifoPtrStep<u32:2, u32:3> {
        next_state: state,
        push_accepted: false,
        pop_accepted: false,
        next_full: false,
        next_empty: true,
    });
}

#[test]
fn test_push_into_empty() {
    let state = FifoPtrState<u32:2, u32:3> { rd: u2:0, wr: u2:0, count: u3:0 };
    let got = fifo_pointers<u32:4>(state, true, false);
    assert_eq(got, FifoPtrStep<u32:2, u32:3> {
        next_state: FifoPtrState<u32:2, u32:3> { rd: u2:0, wr: u2:1, count: u3:1 },
        push_accepted: true,
        pop_accepted: false,
        next_full: false,
        next_empty: false,
    });
}

#[test]
fn test_middle_push_pop_advances_both_and_count_stays() {
    let state = FifoPtrState<u32:2, u32:3> { rd: u2:1, wr: u2:3, count: u3:2 };
    let got = fifo_pointers<u32:4>(state, true, true);
    assert_eq(got, FifoPtrStep<u32:2, u32:3> {
        next_state: FifoPtrState<u32:2, u32:3> { rd: u2:2, wr: u2:0, count: u3:2 },
        push_accepted: true,
        pop_accepted: true,
        next_full: false,
        next_empty: false,
    });
}

#[test]
fn test_full_push_only_is_ignored_but_push_pop_is_allowed() {
    let state = FifoPtrState<u32:2, u32:3> { rd: u2:1, wr: u2:1, count: u3:4 };
    let push_only = fifo_pointers<u32:4>(state, true, false);
    assert_eq(push_only, FifoPtrStep<u32:2, u32:3> {
        next_state: state,
        push_accepted: false,
        pop_accepted: false,
        next_full: true,
        next_empty: false,
    });

    let push_pop = fifo_pointers<u32:4>(state, true, true);
    assert_eq(push_pop, FifoPtrStep<u32:2, u32:3> {
        next_state: FifoPtrState<u32:2, u32:3> { rd: u2:2, wr: u2:2, count: u3:4 },
        push_accepted: true,
        pop_accepted: true,
        next_full: true,
        next_empty: false,
    });
}

#[test]
fn test_non_power_of_two_depth_wraps_at_depth_minus_one() {
    let state = FifoPtrState<u32:3, u32:3> { rd: u3:4, wr: u3:4, count: u3:4 };
    let got = fifo_pointers<u32:5>(state, true, true);
    assert_eq(got, FifoPtrStep<u32:3, u32:3> {
        next_state: FifoPtrState<u32:3, u32:3> { rd: u3:0, wr: u3:0, count: u3:4 },
        push_accepted: true,
        pop_accepted: true,
        next_full: false,
        next_empty: false,
    });
}

#[quickcheck(exhaustive)]
fn prop_depth4_count_stays_in_range(rd: u2, wr: u2, count: u3, push: bool, pop: bool) -> bool {
    if count <= u3:4 {
        let state = FifoPtrState<u32:2, u32:3> { rd, wr, count };
        fifo_pointers<u32:4>(state, push, pop).next_state.count <= u3:4
    } else {
        true
    }
}

#[quickcheck(exhaustive)]
fn prop_empty_never_accepts_pop(rd: u2, wr: u2, push: bool) -> bool {
    let state = FifoPtrState<u32:2, u32:3> { rd, wr, count: u3:0 };
    !fifo_pointers<u32:4>(state, push, true).pop_accepted
}

#[quickcheck(exhaustive)]
fn prop_full_accepts_push_only_with_pop(rd: u2, push: bool, pop: bool) -> bool {
    let state = FifoPtrState<u32:2, u32:3> { rd, wr: rd, count: u3:4 };
    let got = fifo_pointers<u32:4>(state, push, pop);
    got.push_accepted == (push && pop)
}
```
