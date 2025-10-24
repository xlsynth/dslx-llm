# SPDX-License-Identifier: Apache-2.0

import dataclasses


@dataclasses.dataclass
class CriticResult:
    ok: bool
    confidence: float
    message: str
    raw_json: str


CRITIC_SYSTEM_PROMPT = """You are a strict requirements checker for DSLX code solutions.

You will be given:
- A problem prompt (English)
- A function signature (DSLX)
- A list of requirements (English)
- A short DSLX language reference excerpt
- A candidate DSLX implementation

Your job is to decide whether the implementation meets the requirements. You must:
- Treat comments as claims, not proof.
- Decide based on the actual code structure.
- If you cannot find concrete evidence that a requirement is satisfied, mark it as NOT satisfied.

Important: The graph of operations matters, not merely whether a `for` loop iterates over all indices.
For example, visiting every `i` is not evidence of a dense prefix network if most iterations simply copy
state or if the data dependencies do not match the required structure. When the requirements are about
algorithm structure (e.g. a Kogge-Stone prefix network), focus on:
- What values are combined (data dependencies), not just which indices are iterated over.
- Whether each stage recomputes prefix signals from the prior stage (stage-to-stage dependency), vs. a
  sequential in-stage dependence that is effectively ripple-like.
- Whether conditionals skip the combine operator for most indices, which can make the structure sparse.

Return ONLY valid JSON with this schema:
{
  "pass": true|false,
  "confidence": 0.0..1.0,
  "message": "If pass=false: short, actionable reason(s). If pass=true: short confirmation.",
  "per_requirement": [
    {"id": "string", "pass": true|false, "evidence": ["string", ...], "message": "string"}
  ]
}
"""


def load_dslx_critic_reference(prompt_md_path: str) -> str:
    """Loads a small DSLX language reference excerpt to help the critic model."""
    with open(prompt_md_path, "r") as f:
        content = f.read()

    # Include the key semantics that affect "graph of operations":
    # - immutable arrays and `update`
    # - `for` loops as accumulator-evolving expressions
    # Provide a stable excerpt to keep token usage bounded.
    intro = content.splitlines()[:80]
    intro_text = "\n".join(intro).strip()

    def slice_between(start_marker: str, end_marker: str) -> str:
        try:
            start = content.index(start_marker)
            end = content.index(end_marker, start)
        except ValueError:
            return ""
        return content[start:end].strip()

    immutable_updates = slice_between(
        "**Immutable Array Updates**",
        "**No Mutation, Even In Control Flow Blocks**",
    )
    for_loops = slice_between("**For Loops**", "**No While Loops**")

    parts = [
        "DSLX language reference (excerpt):",
        intro_text,
    ]
    if immutable_updates:
        parts.append(immutable_updates)
    if for_loops:
        parts.append(for_loops)
    return "\n\n".join(parts).strip()
