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
