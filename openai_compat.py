# SPDX-License-Identifier: Apache-2.0
"""Compatibility helpers for OpenAI-style text generation APIs.

This module exists to isolate API-shape differences between the legacy Chat
Completions interface and newer OpenAI-compatible Responses-style interfaces.
The goal is to keep provider code small and explicit when we need to support
multiple request/response schemas for the same eval harness.

The intended mental model is:

- Normalize transport and schema differences here.
- Keep model-behavior policy out of this module.
- Do not use this layer to "fix" model output or mask instruction-following
  failures; those should remain visible in eval results.

In practice that means this module is the right place for tasks such as:

- deciding whether a model supports a reasoning-effort parameter,
- building a Responses API request payload from harness inputs,
- extracting plain text from different response object layouts,
- translating usage accounting fields into one common token-total tuple.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Any, Optional


REASONING_EFFORT_CHOICES = ['none', 'low', 'medium', 'high', 'xhigh']
_REASONING_MODEL_RE = re.compile(r'^(gpt-5(?:$|[-.])|o[1-9](?:$|[-.]))')


@dataclasses.dataclass(frozen=True)
class UsageTotals:
    """Normalized token accounting for one model response."""

    input: int
    cached: int
    output: int
    total: int


def _get_field(value: Any, name: str, default: Any = None) -> Any:
    """Reads a field from either a dict-backed or attribute-backed object.

    OpenAI-compatible SDKs and transport wrappers are not consistent about
    whether response objects are plain dictionaries or typed objects. This
    helper lets the rest of the module read fields without caring which form
    was returned.
    """
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def supports_reasoning_effort(model: str) -> bool:
    """Returns whether the model name appears to support reasoning effort.

    This is a conservative name-based check used to decide whether it is valid
    to attach a reasoning-effort setting to a request. It is intentionally a
    lightweight heuristic rather than a capability probe.
    """
    return bool(_REASONING_MODEL_RE.match(model.lower()))


def resolve_reasoning_effort(model: str, reasoning_effort: Optional[str]) -> Optional[str]:
    """Normalizes the requested reasoning-effort setting for one model.

    `none` is treated as an explicit request to omit the field entirely. When
    the caller does not specify a value, reasoning-capable models default to
    `high` so the harness preserves its current behavior.
    """
    if reasoning_effort == 'none':
        return None
    if reasoning_effort is not None:
        return reasoning_effort
    if supports_reasoning_effort(model):
        return 'high'
    return None


def build_responses_request(
    *,
    model: str,
    instructions: Optional[str],
    messages: list[dict[str, str]],
    reasoning_effort: Optional[str],
) -> dict[str, Any]:
    """Builds a Responses API request payload from harness conversation state.

    The harness represents conversations as a list of role/content messages.
    This helper converts that state into the request shape expected by the
    Responses API and attaches optional instructions and reasoning config when
    appropriate.
    """
    kwargs: dict[str, Any] = {
        'model': model,
        'input': messages,
        'store': False,
    }
    if instructions is not None:
        kwargs['instructions'] = instructions
    effective_reasoning_effort = resolve_reasoning_effort(model, reasoning_effort)
    if effective_reasoning_effort is not None:
        kwargs['reasoning'] = {'effort': effective_reasoning_effort}
    return kwargs


def create_response(client: Any, **kwargs: Any) -> Any:
    """Invokes `client.responses.create` with a clearer failure mode.

    Some environments still have an older `openai` package installed that only
    supports Chat Completions. Raising here makes the dependency problem
    obvious instead of failing later with a less specific attribute error.
    """
    responses_api = getattr(client, 'responses', None)
    if responses_api is None:
        raise RuntimeError(
            'The installed "openai" Python package does not support the Responses API. '
            'Upgrade dependencies (for example, `pip install -r requirements.txt`) and retry.'
        )
    return responses_api.create(**kwargs)


def extract_output_text(response: Any) -> str:
    """Extracts assistant text from a Responses API result object.

    The SDK may expose a convenience `output_text` field, but some compatible
    implementations only populate the structured `output[].content[]` form.
    This helper accepts either layout and returns one stripped text string.
    """
    output_text = getattr(response, 'output_text', None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: list[str] = []
    for item in getattr(response, 'output', []) or []:
        if _get_field(item, 'type') != 'message':
            continue
        for content in _get_field(item, 'content', []) or []:
            text = _get_field(content, 'text')
            if isinstance(text, str):
                chunks.append(text)

    if chunks:
        return ''.join(chunks).strip()

    raise RuntimeError('Responses API returned no text output.')


def usage_to_totals(usage: Any) -> UsageTotals | None:
    """Normalizes usage objects into a `UsageTotals` record.

    OpenAI-compatible APIs do not all report token accounting with the same
    field names. This helper accepts either Responses-style usage
    (`input_tokens`, `output_tokens`) or Chat Completions-style usage
    (`prompt_tokens`, `completion_tokens`) and translates both into a single
    named record used by the harness.
    """
    if usage is None:
        return None

    input_tokens = _get_field(usage, 'input_tokens')
    if input_tokens is not None:
        details = _get_field(usage, 'input_tokens_details')
        cached_tokens = _get_field(details, 'cached_tokens', 0) or 0
        output_tokens = _get_field(usage, 'output_tokens', 0) or 0
        total_tokens = _get_field(usage, 'total_tokens', input_tokens + output_tokens) or 0
        return UsageTotals(
            input=input_tokens - cached_tokens,
            cached=cached_tokens,
            output=output_tokens,
            total=total_tokens,
        )

    prompt_tokens = _get_field(usage, 'prompt_tokens')
    if prompt_tokens is not None:
        details = _get_field(usage, 'prompt_tokens_details')
        cached_tokens = _get_field(details, 'cached_tokens', 0) or 0
        output_tokens = _get_field(usage, 'completion_tokens', 0) or 0
        total_tokens = _get_field(usage, 'total_tokens', prompt_tokens + output_tokens) or 0
        return UsageTotals(
            input=prompt_tokens - cached_tokens,
            cached=cached_tokens,
            output=output_tokens,
            total=total_tokens,
        )

    return None
