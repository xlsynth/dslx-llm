# Least-Recently Used Arbiter

## Prompt

Write a least-recently-used (LRU) arbiter -- this grants a single request at a time with a
least-recently-used which-to-grant policy that is based on the requestor index. If there are
more than one requestor at a time, the one that was least recently used must get granted.

Takes a bit vector that indicates which requestors are requesting a grant and
the previous state for the arbiter, and returns a bit vector indicating which
requestor has been granted and the corresponding output state.

The prologue will be automatically included, just implement the signature in the output answer.

## Prologue

```dslx
```

## Signature

```dslx-snippet
fn lru_arbiter<N: u32, IndexWidth: u32 = {std::clog2(N)}>(requests: bits[N], state: uN[IndexWidth][N]) -> (bits[N], uN[IndexWidth][N])
```

## Tests

```dslx-snippet
///////////////////////////
///////////////////////////
// TEST HELPER FUNCTIONS //
///////////////////////////
///////////////////////////

/// Returns true iff we gave a grant an index where req was true.
fn granted_at_requested_index<N: u32>(req: bits[N], grant: bits[N]) -> bool {
  let (found, index) = std::find_index(std::convert_to_bools_lsb0(grant), true);
  if found {
    req[index +: bool]
  } else {
    false
  }
}

// Returns true iff:
// - the highest priority requested index was the granted index, OR
// - there was no request and concordantly no grant
fn highest_priority_is_granted<N: u32, IndexWidth: u32 = {std::clog2(N)}>(req: bits[N], ref_priority_order: uN[IndexWidth][N], grant: bits[N]) -> bool {
  type Index = uN[IndexWidth];
  let (grant_found, grant_index) = std::find_index(std::convert_to_bools_lsb0(grant), true);
  let grant_index = grant_index as Index;
  let req = std::convert_to_bools_lsb0(req);
  let (req_found, req_index): (bool, Index) = for (element, (saved_req_found, saved_index)): (Index, (bool, Index)) in ref_priority_order {
    if !saved_req_found && req[element] {
        (true, element)
    } else {
        (saved_req_found, saved_index)
    }
  }((false, Index:0));
  if req_found {
    grant_found && grant_index == req_index
  } else {
    grant_found == false
  }
}

// Returns true iff any state[i] is >= N
fn any_state_out_of_range<N: u32, IndexWidth: u32 = {std::clog2(N)}>(state: uN[IndexWidth][N]) -> bool {
    let result: bool = for (s, r): (uN[IndexWidth], bool) in state {
        let r_next = if s >= N as uN[IndexWidth] {
            true
        } else {
            r
        };
        r_next
    }(false);
    result
}

// Returns true if lookup is in arr except at location except_index.
fn array_contains<N: u32, IndexWidth: u32 = {std::clog2(N)}>(arr: uN[IndexWidth][N], lookup: uN[IndexWidth], except_index: u32) -> bool {
    let contains = for (i, saved_contains): (u32, bool) in u32:0..N {
        saved_contains || ((except_index != i) && (lookup == arr[i]))
    }(false);
    contains
}

// Returns true iff all state[i] are unique.
fn state_unique_indices<N: u32, IndexWidth: u32 = {std::clog2(N)}>(state: uN[IndexWidth][N]) -> bool {
    let outer_unique = for (i, saved_outer_unique): (u32, bool) in u32:0..N {
        let inner_unique = !array_contains(state, state[i], i);
        saved_outer_unique && inner_unique
    }(true);
    outer_unique
}

const TEST_N = u32:5;
const TEST_INDEX_WIDTH = std::clog2(TEST_N);

// Tests the granted_at_requested_index test helper function.
#[quickcheck]
fn quickcheck_helper_granted_at_requested_index(req: bits[TEST_N], grant: bits[TEST_N]) -> bool {

  // Having more than one grant is undefined behavior, so we just return true.
  // TODO(mgottscho): Is there a way to express this constraint in QuickCheck?
  if std::popcount(grant) != uN[TEST_N]:1 {
    true
  } else {
    let actual = granted_at_requested_index(req, grant);
    let expected = ((req & grant) == grant);
    actual == expected
  }
}

// Tests the highest_priority_is_granted test helper function.
#[test]
fn test_helper_highest_priority_is_granted_true() {
    let req = bits[TEST_N]:0b11111;
    let ref_priority_order = uN[TEST_INDEX_WIDTH][TEST_N]:[0, 1, 2, 3, 4];
    let grant = bits[TEST_N]:0b00001;
    assert_eq(highest_priority_is_granted(req, ref_priority_order, grant), true);

    let req = bits[TEST_N]:0b11111;
    let ref_priority_order = uN[TEST_INDEX_WIDTH][TEST_N]:[4, 0, 1, 2, 3];
    let grant = bits[TEST_N]:0b10000;
    assert_eq(highest_priority_is_granted(req, ref_priority_order, grant), true);

    let req = bits[TEST_N]:0b00000;
    let ref_priority_order = uN[TEST_INDEX_WIDTH][TEST_N]:[3, 0, 1, 2, 4];
    let grant = bits[TEST_N]:0b00000;
    assert_eq(highest_priority_is_granted(req, ref_priority_order, grant), true);
}

// Tests the highest_priority_is_granted test helper function.
#[test]
fn test_helper_highest_priority_is_granted_false() {
    let req = bits[TEST_N]:0b00110;
    let ref_priority_order = uN[TEST_INDEX_WIDTH][TEST_N]:[4, 3, 0, 2, 1];
    let grant = bits[TEST_N]:0b00010;
    assert_eq(highest_priority_is_granted(req, ref_priority_order, grant), false);

    let req = bits[TEST_N]:0b10110;
    let ref_priority_order = uN[TEST_INDEX_WIDTH][TEST_N]:[4, 3, 0, 2, 1];
    let grant = bits[TEST_N]:0b00010;
    assert_eq(highest_priority_is_granted(req, ref_priority_order, grant), false);
}

// Tests the array_contains test helper function.
#[test]
fn test_helper_array_contains() {
    type Index = uN[TEST_INDEX_WIDTH];
    let state = uN[TEST_INDEX_WIDTH][TEST_N]:[0, 1, 2, 3, 4];
    assert_eq(array_contains(state, Index:1, u32:0), true);
    assert_eq(array_contains(state, Index:2, u32:1), true);
    assert_eq(array_contains(state, Index:3, u32:2), true);
    assert_eq(array_contains(state, Index:4, u32:3), true);
    assert_eq(array_contains(state, Index:0, u32:4), true);

    let state = uN[TEST_INDEX_WIDTH][TEST_N]:[0, 1, 3, 3, 4];
    assert_eq(array_contains(state, Index:3, u32:2), true);
    assert_eq(array_contains(state, Index:5, u32:0), false);
}

// Tests the state_unique_indices test helper function.
#[test]
fn test_helper_state_unique_indices() {
    let state = uN[TEST_INDEX_WIDTH][TEST_N]:[0, 1, 2, 3, 4];
    assert_eq(state_unique_indices(state), true);

    let state = uN[TEST_INDEX_WIDTH][TEST_N]:[3, 3, 3, 3, 3];
    assert_eq(state_unique_indices(state), false);

    let state = uN[TEST_INDEX_WIDTH][TEST_N]:[0, 1, 2, 2, 3];
    assert_eq(state_unique_indices(state), false);
}

// Tests the any_state_out_of_range test helper function.
#[test]
fn test_helper_any_state_out_of_range() {
    let state = uN[TEST_INDEX_WIDTH][TEST_N]:[0, 1, 2, 3, 4];
    assert_eq(any_state_out_of_range(state), false);

    let state = uN[TEST_INDEX_WIDTH][TEST_N]:[0, 1, 2, 3, 5];
    assert_eq(any_state_out_of_range(state), true);

    let state = uN[TEST_INDEX_WIDTH][TEST_N]:[0, 7, 2, 3, 3];
    assert_eq(any_state_out_of_range(state), true);
}

///////////////////////////
///////////////////////////
//        TESTS          //
///////////////////////////
///////////////////////////

// Tests the lru_arbiter function with 4 requestors on a specific sequence.
#[test]
fn test_lru_arbiter() {
  const TEST_N = u32:4;
  const TEST_INDEX_WIDTH = std::clog2(TEST_N);

  let state = uN[TEST_INDEX_WIDTH][TEST_N]:[0, 1, 2, 3];

  // Test case 1: requestors 1 and 3 are requesting
  let requests1 = bits[TEST_N]:0b1010;
  let (grant1, state) = lru_arbiter(requests1, state);
  assert_eq(grant1, bits[TEST_N]:0b0010);  // requestor 1 should be granted

  // Test case 2: requestors 0 and 2 are requesting
  let requests2 = bits[TEST_N]:0b0101;
  let (grant2, state) = lru_arbiter(requests2, state);
  assert_eq(grant2, bits[TEST_N]:0b0001);  // requestor 0 should be granted

  // Test case 3: requestors 0 and 2 are requesting
  let requests3 = bits[TEST_N]:0b0101;
  let (grant3, state) = lru_arbiter(requests3, state);
  assert_eq(grant3, bits[TEST_N]:0b0100);  // requestor 2 should be granted

  // Test case 4: requestors 0 and 3 are requesting
  let requests4 = bits[TEST_N]:0b1001;
  let (grant4, state) = lru_arbiter(requests4, state);
  assert_eq(grant4, bits[TEST_N]:0b1000);  // requestor 3 should be granted



  // Test case 5: requestors 0, 1, 2, and 3 are requesting
  let requests5 = bits[TEST_N]:0b1111;
  let (grant5, state) = lru_arbiter(requests5, state);
  assert_eq(grant5, bits[TEST_N]:0b0010);  // requestor 1 should be granted

  // Test case 6: requestors 0, 1, 2, and 3 are requesting
  let requests6 = bits[TEST_N]:0b1111;
  let (grant6, state) = lru_arbiter(requests6, state);
  assert_eq(grant6, bits[TEST_N]:0b0001);  // requestor 0 should be granted

  // Test case 7: requestors 0, 1, 2, and 3 are requesting
  let requests7 = bits[TEST_N]:0b1111;
  let (grant7, state) = lru_arbiter(requests7, state);
  assert_eq(grant7, bits[TEST_N]:0b0100);  // requestor 2 should be granted

  // Test case 8: requestors 0, 1, 2, and 3 are requesting
  let requests8 = bits[TEST_N]:0b1111;
  let (grant8, state) = lru_arbiter(requests8, state);
  assert_eq(grant8, bits[TEST_N]:0b1000);  // requestor 3 should be granted


  // Test case 9: no requestors are requesting
  let requests9 = bits[TEST_N]:0b0000;
  let (grant9, _state) = lru_arbiter(requests9, state);
  assert_eq(grant9, bits[TEST_N]:0b0000);  // no grant should be issued
}


// Tests the lru_arbiter function only grants at most one requestor.
#[quickcheck]
fn quickcheck_lru_arbiter_grant_onehot0(requests: bits[TEST_N], state: uN[TEST_INDEX_WIDTH][TEST_N]) -> bool {
    if any_state_out_of_range(state) || !state_unique_indices(state) {
        true
    } else {
        let any_requests: bool = requests != bits[TEST_N]:0;
        let (granted, _) = lru_arbiter(requests, state);
        if any_requests {
            std::popcount(granted) == uN[TEST_N]:1
        } else {
            granted == uN[TEST_N]:0
        }
    }
}

// Tests the lru_arbiter function only grants at a requested index.
#[quickcheck]
fn quickcheck_lru_arbiter_grant_valid_index(requests: bits[TEST_N], state: uN[TEST_INDEX_WIDTH][TEST_N]) -> bool {
    if any_state_out_of_range(state) || !state_unique_indices(state) {
        true
    } else {
        let (granted, _) = lru_arbiter(requests, state);
        granted_at_requested_index<TEST_N>(requests, granted)
    }
}

// Tests the lru_arbiter function only grants the highest priority active requestor.
#[quickcheck]
fn quickcheck_lru_arbiter_grant_highest_priority(requests: bits[TEST_N], state: uN[TEST_INDEX_WIDTH][TEST_N]) -> bool {
    if any_state_out_of_range(state) || !state_unique_indices(state) {
        true
    } else {
        let (granted, _) = lru_arbiter(requests, state);
        highest_priority_is_granted<TEST_N>(requests, state, granted)
    }
}

```
