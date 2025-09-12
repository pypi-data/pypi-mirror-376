"""LLM client for LitAI."""

import contextlib
import json
import logging
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

import openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from litai.utils.logger import get_logger

from .config import Config
from .models import LLMConfig
from .token_tracker import TokenTracker
from .token_tracker import TokenUsage as TokenUsageTracker

# Suppress OpenAI HTTP request logs
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = get_logger(__name__)

# Reasoning models that don't support max_tokens parameter
# @TODO: Most new openai models don't support max tokens
REASONING_MODELS = {
    "o4-mini-2025-04-16",
    "o3-2025-04-16",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
}


@dataclass
class TokenUsage:
    """Token usage and cost information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


class LLMClient:
    """OpenAI LLM client for LitAI."""

    def __init__(
        self, config: Config | None = None, token_tracker: TokenTracker | None = None,
    ):
        """Initialize the LLM client with optional configuration.

        Args:
            config: Optional Config instance to load LLM settings from
            token_tracker: Optional shared TokenTracker instance
        """
        self.provider: str | None = None
        self.client: AsyncOpenAI | None = None
        self.config: Config | None = config
        self.token_tracker: TokenTracker | None = token_tracker

        # Initialize token tracker if not provided but config is available
        if not token_tracker and config:
            self.token_tracker = TokenTracker(config)

        # Load LLM config from file if config is provided
        llm_config = LLMConfig()  # Default to auto-detection
        if config:
            config_data = config.load_config()
            if "llm" in config_data:
                llm_config = LLMConfig.from_dict(config_data["llm"])

        # Initialize OpenAI client
        if llm_config.is_auto or llm_config.provider == "openai":
            # Get API key from configured env var or default
            api_key_env = llm_config.api_key_env or "OPENAI_API_KEY"
            api_key = os.getenv(api_key_env)
            if not api_key:
                raise ValueError(
                    f"OpenAI API key not found. Please set {api_key_env} "
                    "environment variable, or configure it in ~/.litai/config.json",
                )
            self.provider = "openai"
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info("llm_provider_configured", provider="openai")
        else:
            raise ValueError(
                f"Unsupported provider: {llm_config.provider}. "
                "Only OpenAI is supported.",
            )

    async def close(self) -> None:
        """Close the client connections properly."""
        if self.client:
            with contextlib.suppress(Exception):
                await self.client.close()

    async def test_connection(self) -> tuple[str, TokenUsage]:
        """Test the LLM connection with a simple prompt.

        Returns:
            tuple of (response text, token usage info)
        """
        test_prompt = "Say 'Hello from LitAI' and nothing else."
        response = await self.complete(
            test_prompt,
            max_tokens=10,
            model_size="small",
            operation_type="connection_test",
        )
        if isinstance(response, dict):
            return response["content"], response["usage"]
        else:
            raise ValueError("Unexpected streaming response during connection test")

    async def complete(
        self,
        prompt: str | list[dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.0,
        tools: list[dict[str, Any]] | None = None,
        model_size: Literal["small", "large"] = "small",
        operation_type: str = "",
        reasoning_effort: Literal["minimal", "low", "medium", "high"] | None = None,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """Complete a prompt using the configured LLM with dynamic model selection.

        Args:
            prompt: The prompt to complete (string or list of messages)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            tools: Optional list of tools for function calling
            model_size: Size of model to use ("small" or "large")
            operation_type: Type of operation for tracking purposes
            reasoning_effort: Reasoning effort level for reasoning models (minimal/low/medium/high)
            stream: Whether to stream the response (OpenAI only)

        Returns:
            If stream=False: dict containing:
                - content: The generated text
                - usage: TokenUsage object with token counts and cost
                - tool_calls: Optional list of ToolCall objects
            If stream=True (OpenAI only): AsyncIterator yielding dict chunks
        """
        # Select model based on size
        try:
            if self.config:
                if model_size == "small":
                    selected_model = self.config.get_small_model()
                elif model_size == "large":
                    selected_model = self.config.get_large_model()
                else:
                    raise ValueError(
                        f"Invalid model_size: {model_size}. Must be 'small' or 'large'",
                    )
            else:
                # Fallback to defaults when no config is available
                if model_size == "small":
                    selected_model = "gpt-5-nano"
                elif model_size == "large":
                    selected_model = "gpt-5"
                else:
                    raise ValueError(
                        f"Invalid model_size: {model_size}. Must be 'small' or 'large'",
                    )

            # Validate that we have a model
            if not selected_model or not selected_model.strip():
                raise ValueError(
                    f"No {model_size} model configured. Please set up your LLM configuration with "
                    f"a {model_size} model using the /config command.",
                )

            await logger.ainfo(
                "llm_model_selected",
                provider=self.provider,
                model=selected_model,
                model_size=model_size,
                operation_type=operation_type,
            )

        except Exception as e:
            await logger.aerror(
                "llm_model_selection_failed",
                error=str(e),
                model_size=model_size,
                provider=self.provider,
            )
            raise ValueError(f"Failed to select {model_size} model: {e}") from e

        try:
            if self.provider == "openai":
                response = await self._complete_openai(
                    prompt,
                    max_tokens,
                    temperature,
                    tools,
                    selected_model,
                    reasoning_effort,
                    stream,
                )
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

            # For streaming, return the iterator directly
            if stream:
                return response
            
            # Track token usage if tracker is available (non-streaming)
            if isinstance(response, dict) and self.token_tracker and "usage" in response:
                usage = TokenUsageTracker(
                    input_tokens=response["usage"].prompt_tokens,
                    output_tokens=response["usage"].completion_tokens,
                    model=selected_model,
                    model_size=model_size,
                    operation_type=operation_type,
                )
                self.token_tracker.track_usage(usage)

            return response

        except openai.RateLimitError:
            # Don't log, just re-raise so it can be caught by callers
            raise
        except Exception as e:
            await logger.aerror(
                "llm_completion_failed",
                error=str(e),
                model=selected_model,
                model_size=model_size,
                provider=self.provider,
            )
            raise

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        model_size: Literal["small", "large"] = "small",
        operation_type: str = "text_generation",
    ) -> str:
        """Simple text generation helper - returns just the content string.

        Args:
            prompt: The prompt to complete
            max_tokens: Maximum tokens to generate
            model_size: Model size to use ("small" or "large")
            operation_type: Type of operation for tracking

        Returns:
            The generated text content
        """
        response = await self.complete(
            prompt,
            max_tokens=max_tokens,
            model_size=model_size,
            operation_type=operation_type,
        )
        return str(response["content"])

    async def _complete_openai(
        self,
        prompt: str | list[dict[str, Any]],
        max_tokens: int,
        temperature: float,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        reasoning_effort: Literal["minimal", "low", "medium", "high"] | None = None,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """Complete using OpenAI API with optional streaming."""
        if not self.client:
            raise ValueError("OpenAI client not initialized")

        # Check client type - handle both real client and mocks
        try:
            is_openai_client = isinstance(self.client, AsyncOpenAI)
        except TypeError:
            # Handle mocked clients in tests
            is_openai_client = hasattr(self.client, "chat") and hasattr(
                self.client.chat, "completions",
            )

        if not is_openai_client:
            raise ValueError("OpenAI client not initialized")

        # Handle both string prompts and message lists
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        # Use the passed model or default
        model_name = model or "gpt-5"

        # Build kwargs based on model type
        create_kwargs: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
        }

        # Only add max_tokens and temperature if not a reasoning model
        if model_name not in REASONING_MODELS:
            create_kwargs["max_tokens"] = max_tokens
            create_kwargs["temperature"] = temperature
        else:
            # For reasoning models, add reasoning effort if specified
            if reasoning_effort:
                create_kwargs["reasoning"] = {"effort": reasoning_effort}

        # Add tools if provided
        if tools:
            create_kwargs["tools"] = tools

        # Add streaming flag
        if stream:
            create_kwargs["stream"] = True
            create_kwargs["stream_options"] = {"include_usage": True}
            
            # Return async iterator for streaming
            return self._stream_openai_response(
                await self.client.chat.completions.create(**create_kwargs),
                model_name,
            )

        response: ChatCompletion = await self.client.chat.completions.create(
            **create_kwargs,
        )

        # Log the full API response for debugging
        logger.info(
            "openai_api_response",
            model=model_name,
            response_content=response.choices[0].message.content if response.choices else None,
            tool_calls=[
                {"name": tc.function.name, "args": tc.function.arguments}
                for tc in (response.choices[0].message.tool_calls or [])
            ] if response.choices else [],
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            } if response.usage else None,
        )

        message = response.choices[0].message
        usage = response.usage

        if not usage:
            raise ValueError("No usage information returned from OpenAI API")

        result = {
            "content": message.content or "",
            "usage": TokenUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            ),
        }

        # Add tool calls if present
        if message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    ),
                )
            result["tool_calls"] = tool_calls

        return result

    async def _stream_openai_response(
        self, stream_response: Any, model: str,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream OpenAI response chunks with proper event types for tool detection.
        
        Args:
            stream_response: The streaming response from OpenAI
            model: The model name for tracking
            
        Yields:
            Dictionary chunks with delta content, tool call events, and optional usage
        """
        full_content = ""
        prompt_tokens = 0
        completion_tokens = 0
        
        async for chunk in stream_response:
            # Check for tool call events
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                
                # Handle tool calls
                if hasattr(choice, 'delta') and choice.delta.tool_calls:
                    for tool_call in choice.delta.tool_calls:
                        if tool_call.function:
                            # Emit tool call events
                            if tool_call.id:  # New tool call
                                yield {
                                    "type": "response.output_item.added",
                                    "output_index": tool_call.index,
                                    "item": {
                                        "type": "function_call",
                                        "call_id": tool_call.id,
                                        "name": tool_call.function.name,
                                    },
                                }
                            if tool_call.function.arguments:  # Arguments chunk
                                yield {
                                    "type": "response.function_call_arguments.delta",
                                    "output_index": tool_call.index,
                                    "delta": tool_call.function.arguments,
                                }
                
                # Handle regular content
                if choice.delta.content is not None:
                    delta_content = choice.delta.content
                    full_content += delta_content
                    
                    # Yield the delta chunk
                    yield {"delta": delta_content}
            
            # Check for usage data in the final chunk
            if chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens
                completion_tokens = chunk.usage.completion_tokens
                total_tokens = chunk.usage.total_tokens
                
                # Track token usage if tracker is available
                if self.token_tracker:
                    usage = TokenUsageTracker(
                        input_tokens=prompt_tokens,
                        output_tokens=completion_tokens,
                        model=model,
                        model_size="small",  # Will be determined by caller
                        operation_type="query_processing",
                    )
                    self.token_tracker.track_usage(usage)
                
                # Yield final chunk with usage data
                yield {
                    "usage": TokenUsage(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                    ),
                }

