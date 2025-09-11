import os
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Type,
)
from unittest import mock
import pytest
import structlog
from datetime import datetime
from unittest.mock import call


from .. helpers.fake_llm import FakeLLM

from ...core.pydantic import (
    BaseModel,
    Field,
)
from langchain_core.load.serializable import Serializable
from langgraph.checkpoint.memory import (
    MemorySaver,
)

from langchain_core.runnables.utils import (
    ConfigurableFieldSpec
)
from langchain_core.runnables import (
    RunnableConfig,
)
from langchain_core.messages import (
    AIMessage,
    ToolCall,
)
from ..collaborator import (
    CollaboratorOutputClarification,
    CollaboratorOutputResponse,
    CollaboratorOutputResponseStructured,
    UserMessage,
    ClarificationSimpleMessage,
)
from ..skill import (
    BrainSchemaBase,
    ClarificationSchemaBase,
    ResultSchemaBase,
    Skill,
    SkillComputationDirect,
    SkillComputationWithClarification,
    SkillInputSchemaBase,
    SkillStructuredResponse,
)

from ..brain.brain_types import (
    SituationBuilderFn,
)
from ..agent.agent_base import AgentBase

from ..team import (
    TeamBase,
    SupervisionStrategy,
)

from .crew_base import (
    CrewBase,
    CrewInputFresh,
    CrewInputClarification,
)
from ..helpers.json_serializar_from_custom_models import (
    SERIALIZER_VALID_NAMESPACES,
    JsonSerializarFromCustomModels
)

log = structlog.get_logger()
"Loger para el módulo"


class SumInput(BrainSchemaBase):
    number_1: int
    number_2: int


class SumOutput(ResultSchemaBase):
    result: int


class SingleItemsInput(BaseModel):
    name: str
    description: str


class ListItemsInput(BrainSchemaBase):
    items: List[SingleItemsInput]


class BalanceInput(BrainSchemaBase):
    bank: str = Field(
        ...,
        description="Name of the bank"
    )
    type: Literal[
        'checking',
        'savings'
    ] = Field(
        ...,
        description='account type'
    )


class TransferBrainSchema(
    BrainSchemaBase,
    Serializable
):
    from_account: str
    to_account: str

    @classmethod
    def is_lc_serializable(cls) -> bool:
        return True

    @classmethod
    def get_lc_namespace(cls) -> List[str]:
        return cls.__module__.split(".")

    @classmethod
    def lc_id(cls) -> list[str]:
        # Pydantic generics change the class name.
        # So we need to do the following
        if (
            "origin" in cls.__pydantic_generic_metadata__
            and cls.__pydantic_generic_metadata__["origin"] is not None
        ):
            original_name = cls.__pydantic_generic_metadata__[
                "origin"
            ].__name__
        else:
            original_name = cls.__name__
        return [*cls.get_lc_namespace(), original_name]

    @property
    def lc_attributes(self) -> Dict:
        return {
            "from_account": self.from_account,
            "to_account": self.to_account
        }


class TransferClarification(ClarificationSchemaBase):
    confirmation: Literal['y', 'n']


class TransferInput(SkillInputSchemaBase):
    from_account: str
    to_account: str
    confirmation: Literal['y', 'n']


class TransferOutput(
    ResultSchemaBase,
    Serializable
):
    result: str
    new_balance: int

    @classmethod
    def is_lc_serializable(cls) -> bool:
        return True

    @classmethod
    def get_lc_namespace(cls) -> List[str]:
        return cls.__module__.split(".")

    @property
    def lc_attributes(self) -> Dict:
        return {
            "result": self.result,
            "new_balance": self.new_balance
        }


class SumSkill(
    SkillComputationDirect[
        SumInput,
        SumOutput
    ]
):
    name: str = 'sum'
    description: str = 'given two numbers return the sum of both'

    brain_schema: Type[SumInput] = SumInput
    result_schema: Type[SumOutput] = SumOutput

    @property
    def config_specs(self) -> List[ConfigurableFieldSpec]:
        return [
            ConfigurableFieldSpec(
                id='base_srv_for_sum',
                name='Servicio requerido por el use case',
                description=(
                    'Se utiliza para inicializar el use case'
                ),
                annotation=Any,
                default=...
            )
        ]

    async def async_executor(
        self,
        request: SumInput,
        config: RunnableConfig
    ) -> SumOutput:
        number_1 = request.number_1
        number_2 = request.number_2
        value = SumOutput.model_validate(
            {"result": number_1 + number_2}
        )
        return value


sum_computation = SumSkill()


list_items_computation: Skill = SkillStructuredResponse(
    name='list_items',
    description=(
        'shows a list of items in a structured format for the user \n'
        'use this tool when a user anwser for list of items'
    ),
    brain_schema=ListItemsInput
)


class TransferSkill(
    SkillComputationWithClarification[
        TransferBrainSchema,
        TransferClarification,
        TransferInput,
        TransferOutput,
    ],
):
    name: str = 'transfer'
    description: str = 'transfer money between accounts'
    brain_schema: Type[TransferBrainSchema] = TransferBrainSchema
    result_schema: Type[TransferOutput] = TransferOutput
    skill_input_schema: Type[TransferInput] = TransferInput
    clarification_schema: Type[TransferClarification] = TransferClarification

    @property
    def config_specs(self) -> List[ConfigurableFieldSpec]:
        """List configurable fields for this runnable."""
        return [
            ConfigurableFieldSpec(
                id='base_srv_for_transfer',
                name='Servicio requeridisimo por el use case',
                description=(
                    'Se utiliza para inicializar el use case'
                ),
                annotation=Any,
                default=...
            )
        ]

    async def async_executor(
        self,
        request: TransferInput,
        config: RunnableConfig
    ) -> TransferOutput:
        value = TransferOutput.model_validate(
            {"result": "success", "new_balance": 100}
        )
        return value

    def merge_brain_with_clarification(
        self,
        brain_input: TransferBrainSchema,
        clarification_input: TransferClarification
    ) -> TransferInput:
        input_with_clarification = {
            **brain_input.model_dump(),
            **clarification_input.model_dump()
        }
        result = TransferInput.model_validate(input_with_clarification)
        return result


def situation_builder(input, config):
    return 'keep focus'


tools_availables = [
    sum_computation,
    list_items_computation,
    TransferSkill(),
]


class AgentAdamSmith(AgentBase):
    name: str = 'Adam_Smith'
    job_description: str = 'Expert in Finance and Mathematics'
    options: List[Skill] = tools_availables

class AgentSupervisor(AgentBase):
    name: str = 'Pablo'
    job_description: str = "Select the best team member to answer the user's question"
    options: List[Skill] = []


def create_message(content: str):
    user_message = UserMessage(
        id=datetime.now().isoformat(),
        timestamp=datetime.now().isoformat(),
        content=content
    )
    input = CrewInputFresh(message=user_message)
    return input

@pytest.fixture
def use_cases_srv():
    """Fixture para proveer el falso llm_srv"""
    result = 'aqui viene un servicio'
    # Add finalizer to reset mock after each test
    yield result


@pytest.fixture
def config_fake_llm(use_cases_srv, checkpointer, mocker):
    def real_config(responses, thread_id):
        llm_spy = mocker.spy(FakeLLM, "invoke")
        fake_llm = FakeLLM(messages=iter(responses))
        # Use mocker.patch.object to wrap the method with a spy
        # The 'autospec=True' argument ensures the spy has the same signature as the original method.
        # llm_spy = mocker.patch.object(fake_llm, "invoke", autospec=True)

        config = RunnableConfig(
            configurable={
                "llm_srv": fake_llm,
                # "llm_srv": llm_spyed,
                "use_cases_srv": use_cases_srv,
                "user_name": "Pedrito",
                "today": datetime.now().isoformat(),
                "base_srv_for_transfer": use_cases_srv,
                "base_srv_for_sum": use_cases_srv,
                "checkpointer": checkpointer,
                "thread_id": thread_id
            }
        )
        return config, llm_spy
    return real_config


@pytest.fixture
def checkpointer():
    serde = JsonSerializarFromCustomModels()
    fake_service = MemorySaver(
        serde=serde
    )
    yield fake_service


@pytest.fixture
def team_base():
    agent_finance = AgentAdamSmith()
    agent_supervisor = AgentSupervisor()
    team = TeamBase(
        name='primer_team',
        job_description='Answer user questions',
        distribution_strategy=SupervisionStrategy(
            supervisor=agent_supervisor
        ),
        members=[
            agent_finance,
            agent_supervisor,
        ]
    )
    return team


@pytest.fixture
def crew_base(team_base):
    crew = CrewBase(
        team=team_base
    )
    return crew


# @pytest.mark.only
@pytest.mark.asyncio
async def test_what_is_my_name(crew_base, config_fake_llm):
    input = create_message('hola, cuál es mi nombre?')
    responses = ['tu nombre es Pedrito']
    configuration, llm_spyed = config_fake_llm(responses, thread_id='1111')
    result = await crew_base.ainvoke(input, configuration)
    assert llm_spyed.call_count == 1
    input_llm = llm_spyed.call_args_list[0].args[1]
    # configuration_llm = llm_spyed.call_args_list[0].args[2].get('configurable')
    messages_to_llm = input_llm.messages
    assert isinstance(messages_to_llm, list)
    assert len(messages_to_llm) == 2

    assert isinstance(result, CollaboratorOutputResponse)
    content = result.message.content
    assert 'Pedrito' in content


# @pytest.mark.only
@pytest.mark.asyncio
async def test_remember_previous_message(crew_base, config_fake_llm):
    thread_id = "222222"
    first_message = create_message('hola, ahora estoy en la ciudad de Budapest')
    second_message = create_message('Recuerdas en qué ciudad estoy?')
    first_response = AIMessage(content='Hola, en que puedo ayudarte')
    second_response = AIMessage(content='Estás en Budapest')
    responses = [first_response, second_response]    
    configuration, llm_spyed = config_fake_llm(responses, thread_id)
    result = await crew_base.ainvoke(first_message, configuration)
    assert isinstance(result, CollaboratorOutputResponse)
    result = await crew_base.ainvoke(second_message, configuration)
    assert isinstance(result, CollaboratorOutputResponse)
    content = result.message.content
    assert 'Budapest' in content


# @pytest.mark.only
@pytest.mark.asyncio
async def test_structured_response(crew_base, config_fake_llm):
    input = create_message(content=(
            'Dile a Adam_Smith que quiero ver una lista de los tipos'
            ' de cuenta bancaria que existen?'
        ))
    first_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='send_message_to_colleague',
                id='1', 
                args={'to': 'Adam_Smith', 'from': 'Pablo', 'message': "ayudame con esto"}
            ),
        ]
    )
    second_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='list_items',
                id='1', 
                args={"items": [{"name": "corriente", "description": "cuenta con cheques"}]}
            ),
        ]
    )
    responses = [first_response, second_response]
    config_with_thread, llm_spyed = config_fake_llm(responses=responses, thread_id="3333")
    result = await crew_base.ainvoke(input, config_with_thread)
    assert isinstance(result, CollaboratorOutputResponseStructured)


# @pytest.mark.only
@pytest.mark.asyncio
async def test_clarification_complete(crew_base, config_fake_llm):
    # Hacemos una petición que retorna un clarification request
    input = create_message(content=(
        'Transfiere 25$ de mi cuenta corriente a la de ahorro'
    ))
    first_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='send_message_to_colleague',
                id='1', 
                args={'to': 'Adam_Smith', 'from': 'Pablo', 'message': "ayudame con esto"}
            ),
        ]
    )
    second_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='transfer',
                id='1', 
                args={'from_account': 'corriente', 'to_account': 'ahorro'}
            ),
        ]
    )
    third_response = AIMessage(
        content="Transferencia realizada"
    )
    responses = [first_response, second_response, third_response]
    config_with_thread, llm_spyed = config_fake_llm(responses=responses, thread_id="44444")
    result = await crew_base.ainvoke(input, config_with_thread)
    assert isinstance(result, CollaboratorOutputClarification)
    assert llm_spyed.call_count == 2
    # Respondemos la clarificación
    requested = result.clarification_requested
    message = ClarificationSimpleMessage(
        payload={"confirmation": "y"},
        computation_id=requested.clarification_id,
        timestamp=datetime.now().isoformat(),
        content=""
    )
    input = CrewInputClarification(
        clarification_message=message
    )
    result = await crew_base.ainvoke(input, config_with_thread)
    assert isinstance(result, CollaboratorOutputResponse)


# @pytest.mark.only
@pytest.mark.asyncio
async def test_clarification_non_existent(crew_base, config_fake_llm):
    message = ClarificationSimpleMessage(
        payload={"confirmation": "y"},
        computation_id="2222222222222",
        timestamp=datetime.now().isoformat(),
        content=""
    )
    input = CrewInputClarification(
        clarification_message=message
    )
    config_with_thread, llm_spyed = config_fake_llm(responses=[], thread_id="55555")
    with pytest.raises(ValueError) as exc_info:
        await crew_base.ainvoke(input, config_with_thread)
    assert str(exc_info.value).startswith('There is no clarification')


# @pytest.mark.only
@pytest.mark.asyncio
async def test_stream_what_is_my_name(crew_base, config_fake_llm):
    input = create_message(content='hola, cuál es mi nombre?')
    thread_id = "11111"
    responses = ['tu nombre es Pedrito']
    configuration, llm_spyed = config_fake_llm(responses, thread_id)
    events = []
    async for event in crew_base.astream_events(
        input,
        config=configuration,
        version="v2",
    ):
        events.append(event)
    assert len(events) > 4
    last_event = events[-1]
    assert last_event.get('event') == 'on_chain_end'
    result = last_event.get('data', {}).get('output')
    assert isinstance(result, CollaboratorOutputResponse)
    content = result.message.content
    assert 'Pedrito' in content
