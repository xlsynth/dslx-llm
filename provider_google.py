# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from typing import Optional, Any, cast

try:
    from google import genai
    from google.genai import types
except ModuleNotFoundError:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]

import termcolor

from dslx_text import strip_fences
import critic
from openai_compat import REASONING_EFFORT_CHOICES


SUPPORTED_REASONING_MODELS = {
    'gemini-3-flash-preview',
    'gemini-3.1-flash-lite-preview',
    'gemini-3.1-pro-preview',
}
MODEL_CHOICES = [
    'gemini-3-flash-preview',
    'gemini-3.1-flash-lite-preview',
    'gemini-3.1-pro-preview',
]
TOTAL_USAGE = {
    'input': 0,
    'cached': 0,
    'output': 0,
}


def print_usage(usage: Any | None) -> None:
    if usage is None:
        return

    TOTAL_USAGE['cached'] += usage.cached_content_token_count or 0
    TOTAL_USAGE['input'] += usage.prompt_token_count
    TOTAL_USAGE['output'] += usage.candidates_token_count
    termcolor.cprint(
        f'Used tokens - in {usage.prompt_token_count} (cached {usage.cached_content_token_count})'
        f' - out {usage.candidates_token_count} - total {usage.total_token_count}',
        color='red',
    )


def supports_reasoning_effort(model: str) -> bool:
    return model in SUPPORTED_REASONING_MODELS


def get_reasoning_effort_choices(model: str) -> tuple[str, ...] | None:
    if model in SUPPORTED_REASONING_MODELS:
        return tuple(level for level in REASONING_EFFORT_CHOICES if level in ('low', 'medium', 'high'))
    return None


def _chat_kwargs(model: str, reasoning_effort: Optional[str], messages):
    if reasoning_effort is not None:
        if types is None:
            raise RuntimeError(
                'The "google-genai" Python package is required to use Google '
                'reasoning models. Install it (e.g. `pip install -r '
                'requirements.txt`) and retry.'
            )
        google_types = types
        return {
            'model': model,
            'contents': [google_types.Content(
                role=m['role'],
                parts=[google_types.Part.from_text(text=m['content'])]
            ) for m in messages],
            'config': google_types.GenerateContentConfig(
                thinking_config=google_types.ThinkingConfig(
                    thinking_level=cast(Any, reasoning_effort)
                )
            ),
        }
    return {'model': model, 'contents': messages}


def _parse_critic_json(text: str) -> dict:
    # Allow the critic to wrap the JSON in a triple-backtick block.
    raw = strip_fences(text).strip()
    return json.loads(raw)


def _response_text(response: Any) -> str:
    return (response.text or '').strip()


class CodeGenerator:
    def __init__(
        self,
        model: str,
        reasoning_effort: Optional[str],
        system_prompt: str,
        timeout: int | float | None = None,
    ):
        if genai is None or types is None:
            raise RuntimeError(
                'The "google-genai" Python package is required to use the '
                'Google provider. Install it (e.g. `pip install -r '
                'requirements.txt`) and retry.'
            )
        google_genai = genai
        google_types = types
        timeout_ms = int(timeout) if timeout is not None else None
        self.client = google_genai.Client(
            http_options=google_types.HttpOptions(timeout=timeout_ms)
        )
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.messages = [{'role': 'user', 'content': system_prompt}]


    def _get_chat_kwargs(self):
        return _chat_kwargs(self.model, self.reasoning_effort, self.messages)

    def generate_code(self, prompt: str, signature: str, prologue: Optional[str] = None) -> str:
        message = prompt
        if prologue:
            message += '\n\nPrologue:\n' + prologue
        message += '\n\nSignature:\n' + signature
        termcolor.cprint('<<PROBLEM', color='blue')
        print(message)
        termcolor.cprint('PROBLEM', color='blue')
        self.messages.append({'role': 'user', 'content': message})

        response = self.client.models.generate_content(**self._get_chat_kwargs())
        print_usage(response.usage_metadata)

        assistant_response = _response_text(response)
        self.messages.append({'role': 'assistant', 'content': assistant_response})

        return assistant_response

    def provide_feedback(self, error_message: str) -> str:
        self.messages.append({'role': 'user', 'content': f'Error encountered:\n{error_message}'})

        response = self.client.models.generate_content(**self._get_chat_kwargs())
        print_usage(response.usage_metadata)

        assistant_response = _response_text(response)
        self.messages.append({'role': 'assistant', 'content': assistant_response})

        return assistant_response


def run_critic(
    *,
    critic_model: str,
    critic_reasoning_effort: Optional[str],
    dslx_critic_reference: str,
    prompt: str,
    signature: str,
    requirements: str,
    generated_code: str,
) -> critic.CriticResult:
    if genai is None:
        raise RuntimeError(
            'The "google-genai" Python package is required to use the Google '
            'provider. Install it (e.g. `pip install -r requirements.txt`) '
            'and retry.'
        )

    candidate = strip_fences(generated_code).strip()
    user_message = (
        'Problem prompt:\n'
        f'{prompt}\n\n'
        'Signature:\n'
        f'{signature}\n\n'
        'Requirements:\n'
        f'{requirements}\n\n'
        f'{dslx_critic_reference}\n\n'
        'Candidate DSLX implementation:\n'
        '```dslx\n'
        f'{candidate}\n'
        '```'
    )

    google_genai = genai
    client = google_genai.Client()
    messages = [
        {'role': 'system', 'content': critic.CRITIC_SYSTEM_PROMPT},
        {'role': 'user', 'content': user_message},
    ]

    last_text = ''
    for _attempt in range(1, 3):
        response = client.models.generate_content(
            **_chat_kwargs(critic_model, critic_reasoning_effort, messages)
        )
        last_text = _response_text(response)
        try:
            parsed = _parse_critic_json(last_text)
        except Exception as e:
            # Ask for a regeneration with strictly valid JSON.
            messages.append({'role': 'assistant', 'content': last_text})
            messages.append({
                'role': 'user',
                'content': (
                    'Your previous response was not valid JSON and could not be parsed. '
                    f'Parsing error: {e}. '
                    'Please respond again with ONLY valid JSON matching the schema exactly.'
                ),
            })
            continue

        ok = bool(parsed.get('pass'))
        confidence = float(parsed.get('confidence', 0.0))
        message = str(parsed.get('message', '')).strip()
        raw_json = strip_fences(last_text).strip()
        return critic.CriticResult(ok=ok, confidence=confidence, message=message, raw_json=raw_json)

    return critic.CriticResult(
        ok=False,
        confidence=0.0,
        message='Critic did not return valid JSON after retries.',
        raw_json=strip_fences(last_text).strip(),
    )
