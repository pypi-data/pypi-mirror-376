from typing import Any, AsyncIterator, Dict, List, Optional
import pytest
import structlog

from langchain_core.runnables.utils import (
    ConfigurableFieldSpec
)
from langchain_core.runnables import (
    RunnableConfig,
)
from langchain_core.callbacks.manager import (
    CallbackManagerForChainRun
)
from .with_config_verified import WithAsyncStreamConfigVerified
from ...core.pydantic import (
    BaseModel,
)


log = structlog.get_logger()
"Loger para el módulo"

class InputModel(BaseModel):
    message: str

class OutputModel(BaseModel):
    result: str

class FakeStreamable(
    WithAsyncStreamConfigVerified[InputModel, OutputModel]
):
    @property
    def config_specs(self) -> List[ConfigurableFieldSpec]:
        required = [
            ConfigurableFieldSpec(
                id='client_name',
                name='test of dependency',
                annotation=str,
                default=...
            ),
            ConfigurableFieldSpec(
                id='age',
                name='test of number dependency',
                annotation=int,
                default=...
            )
        ]
        return required

    def invoke(
        self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any
    ):
        raise Exception('Not implemented')


    async def astream_config_parsed(
        self,
        input: InputModel,
        config_parsed: BaseModel,
        config_raw: RunnableConfig,
        run_manager: CallbackManagerForChainRun,
        **kwargs: Optional[Any],
    ) -> AsyncIterator[Dict[str, Any]]:
        client_name = config_parsed.configurable.client_name
        age = config_parsed.configurable.age
        iterator = iter([{"result": f'{input.message}, {client_name} is {age} years old'}])
        for chunk in iterator:
            yield chunk


# @pytest.mark.only
@pytest.mark.asyncio
async def test_invoke_with_valid_parameters():
    fake_runnable = FakeStreamable()
    config = RunnableConfig(configurable={
        'client_name': 'Pedrito',
        'age': 25
    })
    input = InputModel.model_validate({'message': 'hola'})
    iterator = fake_runnable.astream(input, config)
    async for chunk in iterator:
        output = chunk
    assert output.get('result') == "hola, Pedrito is 25 years old"

@pytest.mark.asyncio
async def test_invoke_with_incomplete_parameters():
    fake_runnable = FakeStreamable()
    config = RunnableConfig(configurable={
        'client_name': 'Pedrito'
    })
    input = InputModel.model_validate({'message': 'hola'})
    with pytest.raises(Exception) as exc_info:
        async for chunk in fake_runnable.astream(input, config):
            result = chunk
    error_msg = str(exc_info.value)
    assert "configurable.age" in error_msg
    assert "Field required" in error_msg
    assert "type=missing" in error_msg

@pytest.mark.asyncio
async def test_invoke_with_wrong_parameters():
    fake_runnable = FakeStreamable()
    config = RunnableConfig(configurable={
        'client_name': 'Pedrito',
        'age': 'no_soy_un_numero'
    })
    input = InputModel.model_validate({'message': 'hola'})
    with pytest.raises(Exception) as exc_info:
        async for chunk in fake_runnable.astream(input, config):
            result = chunk
    error_msg = str(exc_info.value)
    assert "Input should be a valid integer" in error_msg
