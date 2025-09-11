"""Tests for BrainBase

"""

from typing import Dict, List, Optional, Type

import pytest
import structlog
from datetime import datetime


from langchain_core.messages import (
    AIMessage,
    ToolCall,
)

from langchain_core.runnables import (
    RunnableConfig,
)

from ...core.pydantic import (
    BaseModel,
    Field,
)
from ..helpers.fake_llm import FakeLLM

from ..collaborator import (
    UserMessage,
)
from ..skill import (
    BrainSchemaBase,
    ResultSchemaBase,
    Skill,
    SkillComputationDirect,
    SkillStructuredResponse,
    SkillContribute,
)
from .brain_types import (
    BrainOutputComputationsRequired,
    BrainOutputContribution,
    BrainOutputResponse,
    BrainOutputResponseStructured,
    BrainInputFresh,
    SituationBuilderFn,
)
from .brain_base import (
    BrainBase
)

log = structlog.get_logger()
"Loger para el módulo"



class SumInput(BrainSchemaBase):
    """Esquema de entrada para fake tool de Suma"""
    number_1: int
    number_2: int


class SumOutput(ResultSchemaBase):
    """Esquema de salida para fake tool de Suma"""
    result: int


class SingleItemsInput(BaseModel):
    """Esquema de entrada para fake tool de Listar items"""
    name: str
    description: str


class ListItemsInput(BrainSchemaBase):
    """Esquema de salida para fake tool de Listar items"""
    items: List[SingleItemsInput]


class SumSkill(
    SkillComputationDirect[
        SumInput,
        SumOutput
    ]
):
    """Fake tool para sumar dos números"""
    name: str = 'sum'
    description: str = 'given two numbers return the sum of both'
    brain_schema: Type[SumInput] = SumInput
    result_schema: Type[SumOutput] = SumOutput

    async def async_executor(
        self,
        request: SumInput,
        config: RunnableConfig
    ) -> SumOutput:
        number_1 = request.number_1
        number_2 = request.number_2
        value = SumOutput.parse_obj(
            {"result": number_1 + number_2}
        )
        return value


sum_computation = SumSkill()

list_items_computation: Skill = SkillStructuredResponse(
    name='list_items',
    description=(
        'shows a list of items in a structured format for the user'
    ),
    brain_schema=ListItemsInput
)


send_message_to_colleague = SkillContribute(
    name='send_message_to_colleague',
    description='Send a message to a colleague',
)


def situation_builder(input, config):
    return 'keep focus'


class BrainFake(BrainBase):
    """Cerebro fake para los tests"""
    agent_name: str = "Adam_Smith"
    instructions: str = """
        Your name is Adam_Smith

        Answer questions only about Finance and Mathematics.
    """
    skills: List[Skill] = [
        send_message_to_colleague,
        sum_computation,
        list_items_computation,
    ]
    situation_builder: Optional[SituationBuilderFn] = situation_builder


def create_input_fresh(content: str, user_name: str = 'Cheito'):
    user_message = UserMessage(
        id='1222',
        timestamp=datetime.now().isoformat(),
        content=content
    )
    input = BrainInputFresh(
        messages=[user_message],
        user_name=user_name,
        today=datetime.now().isoformat()
    )
    return input


@pytest.fixture
def config_fake_llm():
    def real_config(responses):
        config = RunnableConfig(
            configurable={
                "llm_srv": FakeLLM(messages=iter(responses))
            }
        )
        return config
    return real_config


# @pytest.mark.only
def test_hello(config_fake_llm):
    brain = BrainFake()
    input = create_input_fresh('hola, cuál es mi nombre?', 'Cheito')
    response = ['Hola, Cheito']
    result = brain.invoke(input, config_fake_llm(response))
    assert isinstance(result, BrainOutputResponse)
    content = result.message.content
    assert 'Cheito' in content


# @pytest.mark.only
def test_computation_required(config_fake_llm):
    brain = BrainFake()
    mock_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='sum',
                id='1', 
                args={'number_1': 3, 'number_2': 3}
            ),
        ]
    )
    input = create_input_fresh('cuánto es 3 + 3?')
    result = brain.invoke(input, config_fake_llm([mock_response]))
    assert isinstance(result, BrainOutputComputationsRequired)

# @pytest.mark.only
def test_skill_non_valid(config_fake_llm):
    brain = BrainFake()
    mock_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='parrot_multiply_tool',
                id='1', 
                args={'a': 3, 'b': 3}
            ),
        ]
    )
    input = create_input_fresh('cuánto es 3 + 3?')
    with pytest.raises(ValueError) as exc_info:
        brain.invoke(input, config_fake_llm([mock_response]))
    
    error_message = str(exc_info.value)

    assert "Skill name not available" in error_message


# @pytest.mark.only
def test_contribution(config_fake_llm):
    brain = BrainFake()
    input = create_input_fresh(
        'Una pregunta de literatura, '
        'quién escribió la novela 100 martirios insoportables?'
    )
    mock_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='send_message_to_colleague',
                id='1', 
                args={'to': 'cervantes', 'from': 'supervisor', 'message': "ayudame con esto"}
            ),
        ]
    )    
    result = brain.invoke(input, config_fake_llm([mock_response]))
    assert isinstance(result, BrainOutputContribution)


# @pytest.mark.only
def test_response_structured(config_fake_llm):
    brain = BrainFake()
    input = create_input_fresh(
        'Quiero ver una lista de los tipos'
        ' de cuenta bancaria que existen?'
    )
    mock_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='list_items',
                id='1', 
                args={"items": [{"name": "corriente", "description": "cuenta con cheques"}]}
            ),
        ]
    )    
    result = brain.invoke(input, config_fake_llm([mock_response]))
    assert isinstance(result, BrainOutputResponseStructured)


# @pytest.mark.only
@pytest.mark.asyncio
async def test_stream_hello(config_fake_llm):
    brain = BrainFake()
    input = create_input_fresh('hola, cuál es mi nombre?')
    mock_response = AIMessage(
        content="Hola, tu nombre es Cheito",
    )   
    events = []
    async for event in brain.astream_events(
        input,
        config=config_fake_llm([mock_response]),
        version="v2",
    ):
        events.append(event)
    assert len(events) > 4
    last_event = events[-1]
    assert last_event.get('event') == 'on_chain_end'
    result = last_event.get('data', {}).get('output')
    assert isinstance(result, BrainOutputResponse)
    content = result.message.content
    assert 'Cheito' in content

# @pytest.mark.only
@pytest.mark.asyncio
async def test_stream_computation_requested(config_fake_llm):
    brain = BrainFake()
    input = create_input_fresh('cuánto es 3 + 3?')
    mock_response = AIMessage(
        content="churro",
        tool_calls=[
            ToolCall(
                name='sum',
                id='1', 
                args={'number_1': 3, 'number_2': 3}
            ),
        ]
    )
    events = []
    async for event in brain.astream_events(
        input,
        config=config_fake_llm([mock_response]),
        version="v2",
    ):
        events.append(event)
    assert len(events) > 4
    last_event = events[-1]
    assert last_event.get('event') == 'on_chain_end'
    result = last_event.get('data', {}).get('output')
    assert isinstance(result, BrainOutputComputationsRequired)


# @pytest.mark.only
@pytest.mark.asyncio
async def test_get_skills_brain_schema():
    brain = BrainFake()
    skills_map = brain.get_skills_as_dict()
    assert isinstance(skills_map, Dict)
    assert 'sum' in skills_map.keys()
    assert skills_map['sum'].brain_schema == SumInput
