from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from openai import AsyncOpenAI, AsyncStream
from pydantic import BaseModel

from any_llm.exceptions import UnsupportedParameterError
from any_llm.provider import Provider
from any_llm.types.responses import Response, ResponseStreamEvent

if TYPE_CHECKING:
    from any_llm.types.completion import CreateEmbeddingResponse

MISSING_PACKAGES_ERROR = None
try:
    import groq

    from .utils import (
        _convert_models_list,
        _create_openai_chunk_from_groq_chunk,
        to_chat_completion,
    )
except ImportError as e:
    MISSING_PACKAGES_ERROR = e

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    import groq  # noqa: TC004
    from groq import AsyncStream as GroqAsyncStream
    from groq.types.chat import ChatCompletion as GroqChatCompletion
    from groq.types.chat import ChatCompletionChunk as GroqChatCompletionChunk

    from any_llm.types.completion import ChatCompletion, ChatCompletionChunk, CompletionParams
    from any_llm.types.model import Model


class GroqProvider(Provider):
    """Groq Provider using instructor for structured output."""

    PROVIDER_NAME = "groq"
    ENV_API_KEY_NAME = "GROQ_API_KEY"
    PROVIDER_DOCUMENTATION_URL = "https://groq.com/api"

    SUPPORTS_COMPLETION_STREAMING = True
    SUPPORTS_COMPLETION = True
    SUPPORTS_RESPONSES = True
    SUPPORTS_COMPLETION_REASONING = True
    SUPPORTS_COMPLETION_IMAGE = False
    SUPPORTS_COMPLETION_PDF = False
    SUPPORTS_EMBEDDING = False
    SUPPORTS_LIST_MODELS = True

    MISSING_PACKAGES_ERROR = MISSING_PACKAGES_ERROR

    @staticmethod
    def _convert_completion_params(params: CompletionParams, **kwargs: Any) -> dict[str, Any]:
        """Convert CompletionParams to kwargs for Groq API."""
        # Groq does not support providing reasoning effort
        converted_params = params.model_dump(exclude_none=True, exclude={"model_id", "messages"})
        if converted_params.get("reasoning_effort") == "auto":
            converted_params.pop("reasoning_effort")
        converted_params.update(kwargs)
        return converted_params

    @staticmethod
    def _convert_completion_response(response: Any) -> ChatCompletion:
        """Convert Groq response to OpenAI format."""
        return to_chat_completion(response)

    @staticmethod
    def _convert_completion_chunk_response(response: Any, **kwargs: Any) -> ChatCompletionChunk:
        """Convert Groq chunk response to OpenAI format."""
        return _create_openai_chunk_from_groq_chunk(response)

    @staticmethod
    def _convert_embedding_params(params: Any, **kwargs: Any) -> dict[str, Any]:
        """Convert embedding parameters for Groq."""
        msg = "Groq does not support embeddings"
        raise NotImplementedError(msg)

    @staticmethod
    def _convert_embedding_response(response: Any) -> CreateEmbeddingResponse:
        """Convert Groq embedding response to OpenAI format."""
        msg = "Groq does not support embeddings"
        raise NotImplementedError(msg)

    @staticmethod
    def _convert_list_models_response(response: Any) -> Sequence[Model]:
        """Convert Groq list models response to OpenAI format."""
        return _convert_models_list(response)

    async def _stream_async_completion(
        self, client: groq.AsyncGroq, params: CompletionParams, **kwargs: Any
    ) -> AsyncIterator[ChatCompletionChunk]:
        if params.stream and params.response_format:
            msg = "stream and response_format"
            raise UnsupportedParameterError(msg, self.PROVIDER_NAME)

        completion_kwargs = self._convert_completion_params(params, **kwargs)
        stream: GroqAsyncStream[GroqChatCompletionChunk] = await client.chat.completions.create(
            model=params.model_id,
            messages=cast("Any", params.messages),
            **completion_kwargs,
        )

        async def _stream() -> AsyncIterator[ChatCompletionChunk]:
            async for chunk in stream:
                yield self._convert_completion_chunk_response(chunk)

        return _stream()

    async def acompletion(
        self, params: CompletionParams, **kwargs: Any
    ) -> ChatCompletion | AsyncIterator[ChatCompletionChunk]:
        """Create a chat completion using Groq."""
        client = groq.AsyncGroq(
            api_key=self.config.api_key, **(self.config.client_args if self.config.client_args else {})
        )

        if params.response_format:
            if isinstance(params.response_format, type) and issubclass(params.response_format, BaseModel):
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": params.response_format.__name__,
                        "schema": params.response_format.model_json_schema(),
                    },
                }
            else:
                kwargs["response_format"] = params.response_format

        completion_kwargs = self._convert_completion_params(params, **kwargs)

        if params.stream:
            return await self._stream_async_completion(
                client,
                params,
                **kwargs,
            )
        response: GroqChatCompletion = await client.chat.completions.create(
            model=params.model_id,
            messages=cast("Any", params.messages),
            **completion_kwargs,
        )

        return self._convert_completion_response(response)

    async def aresponses(
        self, model: str, input_data: Any, **kwargs: Any
    ) -> Response | AsyncIterator[ResponseStreamEvent]:
        """Call Groq Responses API and normalize into ChatCompletion/Chunks."""
        # Python SDK doesn't yet support it: https://community.groq.com/feature-requests-6/groq-python-sdk-support-for-responses-api-262

        if "max_tool_calls" in kwargs:
            parameter = "max_tool_calls"
            raise UnsupportedParameterError(parameter, self.PROVIDER_NAME)

        client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.config.api_key,
            **(self.config.client_args if self.config.client_args else {}),
        )

        response = await client.responses.create(
            model=model,
            input=input_data,
            **kwargs,
        )

        if not isinstance(response, Response | AsyncStream):
            msg = f"Responses API returned an unexpected type: {type(response)}"
            raise ValueError(msg)

        return response

    def list_models(self, **kwargs: Any) -> Sequence[Model]:
        """
        Fetch available models from the /v1/models endpoint.
        """
        client = groq.Groq(api_key=self.config.api_key, **(self.config.client_args if self.config.client_args else {}))
        models_list = client.models.list(**kwargs)
        return self._convert_list_models_response(models_list)
