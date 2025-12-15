# SPDX-License-Identifier: Apache-2.0

import re
import shlex

_DSLX_RUN_FLAGS_RE = re.compile(r"^\s*//\s*dslx_run_(?:flags|options):\s*(.*)\s*$")


def extract_dslx_run_flags(text: str) -> list[str]:
    """Extracts interpreter flags from directive comment lines.

    Supported directives:
      // dslx_run_flags: --warnings_as_errors=false
      // dslx_run_options: --warnings_as_errors=false
    """
    flags: list[str] = []
    for line in text.splitlines():
        m = _DSLX_RUN_FLAGS_RE.match(line)
        if not m:
            continue
        extra = m.group(1).strip()
        if not extra:
            continue
        for tok in shlex.split(extra):
            assert tok.startswith('--'), f'dslx_run_* directive token must start with "--": {tok!r}'
            flags.append(tok)

    # Deduplicate while preserving order.
    seen = set()
    deduped: list[str] = []
    for f in flags:
        if f in seen:
            continue
        seen.add(f)
        deduped.append(f)
    return deduped


def split_dslx_run_flags_from_code(code: str) -> tuple[str, tuple[str, ...]]:
    """Removes directive lines and returns (cleaned_code, flags).

    This is useful for tools that accept flags out-of-band rather than in-file.
    """
    flags: list[str] = []
    kept_lines: list[str] = []
    for line in code.splitlines():
        m = _DSLX_RUN_FLAGS_RE.match(line)
        if m:
            flags.extend(shlex.split(m.group(1)))
            continue
        kept_lines.append(line)
    cleaned = "\n".join(kept_lines) + ("\n" if code.endswith("\n") else "")
    return cleaned, tuple(flags)


