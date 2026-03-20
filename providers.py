from typing import Protocol, Optional

import critic
import provider_google as google
import provider_openai as openai


class ClassGenerator(Protocol):
    def generate_code(self,
                       prompt: str,
                       signature: str,
                       prologue: Optional[str] = None) -> str: ...
    def provide_feedback(self, error_message: str) -> str: ...


class ProviderModule(Protocol):
    @staticmethod
    def CodeGenerator(
            model: str,
            reasoning_effort: Optional[str],
            system_prompt: str,
            timeout: int | float | None = None
    ) -> ClassGenerator: ...

    @staticmethod
    def run_critic(
            *,
            critic_model: str,
            critic_reasoning_effort: Optional[str],
            dslx_critic_reference: str,
            prompt: str,
            signature: str,
            requirements: str,
            generated_code: str,
    ) -> critic.CriticResult: ...
