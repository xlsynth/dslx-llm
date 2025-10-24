# SPDX-License-Identifier: Apache-2.0

from typing import Optional, List, Dict

import openai
import termcolor

class CodeGenerator:
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
    ]

    def __init__(self, model: str, reasoning_effort: Optional[str], system_prompt: str):
        """Initialize the CodeGenerator with a persistent OpenAI connection."""
        self.client = openai.Client()
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.messages = [
            {"role": "user", "content": system_prompt}
        ]

    def _get_chat_kwargs(self):
        if self.model == 'o3-mini' or self.model == 'o4-mini':
            assert self.reasoning_effort is not None
            return {
                'model': self.model,
                'reasoning_effort': self.reasoning_effort,
                'messages': self.messages,
            }
        return {'model': self.model, 'messages': self.messages}

    def generate_code(self, prompt: str, signature: str, prologue: Optional[str] = None) -> str:
        """Generate code using the OpenAI API and retain context for follow-ups."""
        # Add user prompt to the message history
        message = prompt
        if prologue:
            message += '\n\nPrologue:\n' + prologue
        message += '\n\nSignature:\n' + signature
        termcolor.cprint('<<PROBLEM', color='blue')
        print(message)
        termcolor.cprint('PROBLEM', color='blue')
        self.messages.append({"role": "user", "content": message})

        # Make the API call
        response = self.client.chat.completions.create(
            **self._get_chat_kwargs()
        )

        # Capture assistant response and add it to the message history
        assistant_response = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response

    def provide_feedback(self, error_message):
        """Feed follow-up errors back into the conversation."""
        # Add the error message as a user input to the message history
        self.messages.append({"role": "user", "content": f"Error encountered:\n{error_message}"})

        # Make the API call
        response = self.client.chat.completions.create(
            **self._get_chat_kwargs()
        )

        # Capture assistant response and add it to the message history
        assistant_response = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response
