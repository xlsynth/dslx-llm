# SPDX-License-Identifier: Apache-2.0

import dataclasses
import json
import os
import time
from typing import Optional, List, Dict, Any

try:
    import openai  # type: ignore
except ModuleNotFoundError:
    openai = None
import termcolor

from dslx_text import strip_fences
import critic


NEED_REASONING_EFFORT = set(['o3-mini', 'o4-mini', 'gpt-5.1', 'gpt-5.2'])
MODEL_CHOICES = [
    'gpt-3.5-turbo',
    'gpt-4o-mini',
    'gpt-4o',
    'o1-preview',
    'o1-mini',
    'o1',
    'o1-pro',
    'o3-mini',
    'o3',
    'o4-mini',
    'gpt-4.1',
    'gpt-4.1-mini',
    'gpt-5.1',
    'gpt-5.2',
]
TOTAL_USAGE = {
    "input": 0,
    "cached": 0,
    "output": 0,
}


def print_usage(usage: Any | None) -> None:
    if usage is None:
        return

    # OpenAI-compatible backends such as vLLM can omit nested usage details, so
    # read these fields defensively instead of assuming the hosted OpenAI schema.
    prompt_tokens_details = getattr(usage, 'prompt_tokens_details', None)
    cached_tokens = getattr(prompt_tokens_details, 'cached_tokens', 0) or 0
    prompt_tokens = getattr(usage, 'prompt_tokens', 0) or 0
    completion_tokens = getattr(usage, 'completion_tokens', 0) or 0

    TOTAL_USAGE["cached"] += cached_tokens
    TOTAL_USAGE["input"] += prompt_tokens - cached_tokens
    TOTAL_USAGE["output"] += completion_tokens
    termcolor.cprint(
        f"Used tokens - in {prompt_tokens} (cached {cached_tokens})"
        f" - out {completion_tokens} - total {getattr(usage, 'total_tokens', 0) or 0}",
        color="red",
    )


def _chat_kwargs(model: str, reasoning_effort: Optional[str], messages):
    if model in NEED_REASONING_EFFORT:
        assert reasoning_effort is not None
        kwargs = {'model': model, 'reasoning_effort': reasoning_effort, 'messages': messages}
    else:
        kwargs = {'model': model, 'messages': messages}
    kwargs.update(_request_overrides())
    return kwargs


def _request_overrides() -> dict[str, Any]:
    provider_only = os.environ.get('OPENROUTER_PROVIDER_ONLY')
    if not provider_only:
        return {}

    only = [value.strip() for value in provider_only.split(',') if value.strip()]
    provider: dict[str, Any] = {'only': only}

    allow_fallbacks = os.environ.get('OPENROUTER_ALLOW_FALLBACKS')
    if allow_fallbacks is not None:
        provider['allow_fallbacks'] = allow_fallbacks.lower() in ('1', 'true', 'yes')

    return {'extra_body': {'provider': provider}}


def _parse_critic_json(text: str) -> dict:
    # Allow the critic to wrap the JSON in a triple-backtick block.
    raw = strip_fences(text).strip()
    return json.loads(raw)


def _create_chat_completion_with_retries(client: Any, **kwargs: Any) -> Any:
    for attempt in range(1, 4):
        try:
            return client.chat.completions.create(**kwargs)
        except json.JSONDecodeError:
            if attempt == 3:
                raise
            termcolor.cprint(
                f"Malformed JSON response from OpenAI-compatible backend; retrying ({attempt}/3)...",
                color="yellow",
            )
            time.sleep(attempt)


class CodeGenerator:
    # Models that require a reasoning effort config to be set.

    def __init__(
        self,
        model: str,
        reasoning_effort: Optional[str],
        system_prompt: str,
        timeout: int | float | None = None,
    ):
        if openai is None:
            raise RuntimeError(
                'The "openai" Python package is required to run evaluations. '
                'Install it (e.g. `pip install -r requirements.txt`) and retry.'
            )
        client_kwargs = {"timeout": 60 * timeout} if timeout else {}
        self.client = openai.Client(**client_kwargs)
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.messages = [{"role": "user", "content": system_prompt}]

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
        self.messages.append({"role": "user", "content": message})

        response = _create_chat_completion_with_retries(
            self.client, **self._get_chat_kwargs()
        )
        print_usage(response.usage)

        assistant_response = (response.choices[0].message.content or '').strip()
        self.messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response

    def provide_feedback(self, error_message: str) -> str:
        self.messages.append({"role": "user", "content": f"Error encountered:\n{error_message}"})

        response = _create_chat_completion_with_retries(
            self.client, **self._get_chat_kwargs()
        )
        print_usage(response.usage)

        assistant_response = (response.choices[0].message.content or '').strip()
        self.messages.append({"role": "assistant", "content": assistant_response})

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
    if openai is None:
        raise RuntimeError(
            'The "openai" Python package is required to run evaluations. '
            'Install it (e.g. `pip install -r requirements.txt`) and retry.'
        )

    candidate = strip_fences(generated_code).strip()
    user_message = (
        "Problem prompt:\n"
        f"{prompt}\n\n"
        "Signature:\n"
        f"{signature}\n\n"
        "Requirements:\n"
        f"{requirements}\n\n"
        f"{dslx_critic_reference}\n\n"
        "Candidate DSLX implementation:\n"
        "```dslx\n"
        f"{candidate}\n"
        "```"
    )

    client = openai.Client()
    messages = [
        {"role": "system", "content": critic.CRITIC_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    last_text = ""
    for _attempt in range(1, 3):
        response = _create_chat_completion_with_retries(
            client,
            **_chat_kwargs(critic_model, critic_reasoning_effort, messages),
        )
        last_text = (response.choices[0].message.content or '').strip()
        try:
            parsed = _parse_critic_json(last_text)
        except Exception as e:
            # Ask for a regeneration with strictly valid JSON.
            messages.append({"role": "assistant", "content": last_text})
            messages.append({
                "role": "user",
                "content": (
                    "Your previous response was not valid JSON and could not be parsed. "
                    f"Parsing error: {e}. "
                    "Please respond again with ONLY valid JSON matching the schema exactly."
                ),
            })
            continue

        ok = bool(parsed.get("pass"))
        confidence = float(parsed.get("confidence", 0.0))
        message = str(parsed.get("message", "")).strip()
        raw_json = strip_fences(last_text).strip()
        return critic.CriticResult(ok=ok, confidence=confidence, message=message, raw_json=raw_json)

    return critic.CriticResult(
        ok=False,
        confidence=0.0,
        message="Critic did not return valid JSON after retries.",
        raw_json=strip_fences(last_text).strip(),
    )
