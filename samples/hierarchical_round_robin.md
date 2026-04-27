# Hierarchical Round-Robin Arbiter

## Prompt

Implement one step of a two-level hierarchical round-robin arbiter.

The request vector is flattened from `GROUPS` groups with `LANES` lanes per
group. LSB-zero bit index `group * LANES + lane` corresponds to that lane in
that group. Assume `GROUPS > 1`, `LANES > 1`, `state.group_ptr < GROUPS`, and
each `state.lane_ptrs[g] < LANES`.

Hierarchical arbitration contract:

- A group is request-active when any lane in that group requests.
- The granted group, when one exists, is the request-active group with highest
  cyclic priority relative to `state.group_ptr`; `state.group_ptr` itself has
  highest priority, followed by increasing group numbers modulo `GROUPS`.
- The granted lane is chosen only among lanes of the granted group. It is the
  requesting lane with highest cyclic priority relative to
  `state.lane_ptrs[group]`, using increasing lane numbers modulo `LANES`.
- The grant is one-hot at flattened bit index `group * LANES + lane`. If no
  group is request-active, the grant is zero.
- State changes only when a nonzero grant is accepted, and acceptance requires
  `grant_ready == true`.
- On an accepted grant, `group_ptr` becomes one past the granted group modulo
  `GROUPS`, and only the granted group's lane pointer becomes one past the
  granted lane modulo `LANES`.
- With no request, or with an unaccepted grant because `grant_ready == false`,
  all state is unchanged.

The prologue will be automatically included, just implement the signature in
the output answer.

## Requirements

The following requirements will be checked by a separate critic model. The
critic should treat comments as claims, not proof, and decide from actual DSLX
structure.

- id: two_level_selection
  requirement: The grant choice must obey the two-level priority contract: group priority determines the granted group, and lane priority applies only within that group, rather than treating all requestors as one flat round-robin ring.

- id: per_group_lane_state
  requirement: Lane priority state must be independent per group, and an accepted grant must change only the lane pointer for the granted group.

## Prologue

```dslx
import std;

struct HierRrState<GROUPS: u32, LANES: u32, GROUP_W: u32 = {std::clog2(GROUPS)}, LANE_W: u32 = {std::clog2(LANES)}> {
    group_ptr: uN[GROUP_W],
    lane_ptrs: uN[LANE_W][GROUPS],
}
```

## Signature

```dslx-snippet
fn hierarchical_round_robin<GROUPS: u32, LANES: u32, FLAT: u32 = {GROUPS * LANES}, GROUP_W: u32 = {std::clog2(GROUPS)}, LANE_W: u32 = {std::clog2(LANES)}>(requests: bits[FLAT], state: HierRrState<GROUPS, LANES, GROUP_W, LANE_W>, grant_ready: bool) -> (bits[FLAT], HierRrState<GROUPS, LANES, GROUP_W, LANE_W>)
```

## Tests

```dslx-snippet
#[test]
fn test_hierarchical_round_robin_group_and_lane_sequence() {
    type State = HierRrState<u32:2, u32:4, u32:1, u32:2>;

    let st0 = State { group_ptr: u1:0, lane_ptrs: u2[2]:[0, 0] };
    let (grant0, st1) = hierarchical_round_robin<u32:2, u32:4>(u8:0b0010_1000, st0, true);
    assert_eq(grant0, u8:0b0000_1000);
    assert_eq(st1, State { group_ptr: u1:1, lane_ptrs: u2[2]:[0, 0] });

    let (grant1, st2) = hierarchical_round_robin<u32:2, u32:4>(u8:0b0010_1000, st1, true);
    assert_eq(grant1, u8:0b0010_0000);
    assert_eq(st2, State { group_ptr: u1:0, lane_ptrs: u2[2]:[0, 2] });
}

#[test]
fn test_hierarchical_round_robin_stall_holds_all_state() {
    type State = HierRrState<u32:2, u32:4, u32:1, u32:2>;

    let st0 = State { group_ptr: u1:1, lane_ptrs: u2[2]:[3, 2] };
    let (grant, st1) = hierarchical_round_robin<u32:2, u32:4>(u8:0b1101_0001, st0, false);
    assert_eq(grant, u8:0b0100_0000);
    assert_eq(st1, st0);
}

#[test]
fn test_hierarchical_round_robin_no_requests_holds_state() {
    type State = HierRrState<u32:2, u32:4, u32:1, u32:2>;

    let st0 = State { group_ptr: u1:1, lane_ptrs: u2[2]:[1, 3] };
    let (grant, st1) = hierarchical_round_robin<u32:2, u32:4>(u8:0, st0, true);
    assert_eq(grant, u8:0);
    assert_eq(st1, st0);
}

#[test]
fn test_hierarchical_round_robin_non_power_of_two_groups_and_lanes() {
    type State = HierRrState<u32:3, u32:3, u32:2, u32:2>;

    let st0 = State { group_ptr: u2:2, lane_ptrs: u2[3]:[0, 1, 2] };
    let (grant0, st1) = hierarchical_round_robin<u32:3, u32:3>(u9:0b1_0000_0010, st0, true);
    assert_eq(grant0, u9:0b1_0000_0000);
    assert_eq(st1, State { group_ptr: u2:0, lane_ptrs: u2[3]:[0, 1, 0] });

    let (grant1, st2) = hierarchical_round_robin<u32:3, u32:3>(u9:0b1_0000_0010, st1, true);
    assert_eq(grant1, u9:0b0_0000_0010);
    assert_eq(st2, State { group_ptr: u2:1, lane_ptrs: u2[3]:[2, 1, 0] });
}

#[quickcheck(exhaustive)]
fn prop_two_by_three_grant_is_zero_or_onehot(requests: u6, group_ptr: u1, lane_ptr0: u2, lane_ptr1: u2, grant_ready: bool) -> bool {
    if lane_ptr0 < u2:3 && lane_ptr1 < u2:3 {
        let state = HierRrState<u32:2, u32:3, u32:1, u32:2> {
            group_ptr,
            lane_ptrs: u2[2]:[lane_ptr0, lane_ptr1],
        };
        let (grant, _) = hierarchical_round_robin<u32:2, u32:3>(requests, state, grant_ready);
        std::popcount(grant) <= u6:1
    } else {
        true
    }
}

#[quickcheck(exhaustive)]
fn prop_two_by_three_grant_is_requested(requests: u6, group_ptr: u1, lane_ptr0: u2, lane_ptr1: u2, grant_ready: bool) -> bool {
    if lane_ptr0 < u2:3 && lane_ptr1 < u2:3 {
        let state = HierRrState<u32:2, u32:3, u32:1, u32:2> {
            group_ptr,
            lane_ptrs: u2[2]:[lane_ptr0, lane_ptr1],
        };
        let (grant, _) = hierarchical_round_robin<u32:2, u32:3>(requests, state, grant_ready);
        (grant & !requests) == u6:0
    } else {
        true
    }
}

#[quickcheck(exhaustive)]
fn prop_two_by_three_stall_holds_state(requests: u6, group_ptr: u1, lane_ptr0: u2, lane_ptr1: u2) -> bool {
    if lane_ptr0 < u2:3 && lane_ptr1 < u2:3 {
        let state = HierRrState<u32:2, u32:3, u32:1, u32:2> {
            group_ptr,
            lane_ptrs: u2[2]:[lane_ptr0, lane_ptr1],
        };
        let (_, next_state) = hierarchical_round_robin<u32:2, u32:3>(requests, state, false);
        next_state == state
    } else {
        true
    }
}
```
