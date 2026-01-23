"""
Base Agent class for the Three-Fish framework
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from openai import OpenAI

from ..config import config


@dataclass
class AgentResponse:
    """Standardized response from an agent"""
    success: bool
    data: Dict[str, Any]
    raw_response: str
    model: str
    usage: Dict[str, int]  # tokens used
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Base class for Panchatantra Three-Fish agents.

    Each agent has:
    - A specific role and system prompt
    - A designated model (optimized for cost/capability)
    - Structured output schema
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the agent.

        Args:
            model: Override the default model for this agent
        """
        self.model = model or self.default_model
        self.client = OpenAI(
            api_key=config.models.api_key,
            base_url=config.models.base_url,
        )

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this agent type"""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining the agent's role"""
        pass

    @property
    @abstractmethod
    def output_schema(self) -> Dict[str, Any]:
        """JSON schema for structured output"""
        pass

    def _build_messages(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> list:
        """Build the message list for the API call"""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Add context from previous agents if provided
        if context:
            context_str = f"Context from previous analysis:\n```json\n{json.dumps(context, indent=2)}\n```\n\n"
            user_input = context_str + user_input

        messages.append({"role": "user", "content": user_input})

        return messages

    def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Execute the agent on the given input.

        Args:
            user_input: The user's query or input
            context: Optional context from previous agents in the chain

        Returns:
            AgentResponse with structured data
        """
        messages = self._build_messages(user_input, context)

        try:
            # Request structured JSON output
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7,
            )

            raw_content = response.choices[0].message.content

            # Handle empty response
            if not raw_content or not raw_content.strip():
                return AgentResponse(
                    success=False,
                    data={},
                    raw_response=raw_content or "",
                    model=self.model,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    },
                    error="Empty response from model"
                )

            # Clean markdown code blocks if present
            cleaned_content = raw_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            elif cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()

            # Parse JSON response
            try:
                data = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                # Try to extract JSON from the response if it's wrapped in other text
                import re
                json_match = re.search(r'\{[\s\S]*\}', cleaned_content)
                if json_match:
                    try:
                        data = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        return AgentResponse(
                            success=False,
                            data={},
                            raw_response=raw_content,
                            model=self.model,
                            usage={
                                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                            },
                            error=f"Failed to parse JSON: {e}. Raw: {raw_content[:200]}"
                        )
                else:
                    return AgentResponse(
                        success=False,
                        data={},
                        raw_response=raw_content,
                        model=self.model,
                        usage={
                            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        },
                        error=f"Failed to parse JSON: {e}. Raw: {raw_content[:200]}"
                    )

            return AgentResponse(
                success=True,
                data=data,
                raw_response=raw_content,
                model=self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                },
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                data={},
                raw_response="",
                model=self.model,
                usage={"prompt_tokens": 0, "completion_tokens": 0},
                error=str(e),
            )
