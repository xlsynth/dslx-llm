# Agent Guidance

## Sample Signature Patterns

When creating new samples, make the intended temporal interface explicit in the signature and prompt.

- If full inputs are provided every cycle, use a per-step API where each call takes the full inputs directly.
- If computation is stateful across cycles and inputs are only provided once, prefer an explicit staged API shape like:
  - `my_thing_init(Input) -> State`
  - `my_thing_step(State) -> State`
  - `my_thing_result(State) -> Output`
- In prompts, explicitly say which model applies (full-input-per-step or init/step/result) to avoid ambiguity.

## Quickcheck Scope Guidance

- Use `#[quickcheck(exhaustive)]` only for small, bounded domains.
- Exhaustive over about 16 bits of total input space is generally fine.
- Do not use exhaustive quickcheck for very large spaces (for example 32-bit or 64-bit cartesian input domains), as runs can be killed for resource use.
- For large domains, use regular randomized `#[quickcheck]` and keep a few focused deterministic tests for key edge cases.

## Reference Implementation Contamination

Acceptance tests are included in the prompt context during evaluation, so test
helpers can accidentally teach the model how to solve the sample.

- Prefer explicit expected-value tables, small exhaustive truth tables, and
  invariant-style quickchecks over generic golden/reference implementations.
- Avoid adding a parametric `golden_reference` helper that solves the same
  problem as the requested function; that can make the sample measure copying
  from the tests instead of problem solving.
- A small fixed-width naive helper or table is acceptable when the intended
  difficulty is the arbitrary-width/parametric implementation, not the small
  instance itself.
- If a reference-like helper is necessary, keep it narrowly scoped to the test
  case and avoid naming it `golden`, `reference`, or similar unless it is
  intentionally part of the task design.
