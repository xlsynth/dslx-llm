# Dual-Port Doubly Linked List Step

## Prompt

Implement one cycle of doubly linked list control over a node array memory.

This models a dual-ported memory system:

- your function returns up to two node-write intents per cycle;
- each write intent can update one node entry.

Supported operations:

- `NOOP`: no list change, no writes.
- `PUSH_FRONT`: insert node `idx` at the front of the list.
  - If list was empty: head and tail both become `idx`; write only the new node.
  - If list was non-empty: head becomes `idx`, old head's `prev` becomes `idx`; this uses two writes.
- `REMOVE`: remove node `idx` from the list.
  - Update neighboring nodes to bypass `idx` (up to two writes).
  - Update head/tail as needed.
  - You do not need to clear the removed node's own fields.

Assumptions:

- For `PUSH_FRONT`, `idx` refers to a detached node.
- For `REMOVE`, `idx` refers to a node currently in the list.

Dual-port contract:

- At most two memory writes may be requested per cycle.

The prologue will be automatically included, so implement only the functions listed in the signature section.

## Requirements

The following requirements will be checked by a separate critic model. The critic should treat comments as claims, not proof, and decide from the actual DSLX structure.

- id: at_most_two_writes_per_cycle
  requirement: The implementation must request at most two node writes per operation and use the two returned write ports as the only mechanism for node updates.

- id: no_full_array_rebuild
  requirement: The implementation must not rebuild, map, or iterate over the full node array to emulate link updates. It should compute only the specific neighbor updates required by the operation.

- id: remove_relinks_neighbors
  requirement: The `REMOVE` operation must relink neighbors around `idx` via direct updates to predecessor/successor nodes (where present), and update head/tail accordingly.

## Prologue

```dslx
enum DllOp : u2 {
    NOOP = 0,
    PUSH_FRONT = 1,
    REMOVE = 2,
}

struct DllNode<AW: u32> {
    prev_valid: bool,
    prev: uN[AW],
    next_valid: bool,
    next: uN[AW],
}

struct DllState<AW: u32> {
    head_valid: bool,
    head: uN[AW],
    tail_valid: bool,
    tail: uN[AW],
}

struct DllWrite<AW: u32> {
    we: bool,
    addr: uN[AW],
    node: DllNode<AW>,
}
```

## Signature

```dslx-snippet
fn dll_step<DEPTH: u32, AW: u32 = {std::clog2(DEPTH)}>(nodes: DllNode<AW>[DEPTH], state: DllState<AW>, op: DllOp, idx: uN[AW]) -> (DllState<AW>, DllWrite<AW>, DllWrite<AW>)
```

## Tests

```dslx-snippet
fn default_node<AW: u32>() -> DllNode<AW> {
    DllNode<AW> {
        prev_valid: false,
        prev: uN[AW]:0,
        next_valid: false,
        next: uN[AW]:0,
    }
}

fn default_write<AW: u32>() -> DllWrite<AW> {
    DllWrite<AW> {
        we: false,
        addr: uN[AW]:0,
        node: default_node<AW>(),
    }
}

fn apply_write<AW: u32, DEPTH: u32>(nodes: DllNode<AW>[DEPTH], wr: DllWrite<AW>) -> DllNode<AW>[DEPTH] {
    if wr.we {
        update(nodes, wr.addr as u32, wr.node)
    } else {
        nodes
    }
}

#[test]
fn test_push_front_into_empty() {
    const DEPTH = u32:4;
    const AW = std::clog2(DEPTH);
    let nodes0 = DllNode<AW>[DEPTH]:[
        default_node<AW>(),
        default_node<AW>(),
        default_node<AW>(),
        default_node<AW>(),
    ];
    let state0 = DllState<AW> { head_valid: false, head: uN[AW]:0, tail_valid: false, tail: uN[AW]:0 };

    let (state1, wr_a, wr_b) = dll_step<DEPTH, AW>(nodes0, state0, DllOp::PUSH_FRONT, uN[AW]:2);
    assert_eq(state1, DllState<AW> { head_valid: true, head: uN[AW]:2, tail_valid: true, tail: uN[AW]:2 });
    assert_eq(wr_a.we, true);
    assert_eq(wr_a.addr, uN[AW]:2);
    assert_eq(wr_a.node, DllNode<AW> { prev_valid: false, prev: uN[AW]:0, next_valid: false, next: uN[AW]:0 });
    assert_eq(wr_b, default_write<AW>());
}

#[test]
fn test_push_front_then_remove_middle_node() {
    const DEPTH = u32:4;
    const AW = std::clog2(DEPTH);

    // Initial list: 0 <-> 1 <-> 2, head=0 tail=2.
    let node0 = DllNode<AW> { prev_valid: false, prev: uN[AW]:0, next_valid: true, next: uN[AW]:1 };
    let node1 = DllNode<AW> { prev_valid: true, prev: uN[AW]:0, next_valid: true, next: uN[AW]:2 };
    let node2 = DllNode<AW> { prev_valid: true, prev: uN[AW]:1, next_valid: false, next: uN[AW]:0 };
    let node3 = default_node<AW>();
    let nodes0 = DllNode<AW>[DEPTH]:[node0, node1, node2, node3];
    let state0 = DllState<AW> { head_valid: true, head: uN[AW]:0, tail_valid: true, tail: uN[AW]:2 };

    // Push node 3 to front: expect two writes (new node 3 and old head 0).
    let (state1, wr0_a, wr0_b) = dll_step<DEPTH, AW>(nodes0, state0, DllOp::PUSH_FRONT, uN[AW]:3);
    assert_eq(state1, DllState<AW> { head_valid: true, head: uN[AW]:3, tail_valid: true, tail: uN[AW]:2 });
    let nodes1 = apply_write<AW, DEPTH>(apply_write<AW, DEPTH>(nodes0, wr0_a), wr0_b);

    assert_eq(nodes1[u32:3], DllNode<AW> { prev_valid: false, prev: uN[AW]:0, next_valid: true, next: uN[AW]:0 });
    assert_eq(nodes1[u32:0], DllNode<AW> { prev_valid: true, prev: uN[AW]:3, next_valid: true, next: uN[AW]:1 });

    // Remove node 1 from 3 <-> 0 <-> 1 <-> 2: neighbors 0 and 2 must relink.
    let (state2, wr1_a, wr1_b) = dll_step<DEPTH, AW>(nodes1, state1, DllOp::REMOVE, uN[AW]:1);
    assert_eq(state2, DllState<AW> { head_valid: true, head: uN[AW]:3, tail_valid: true, tail: uN[AW]:2 });
    let nodes2 = apply_write<AW, DEPTH>(apply_write<AW, DEPTH>(nodes1, wr1_a), wr1_b);

    assert_eq(nodes2[u32:0], DllNode<AW> { prev_valid: true, prev: uN[AW]:3, next_valid: true, next: uN[AW]:2 });
    assert_eq(nodes2[u32:2], DllNode<AW> { prev_valid: true, prev: uN[AW]:0, next_valid: false, next: uN[AW]:0 });
}

#[test]
fn test_remove_head_singleton_to_empty() {
    const DEPTH = u32:2;
    const AW = std::clog2(DEPTH);

    let node0 = DllNode<AW> { prev_valid: false, prev: uN[AW]:0, next_valid: false, next: uN[AW]:0 };
    let node1 = default_node<AW>();
    let nodes = DllNode<AW>[DEPTH]:[node0, node1];
    let state = DllState<AW> { head_valid: true, head: uN[AW]:0, tail_valid: true, tail: uN[AW]:0 };

    let (next_state, wr_a, wr_b) = dll_step<DEPTH, AW>(nodes, state, DllOp::REMOVE, uN[AW]:0);
    assert_eq(next_state, DllState<AW> { head_valid: false, head: uN[AW]:0, tail_valid: false, tail: uN[AW]:0 });
    assert_eq(wr_a, default_write<AW>());
    assert_eq(wr_b, default_write<AW>());
}
```
