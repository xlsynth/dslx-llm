# Round-Robin Arbiter

## Prompt

Implement one step of a ready/valid-aware round-robin arbiter.

The state is a pointer to the first requestor that should be considered for
priority in the current cycle. Requestor indices use LSB-zero bit numbering.
Assume `N > 1` and `pointer < N`.

Semantics:

- Grant at most one requestor.
- Starting at `pointer`, scan requestors in increasing index order, wrapping
  from `N - 1` back to zero, and grant the first requested index found.
- If no request bit is set, return a zero grant and leave the pointer
  unchanged.
- A nonzero grant is accepted only when `grant_ready` is true.
- If a grant is accepted, the next pointer is one past the granted index,
  wrapping from `N - 1` back to zero.
- If a grant is not accepted because `grant_ready` is false, return the grant
  but leave the pointer unchanged so the same priority point is retried next
  cycle.

The prologue will be automatically included, just implement the signature in
the output answer.

## Signature

```dslx-snippet
fn round_robin_arbiter<N: u32, INDEX_WIDTH: u32 = {std::clog2(N)}>(requests: bits[N], pointer: uN[INDEX_WIDTH], grant_ready: bool) -> (bits[N], uN[INDEX_WIDTH])
```

## Tests

```dslx-snippet
#[test]
fn test_round_robin_sequence_with_accepts() {
    let (grant0, ptr1) = round_robin_arbiter<u32:4>(u4:0b1010, u2:0, true);
    assert_eq(grant0, u4:0b0010);
    assert_eq(ptr1, u2:2);

    let (grant1, ptr2) = round_robin_arbiter<u32:4>(u4:0b1010, ptr1, true);
    assert_eq(grant1, u4:0b1000);
    assert_eq(ptr2, u2:0);

    let (grant2, ptr3) = round_robin_arbiter<u32:4>(u4:0b1111, ptr2, true);
    assert_eq(grant2, u4:0b0001);
    assert_eq(ptr3, u2:1);
}

#[test]
fn test_round_robin_stall_holds_pointer() {
    let (grant0, ptr1) = round_robin_arbiter<u32:4>(u4:0b1010, u2:0, false);
    assert_eq(grant0, u4:0b0010);
    assert_eq(ptr1, u2:0);

    let (grant1, ptr2) = round_robin_arbiter<u32:4>(u4:0b1010, ptr1, true);
    assert_eq(grant1, u4:0b0010);
    assert_eq(ptr2, u2:2);
}

#[test]
fn test_round_robin_no_requests_holds_pointer() {
    let (grant, next_ptr) = round_robin_arbiter<u32:4>(u4:0b0000, u2:3, true);
    assert_eq(grant, u4:0b0000);
    assert_eq(next_ptr, u2:3);
}

#[test]
fn test_round_robin_non_power_of_two_width() {
    let (grant0, ptr1) = round_robin_arbiter<u32:5>(u5:0b1_0010, u3:4, true);
    assert_eq(grant0, u5:0b1_0000);
    assert_eq(ptr1, u3:0);

    let (grant1, ptr2) = round_robin_arbiter<u32:5>(u5:0b1_0010, ptr1, true);
    assert_eq(grant1, u5:0b0_0010);
    assert_eq(ptr2, u3:2);
}

#[quickcheck(exhaustive)]
fn prop_u4_grant_is_zero_or_onehot(requests: u4, pointer: u2, grant_ready: bool) -> bool {
    let (grant, _) = round_robin_arbiter<u32:4>(requests, pointer, grant_ready);
    std::popcount(grant) <= u4:1
}

#[quickcheck(exhaustive)]
fn prop_u4_grant_is_requested(requests: u4, pointer: u2, grant_ready: bool) -> bool {
    let (grant, _) = round_robin_arbiter<u32:4>(requests, pointer, grant_ready);
    (grant & !requests) == u4:0
}

#[quickcheck(exhaustive)]
fn prop_u4_no_requests_holds_pointer(pointer: u2, grant_ready: bool) -> bool {
    let (grant, next_ptr) = round_robin_arbiter<u32:4>(u4:0, pointer, grant_ready);
    grant == u4:0 && next_ptr == pointer
}

#[quickcheck(exhaustive)]
fn prop_u4_stalled_grant_holds_pointer(requests: u4, pointer: u2) -> bool {
    let (_, next_ptr) = round_robin_arbiter<u32:4>(requests, pointer, false);
    next_ptr == pointer
}
```
