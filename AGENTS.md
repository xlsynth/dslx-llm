# Agent Guidance

## Repository Purpose

This is a public, reusable collection of samples for evaluators assessing how
well models write DSLX. Keep contributions useful across models, evaluators, and
environments. Do not add user-specific experiment logs, machine names or local
paths, account details, or model-trial artifacts to sample documentation.

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

## Contract-Style Sample Prompts

When writing sample prompts, describe the required behavior as a contract
rather than as pseudocode for an implementation.

- Define observable semantics: valid inputs, output values, tie-breaking rules,
  ordering conventions, and state transitions.
- For priority or arbitration logic, prefer contract terms like "highest cyclic
  priority relative to pointer" over step-by-step loop descriptions.
- Keep architectural requirements precise when they matter to the sample, but
  frame them as properties the implementation must satisfy rather than a recipe
  for how to compute them.
- Use examples and tests to remove ambiguity instead of embedding a full
  algorithm in prose.

## Test Quality and Answer Leakage

Tests should distinguish correct solutions from plausible mistakes without
publishing the target DSLX solution. Being absent from the initial prompt is not
enough: public files, documentation, fixtures, and commit history can enter
training data. Review the whole change for answer leakage before publishing.

- Prefer DSLX acceptance tests: representative edge cases, invariants, metamorphic
  relations, and postcondition checks. A predicate that checks a proposed result
  can be more appropriate than a helper that constructs the answer.
- Test boundary behavior, invalid assumptions, and operation ordering; avoid
  relying only on weak properties that many incorrect programs satisfy. Use
  reduced-width exhaustiveness where feasible and mutation checks to establish
  that plausible wrong implementations fail for semantic reasons.
- Python is appropriate for involved validation. An independently checked Python
  reference is more acceptable than a complete target-language implementation:
  it validates semantics without publishing the exact DSLX answer. Keep it out
  of model input and prefer independent formulations to merely translating the
  candidate algorithm.
- Do not commit complete target DSLX implementations, including in fixtures,
  documentation, or mutation-test scaffolding. Keep such development aids outside
  the public repository. Renaming a reference helper does not prevent leakage.
- Avoid exhaustive answer tables when focused examples or property checks provide
  equivalent coverage. Do not weaken correctness checks just to hide answers;
  document unavoidable coverage/disclosure tradeoffs concisely.
- Check the actual prompt assembly path. The function evaluator initially sends
  prompt, signature, and prologue; acceptance tests execute locally, and repair
  feedback can reveal failing test details. Other evaluation paths may differ.
