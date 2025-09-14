import io
import base64
import functools
from abc import ABC, abstractmethod
from typing import (
    Optional,
    Dict,
    Type,
    Generator,
    AsyncGenerator,
    TypedDict,
    Literal,
    List,
    TypeVar,
    Generic,
)
import tiktoken
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from .ai_config import AIConfig, Model, GenerationType
from .moderation import Moderation


# Type variables for default and streamable models
T = TypeVar("T", bound=BaseModel)  # Default model type
S = TypeVar("S", bound=BaseModel)  # Streamable model type


@functools.lru_cache()
def _get_encoding_for_model(model_name: str) -> tiktoken.Encoding:
    """
    Returns the tiktoken encoding for the given model name,
    leveraging LRU caching to avoid repeated calls.
    """
    return tiktoken.encoding_for_model(model_name)


class OpenAIMessage(TypedDict):
    role: str
    content: str


class BaseToolkitModel(ABC, Generic[T, S]):
    model_name: str
    openai_api_key: str
    default_pydantic_model: Type[T] = BaseModel
    default_streamable_pydantic_model: Optional[Type[S]] = None

    def __init__(
        self,
        ai_config: AIConfig,
        openai_api_key: str,
    ):
        self.ai_config = ai_config
        self.openai_api_key = openai_api_key
        self.moderation = Moderation(ai_config=ai_config, openai_api_key=openai_api_key)

    @property
    def text_model_name(self) -> Optional[str]:
        """
        Returns the name of the text model used by this toolkit model.
        If not set, returns None.
        """
        model_dict = self.ai_config.text_generation
        default_model = self._get_default_model(model_dict.models)
        return default_model.name if default_model else None

    def count_tokens(self, text: str) -> int:
        if self.text_model_name is None:
            raise ValueError("text_model_name is not set for this BaseToolkitModel.")
        encoding = _get_encoding_for_model(self.text_model_name)
        encoded_text = encoding.encode(text)
        return len(encoded_text)

    @staticmethod
    def compose_message_openai(
        message_text: str, role: Literal["user", "system"] = "user"
    ) -> OpenAIMessage:
        return OpenAIMessage({"role": role, "content": message_text})

    @staticmethod
    def compose_messages_openai(
        user_input: str, system_prompt: Optional[str] = None
    ) -> List[OpenAIMessage]:
        result = []
        if system_prompt is not None:
            result.append(
                BaseToolkitModel.compose_message_openai(system_prompt, role="system")
            )
        result.append(BaseToolkitModel.compose_message_openai(user_input))
        return result

    @staticmethod
    def get_langchain_message(message_dict: OpenAIMessage) -> BaseMessage:
        return (
            HumanMessage(content=message_dict["content"])
            if message_dict["role"] == "user"
            else SystemMessage(content=message_dict["content"])
        )

    def _compose_messages_list(
        self,
        user_input: str,
        system_message: str,
        communication_history: List[OpenAIMessage],
    ) -> List[OpenAIMessage]:
        user_message = self.compose_message_openai(user_input)
        system_message = self.compose_message_openai(system_message, role="system")
        return [system_message, user_message] + communication_history

    @staticmethod
    def get_langchain_messages(messages: List[OpenAIMessage]) -> List[BaseMessage]:
        return list(map(BaseToolkitModel.get_langchain_message, messages))

    def get_langchain_llm(self) -> ChatOpenAI:
        return ChatOpenAI(
            api_key=self.openai_api_key,
            temperature=self.get_model().temperature,
            model=self.get_model().name,
            max_tokens=self.get_model().structured_output_max_tokens,
        )

    def moderate_text(self, text: str) -> bool:
        return self.moderation.moderate_text(text)

    async def amoderate_text(self, text: str) -> bool:
        return await self.moderation.amoderate_text(text)

    @staticmethod
    def get_b64_from_bytes(in_memory_stream: io.BytesIO) -> str:
        in_memory_stream.seek(0)
        return base64.b64encode(in_memory_stream.read()).decode("utf-8")

    def run(
        self,
        system_prompt: Optional[str] = None,
        pydantic_model: Optional[Type[BaseModel]] = None,
        communication_history: Optional[List[OpenAIMessage]] = None,
        *args,
        **kwargs,
    ) -> BaseModel:
        system_prompt = system_prompt or self.get_default_system_prompt()
        pydantic_model = pydantic_model or self.default_pydantic_model
        communication_history = communication_history or []
        return self.run_impl(
            *args,
            system_prompt=system_prompt,
            pydantic_model=pydantic_model,
            communication_history=communication_history,
            **kwargs,
        )

    @abstractmethod
    def run_impl(
        self,
        system_prompt: str,
        pydantic_model: str,
        communication_history: List[OpenAIMessage],
        *args,
        **kwargs,
    ) -> BaseModel:
        raise NotImplementedError

    def run_default(
        self,
        system_prompt: Optional[str] = None,
        communication_history: Optional[List[OpenAIMessage]] = None,
        *args,
        **kwargs,
    ) -> T:
        result = self.run(
            system_prompt=system_prompt,
            communication_history=communication_history,
            *args,
            **kwargs,
        )
        if not isinstance(result, self.default_pydantic_model):
            raise ValueError(
                f"Expected result of type {self.default_pydantic_model}, "
                f"but got {type(result)}"
            )
        return result

    async def arun(
        self,
        system_prompt: Optional[str] = None,
        pydantic_model: Optional[Type[BaseModel]] = None,
        communication_history: Optional[List[OpenAIMessage]] = None,
        *args,
        **kwargs,
    ) -> BaseModel:
        system_prompt = system_prompt or self.get_default_system_prompt()
        pydantic_model = pydantic_model or self.default_pydantic_model
        communication_history = communication_history or []
        return await self.arun_impl(
            *args,
            system_prompt=system_prompt,
            pydantic_model=pydantic_model,
            communication_history=communication_history,
            **kwargs,
        )

    async def arun_impl(
        self,
        system_prompt: str,
        pydantic_model: str,
        communication_history: List[OpenAIMessage],
        *args,
        **kwargs,
    ) -> BaseModel:
        raise NotImplementedError

    async def arun_default(
        self,
        system_prompt: Optional[str] = None,
        communication_history: Optional[List[OpenAIMessage]] = None,
        *args,
        **kwargs,
    ) -> T:
        result = await self.arun(
            system_prompt=system_prompt,
            communication_history=communication_history,
            *args,
            **kwargs,
        )
        if not isinstance(result, self.default_pydantic_model):
            raise ValueError(
                f"Expected result of type {self.default_pydantic_model}, "
                f"but got {type(result)}"
            )
        return result

    def stream(
        self,
        system_prompt: Optional[str] = None,
        communication_history: Optional[List[OpenAIMessage]] = None,
        *args,
        **kwargs,
    ) -> Generator[BaseModel, None, None]:
        system_prompt = system_prompt or self.get_default_system_prompt()
        communication_history = communication_history or []
        yield from self.stream_impl(
            *args,
            system_prompt=system_prompt,
            communication_history=communication_history,
            **kwargs,
        )

    def stream_impl(
        self,
        system_prompt: str,
        communication_history: List[OpenAIMessage],
        *args,
        **kwargs,
    ) -> Generator[BaseModel, None, None]:
        raise NotImplementedError

    def stream_default(
        self,
        system_prompt: Optional[str] = None,
        communication_history: Optional[List[OpenAIMessage]] = None,
        *args,
        **kwargs,
    ) -> Generator[S, None, None]:
        for model in self.stream(
            system_prompt=system_prompt,
            communication_history=communication_history,
            *args,
            **kwargs,
        ):
            if not isinstance(model, self.default_streamable_pydantic_model):
                raise ValueError(
                    f"Expected result of type {self.default_streamable_pydantic_model}, "
                    f"but got {type(model)}"
                )
            yield model

    async def astream(
        self,
        system_prompt: Optional[str] = None,
        communication_history: Optional[List[OpenAIMessage]] = None,
        *args,
        **kwargs,
    ) -> AsyncGenerator[BaseModel, None]:
        system_prompt = system_prompt or self.get_default_system_prompt()
        communication_history = communication_history or []
        async for model in self.astream_impl(
            *args,
            system_prompt=system_prompt,
            communication_history=communication_history,
            **kwargs,
        ):
            yield model

    async def astream_impl(
        self,
        system_prompt: str,
        communication_history: List[OpenAIMessage],
        *args,
        **kwargs,
    ) -> AsyncGenerator[BaseModel, None]:
        raise NotImplementedError

    async def astream_default(
        self,
        system_prompt: Optional[str] = None,
        communication_history: Optional[List[OpenAIMessage]] = None,
        *args,
        **kwargs,
    ) -> AsyncGenerator[S, None]:
        async for model in self.astream(
            system_prompt=system_prompt,
            communication_history=communication_history,
            *args,
            **kwargs,
        ):
            if not isinstance(model, self.default_streamable_pydantic_model):
                raise ValueError(
                    f"Expected result of type {self.default_streamable_pydantic_model}, "
                    f"but got {type(model)}"
                )
            yield model

    @abstractmethod
    def get_price(*args, **kwargs):
        raise NotImplementedError

    def _get_default_model(
        self, models_dict: Optional[Dict[str, Model]] = None
    ) -> Optional[Model]:
        if models_dict is None:
            models_dict = self.get_models_dict()
        return next(
            iter(
                filter(
                    lambda model: getattr(model, "is_default", False),
                    models_dict.values(),
                )
            ),
            None,
        )

    @abstractmethod
    def get_model_config(self) -> GenerationType:
        raise NotImplementedError

    def get_models_dict(self) -> Dict[str, Model]:
        return self.get_model_config().models

    def get_model(self, model_name: Optional[str] = None) -> Model:
        if model_name is None:
            return self._get_default_model()
        model = self.get_models_dict().get(model_name)
        if model is None:
            raise ValueError(f"Model {model_name} not found")
        return model

    @property
    def default_model(self) -> Model:
        return self._get_default_model()

    @property
    def moderation_needed(self) -> bool:
        return self.get_model_config().moderation_needed

    @abstractmethod
    def get_default_system_prompt(self) -> str:
        raise NotImplementedError(
            "get_default_system_prompt is not implemented in this BaseToolkitModel. "
            "Please implement it in the derived class."
        )
