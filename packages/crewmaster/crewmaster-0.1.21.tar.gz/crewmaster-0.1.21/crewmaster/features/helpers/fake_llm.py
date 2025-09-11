from typing import Any, AsyncIterator, Optional

import structlog

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
)
from langchain_core.messages import (
    BaseMessage,
    AIMessageChunk,
)


log = structlog.get_logger()
"Loger para el módulo"

class FakeLLM(GenericFakeChatModel):
    """Fake LLM for tests
    
    Support streaming and astream_events
    """
    def bind_tools(
            self,
            tools: Any,
            **kwargs: Any,
    ):
        return self
    

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """Stream the output of the model.
        
        Fuente: langchain_core/language_models/fake_chat_models.py
        """
        chat_result = self._generate(
            messages, stop=stop, run_manager=run_manager, **kwargs
        )
        if not isinstance(chat_result, ChatResult):
            msg = (
                f"Expected generate to return a ChatResult, "
                f"but got {type(chat_result)} instead."
            )
            raise ValueError(msg)  # noqa: TRY004

        message = chat_result.generations[0].message

        chunk = ChatGenerationChunk(
            message=AIMessageChunk(
                id=message.id,
                content=message.content,
                tool_calls=message.tool_calls,
            )
        )
        if run_manager:
            run_manager.on_llm_new_token(
                "",
                chunk=chunk,  # No token for function call
            )
        yield chunk

    def invoke(
        self,
        input: Any,
        config: Any = None,
        *args: Any,
        stop: Optional[list[str]] = None,
        **kwargs: Any,            
    ):
        # Log before calling parent
        # log.debug(f"[FakeLLM.invoke]", input=input)
        
        # Forward call to parent implementation
        return super().invoke(
            input=input,
            config=config,
            *args,
            stop=stop,
            **kwargs,
        )