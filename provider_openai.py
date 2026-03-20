# SPDX-License-Identifier: Apache-2.0

import dataclasses
import json
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

    TOTAL_USAGE["cached"] += usage.prompt_tokens_details.cached_tokens
    TOTAL_USAGE["input"] += usage.prompt_tokens - usage.prompt_tokens_details.cached_tokens
    TOTAL_USAGE["output"] += usage.completion_tokens
    termcolor.cprint(
        f"Used tokens - in {usage.prompt_tokens} (cached {usage.prompt_tokens_details.cached_tokens})"
        f" - out {usage.completion_tokens} - total {usage.total_tokens}",
        color="red",
    )


def _chat_kwargs(model: str, reasoning_effort: Optional[str], messages):
    if model in NEED_REASONING_EFFORT:
        assert reasoning_effort is not None
        return {'model': model, 'reasoning_effort': reasoning_effort, 'messages': messages}
    return {'model': model, 'messages': messages}


def _parse_critic_json(text: str) -> dict:
    # Allow the critic to wrap the JSON in a triple-backtick block.
    raw = strip_fences(text).strip()
    return json.loads(raw)


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

        response = self.client.chat.completions.create(**self._get_chat_kwargs())
        print_usage(response.usage)

        assistant_response = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response

    def provide_feedback(self, error_message: str) -> str:
        self.messages.append({"role": "user", "content": f"Error encountered:\n{error_message}"})

        response = self.client.chat.completions.create(**self._get_chat_kwargs())
        print_usage(response.usage)

        assistant_response = response.choices[0].message.content.strip()
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
        response = client.chat.completions.create(
            **_chat_kwargs(critic_model, critic_reasoning_effort, messages)
        )
        last_text = response.choices[0].message.content.strip()
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
