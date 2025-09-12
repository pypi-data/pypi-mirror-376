import asyncio
import logging
from typing import Any, Dict, Generic, List, Protocol, TypeVar, Union

from pydantic import BaseModel

logger = logging.getLogger(__name__)

import dotenv
from cogents_core.llm import BaseLLMClient, get_llm_client

dotenv.load_dotenv()

################################################################################
# Browser-use compatibility
################################################################################

# Define the TypeVar for generic typing
T = TypeVar("T")


class ChatInvokeCompletion(BaseModel, Generic[T]):
    completion: T
    thinking: str | None = None
    redacted_thinking: str | None = None


class ModelError(Exception):
    pass


class ModelProviderError(ModelError):
    def __init__(self, message: str, status_code: int = 502, model: str | None = None):
        super().__init__(message, status_code)
        self.model = model


class ModelRateLimitError(ModelProviderError):
    def __init__(self, message: str, status_code: int = 429, model: str | None = None):
        super().__init__(message, status_code, model)


# Define message types for compatibility
from typing import Literal


class ContentPartTextParam(BaseModel):
    text: str
    type: Literal["text"] = "text"


class ContentPartRefusalParam(BaseModel):
    refusal: str
    type: Literal["refusal"] = "refusal"


class ContentPartImageParam(BaseModel):
    image_url: Any
    type: Literal["image_url"] = "image_url"


class _MessageBase(BaseModel):
    role: Literal["user", "system", "assistant"]
    cache: bool = False


class UserMessage(_MessageBase):
    role: Literal["user"] = "user"
    content: str | list[ContentPartTextParam | ContentPartImageParam]
    name: str | None = None


class SystemMessage(_MessageBase):
    role: Literal["system"] = "system"
    content: str | list[ContentPartTextParam]
    name: str | None = None


class AssistantMessage(_MessageBase):
    role: Literal["assistant"] = "assistant"
    content: str | list[ContentPartTextParam | ContentPartRefusalParam] | None
    name: str | None = None
    refusal: str | None = None
    tool_calls: list = []


BaseMessage = Union[UserMessage, SystemMessage, AssistantMessage]
ContentText = ContentPartTextParam
ContentRefusal = ContentPartRefusalParam
ContentImage = ContentPartImageParam


# Define the BaseChatModel class for compatibility
class BaseChatModel(Protocol):
    """Base chat model that adapts cogents LLM clients for browser-use compatibility."""

    def __init__(self, llm_client: BaseLLMClient):
        """
        Initialize Base Chat Model

        Args:
            llm_client: cogents LLM client to adapt
        """
        self.llm_client = llm_client
        self._verified_api_keys = True  # Assume the cogents client is properly configured

    @property
    def provider(self) -> str:
        """Return provider name if available"""
        return getattr(self.llm_client, "provider", "unknown")

    @property
    def name(self) -> str:
        """Return the model name."""
        return self.model

    @property
    def model(self) -> str:
        """Return model name"""
        return self.model_name

    @property
    def model_name(self) -> str:
        """Return the model name for legacy support."""
        return getattr(self.llm_client, "chat_model", getattr(self.llm_client, "model", "unknown"))

    async def ainvoke(
        self, messages: list[BaseMessage], output_format: type[T] | None = None
    ) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
        """Invoke the LLM with messages."""
        try:
            # Convert browser-use messages to cogents format
            cogents_messages = []
            for msg in messages:
                if hasattr(msg, "role"):
                    # Extract text content properly from browser-use message objects
                    content_text = ""
                    if hasattr(msg, "text"):
                        # Use the convenient .text property that handles both string and list formats
                        content_text = msg.text
                    elif hasattr(msg, "content"):
                        # Fallback: handle content directly
                        if isinstance(msg.content, str):
                            content_text = msg.content
                        elif isinstance(msg.content, list):
                            # Extract text from content parts
                            text_parts = []
                            for part in msg.content:
                                if hasattr(part, "text") and hasattr(part, "type") and part.type == "text":
                                    text_parts.append(part.text)
                            content_text = "\n".join(text_parts)
                        else:
                            content_text = str(msg.content)
                    else:
                        content_text = str(msg)

                    cogents_messages.append({"role": msg.role, "content": content_text})
                elif isinstance(msg, dict):
                    # Already in the right format
                    cogents_messages.append(msg)
                else:
                    # Handle other message formats
                    cogents_messages.append({"role": "user", "content": str(msg)})

            # Choose completion method based on output_format
            if output_format is not None:
                # Use structured completion for structured output
                try:
                    if asyncio.iscoroutinefunction(self.llm_client.structured_completion):
                        structured_response = await self.llm_client.structured_completion(
                            cogents_messages, output_format
                        )
                    else:
                        structured_response = self.llm_client.structured_completion(cogents_messages, output_format)
                    return ChatInvokeCompletion(completion=structured_response)
                except Exception as e:
                    logger.error(f"Error in structured completion: {e}")
                    raise
            else:
                # Use regular completion for string output
                if asyncio.iscoroutinefunction(self.llm_client.completion):
                    response = await self.llm_client.completion(cogents_messages)
                else:
                    response = self.llm_client.completion(cogents_messages)

                return ChatInvokeCompletion(completion=str(response))

        except Exception as e:
            logger.error(f"Error in LLM adapter: {e}")
            raise


################################################################################
# MemU agent compatibility
################################################################################


class MemoryLLMAdapter:
    """Adapter to make cogents LLM clients compatible with memory agent system"""

    def __init__(self, llm_client: BaseLLMClient):
        """Initialize with the original LLM client"""
        self.llm_client = llm_client

    def simple_chat(self, message: str) -> str:
        """
        Simple chat method that wraps the completion method

        Args:
            message: The message to send to the LLM

        Returns:
            str: The LLM response
        """
        try:
            # Convert single message to messages format
            messages = [{"role": "user", "content": message}]

            # Call the completion method
            response = self.llm_client.completion(messages)

            # Return the response as string
            return str(response)

        except Exception as e:
            logger.error(f"Error in simple_chat: {e}")
            raise

    def chat_completion(self, messages: List[Dict[str, str]], tools=None, tool_choice=None, **kwargs) -> Any:
        """
        Chat completion method for automated memory processing

        Args:
            messages: List of message dictionaries
            tools: Optional tools for function calling
            tool_choice: Tool choice strategy
            **kwargs: Additional arguments

        Returns:
            Mock response object for memory agent compatibility
        """
        try:
            # For now, call the regular completion method
            # In a full implementation, this would handle tool calls properly
            response_text = self.llm_client.completion(messages, **kwargs)

            # Create a mock response object that the memory agent expects
            class MockResponse:
                def __init__(self, content, success=True):
                    self.success = success
                    self.content = content
                    self.tool_calls = []  # No function calling in this simplified version
                    self.error = None if success else "Mock error"

            return MockResponse(str(response_text))

        except Exception as e:
            logger.error(f"Error in chat_completion: {e}")

            class MockResponse:
                def __init__(self, error_msg):
                    self.success = False
                    self.content = ""
                    self.tool_calls = []
                    self.error = error_msg

            return MockResponse(str(e))

    def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text using the underlying LLM client

        Args:
            text: Text to embed

        Returns:
            List[float]: Embedding vector
        """
        return self.llm_client.embed(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using the underlying LLM client

        Args:
            texts: List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        return self.llm_client.embed_batch(texts)

    def get_embedding_dimensions(self) -> int:
        """
        Get the embedding dimensions from the underlying LLM client

        Returns:
            int: Embedding dimensions
        """
        return self.llm_client.get_embedding_dimensions()


def get_llm_client_bu_compatible(**kwargs) -> BaseChatModel:
    """
    Get an LLM client with browser-use compatibility

    Args:
        **kwargs: Additional arguments to pass to the LLM client

    Returns:
        BaseChatModel: Configured LLM client adapted for browser-use
    """
    return BaseChatModel(get_llm_client(structured_output=True, **kwargs))


def get_llm_client_memu_compatible(**kwargs) -> BaseLLMClient:
    """
    Get an LLM client with optional MemU system compatibility

    Args:
        **kwargs: Additional arguments to pass to the LLM client

    Returns:
        BaseLLMClient: Configured LLM client
    """
    return MemoryLLMAdapter(get_llm_client(structured_output=True, **kwargs))


__all__ = [
    # Adapters
    "MemoryLLMAdapter",
    "BaseChatModel",
    # Factory functions
    "get_llm_client_bu_compatible",
    "get_llm_client_memu_compatible",
    # Message types
    "BaseMessage",
    "UserMessage",
    "SystemMessage",
    "AssistantMessage",
    "ContentText",
    "ContentRefusal",
    "ContentImage",
    # Views
    "ChatInvokeCompletion",
    # Exceptions
    "ModelError",
    "ModelProviderError",
    "ModelRateLimitError",
]
