from typing import List, Optional
import pytest
import structlog

from langchain_core.runnables.utils import (
    ConfigurableFieldSpec
)
from langchain_core.runnables import (
    RunnableConfig,
)
from .with_config_verified import WithInvokeConfigVerified
from ...core.pydantic import (
    BaseModel,
)


log = structlog.get_logger()
"Loger para el módulo"

class FakeInvokable(
    WithInvokeConfigVerified[BaseModel, BaseModel]
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

    def invoke_config_parsed(
        self,
        input: BaseModel,
        config_parsed: BaseModel,
        config_raw: Optional[RunnableConfig] = None
    ) -> str:
        client_name = config_parsed.configurable.client_name
        age = config_parsed.configurable.age
        return f'{input}, {client_name} is {age} years old'


@pytest.mark.asyncio
async def test_invoke_with_valid_parameters():
    fake_runnable = FakeInvokable()
    config = RunnableConfig(configurable={
        'client_name': 'Pedrito',
        'age': 25
    })
    result = fake_runnable.invoke('hola', config)
    assert result == 'hola, Pedrito is 25 years old'

@pytest.mark.asyncio
async def test_invoke_with_incomplete_parameters():
    fake_runnable = FakeInvokable()
    config = RunnableConfig(configurable={
        'client_name': 'Pedrito'
    })
    with pytest.raises(Exception) as exc_info:
        result = fake_runnable.invoke('hola', config)
    error_msg = str(exc_info.value)
    assert "configurable.age" in error_msg
    assert "Field required" in error_msg
    assert "type=missing" in error_msg

@pytest.mark.asyncio
async def test_invoke_with_wrong_parameters():
    fake_runnable = FakeInvokable()
    config = RunnableConfig(configurable={
        'client_name': 'Pedrito',
        'age': 'no_soy_un_numero'
    })
    with pytest.raises(Exception) as exc_info:
        result = fake_runnable.invoke('hola', config)
    error_msg = str(exc_info.value)
    assert "Input should be a valid integer" in error_msg
