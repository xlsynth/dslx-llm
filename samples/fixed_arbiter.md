# Fixed-Priority Arbiter

## Prompt

Write a fixed-priority arbiter -- this grants a single request at a time with a
fixed which-to-grant policy that is based on the requestor index, the lowest
index requestor is granted first.

Takes a bit vector that indicates which requestors are requesting a grant and
the previous state for the arbiter, and returns a bit vector indicating which
requestor has been granted and the corresponding output state.

## Signature

```dslx-snippet
fn fixed_arbiter<N: u32>(requests: bits[N], state: ArbiterState<N>) -> (bits[N], ArbiterState<N>);
```

## Tests

```dslx
#[test]
fn test_fixed_arbiter() {
  let state = ArbiterState<u32:4>{};
  
  // Test case 1: requestors 1 and 3 are requesting
  let requests = bits[4]:0b1010;
  let (grant, state) = fixed_arbiter(requests, state);
  assert_eq(grant, bits[4]:0b0010);  // requestor 1 should be granted

  // Test case 2: requestors 0 and 2 are requesting
  let requests2 = bits[4]:0b0101;
  let (grant2, state) = fixed_arbiter(requests2, state);
  assert_eq(grant2, bits[4]:0b0001);  // requestor 0 should be granted

  // Test case 3: no requestors are requesting
  let requests3 = bits[4]:0b0000;
  let (grant3, state) = fixed_arbiter(requests3, state);
  assert_eq(grant3, bits[4]:0b0000);  // no grant should be issued
}

/// Returns true iff we gave a grant an index where req was true.
fn granted_at_requested_index<N: u32>(req: bits[N], grant: bits[N]) -> bool {
  let (found, index) = std::find_index(std::convert_to_bools_lsb0(grant), true);
  if found {
    req[index +: bool]
  } else {
    true
  }
}

/// Returns true iff:
/// - the lowest requested index was the granted index, OR
/// - there was no request and concordantly no grant
fn lowest_requested_is_granted<N: u32>(req: bits[N], grant: bits[N]) -> bool {
  let (grant_found, grant_index) = std::find_index(std::convert_to_bools_lsb0(grant), true);
  let (req_found, req_index) = std::find_index(std::convert_to_bools_lsb0(req), true);
  if req_found {
    grant_found && grant_index == req_index
  } else {
    grant_found == false
  }
}

const TEST_N = u32:5;

/// Validates that the output is onehot and that a grant is always performed
/// when there is >= 1 request for arb and it came from a requested index.
#[quickcheck]
fn quickcheck_grant_onehot(requests: bits[TEST_N], state: ArbiterState<TEST_N>) -> bool {
    let want = requests != bits[TEST_N]:0;
    let (granted, _state') = fixed_arbiter(requests, state);
    std::popcount(granted) == (want as bits[TEST_N]) && granted_at_requested_index(requests, granted) && lowest_requested_is_granted(requests, granted)
}
```
