# SPDX-License-Identifier: Apache-2.0

def strip_fences(text: str) -> str:
    """Return content inside the outermost triple-backtick fence.

    Strict version: if an opening fence is present it *must* have a corresponding
    closing fence at the same indentation level. Otherwise we raise a ValueError.
    """
    text = text.strip()

    if not text.startswith("```"):
        return text  # Unfenced – treat as literal.

    lines = text.splitlines()

    # Look for a matching closing fence from the end to capture the outermost.
    try:
        closing_index = len(lines) - 1 - lines[::-1].index("```")
    except ValueError:
        raise ValueError("Missing closing ``` fence in code block.")

    if closing_index == 0:
        raise ValueError("Code block consists solely of an opening ``` fence.")

    return "\n".join(lines[1:closing_index])
