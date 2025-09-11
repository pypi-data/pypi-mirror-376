from abc import abstractmethod
from unittest.mock import create_autospec

from typing import (
    List,
    Literal,
    Optional,
    Type,
)
import pytest
import structlog
from datetime import datetime

from langchain_core.messages import (
    AIMessage,
    ToolCall,
)
from langchain_core.runnables.utils import (
    ConfigurableFieldSpec
)
from langchain_core.runnables import (
    RunnableConfig,
)

from ..helpers.fake_llm import FakeLLM

from ...core.pydantic import (
    BaseModel,
)

from ..collaborator import (
    CollaboratorInputFresh,
    CollaboratorInputClarification,
    CollaboratorOutputResponse,
    CollaboratorOutputClarification,
    CollaboratorOutputResponseStructured,
    CollaboratorOutputContribution,
    ClarificationContext,
    UserMessage,
    ClarificationMessage,
)
from ..skill import (
    Skill,
    BrainSchemaBase,
    ResultSchemaBase,
    ClarificationSchemaBase,
    SkillComputationWithClarification,
    SkillComputationDirect,
    SkillStructuredResponse,
    SkillContribute,
    ComputationRequested,
)
from ..brain.brain_types import (
    InstructionsTransformerFn,
    SituationBuilderFn,
)
from .agent_base import AgentBase

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


class TransferBrainSchema(BrainSchemaBase):
    from_account: str
    to_account: str


class TransferClarification(ClarificationSchemaBase):
    confirmation: Literal['y', 'n']


class TransferInput(BrainSchemaBase):
    from_account: str
    to_account: str
    confirmation: Literal['y', 'n']


class TransferOutput(ResultSchemaBase):
    result: str
    new_balance: int


class SumSkillRepositoryPort:
    @abstractmethod
    def sumar(x, y) -> int:
        ...


class SumSkill(
    SkillComputationDirect[SumInput, SumOutput]
):
    name: str = 'sum'
    description: str = 'given two numbers return the sum of both'

    brain_schema: Type[SumInput] = SumInput
    result_schema: Type[SumOutput] = SumOutput

    @property
    def config_specs(self) -> List[ConfigurableFieldSpec]:
        return [
            ConfigurableFieldSpec(
                id='repository_srv',
                name='Servicio requerido por el use case',
                description=(
                    'Se utiliza para inicializar el use case'
                ),
                annotation=SumSkillRepositoryPort,
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
        value = SumOutput.parse_obj(
            {"result": number_1 + number_2}
        )
        return value


list_items_computation: Skill = SkillStructuredResponse(
    name='list_items',
    description=(
        'shows a list of items in a structured format for the user \n'
        'use this tool when a user anwser for list of items'
    ),
    brain_schema=ListItemsInput
)


class TransferSkillRepositoryPort:
    @abstractmethod
    def transfer(x, y) -> int:
        ...


class TransferSkill(
    SkillComputationWithClarification[
        TransferInput,
        TransferClarification,
        TransferInput,
        TransferOutput
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
                id='repository_srv',
                name='Servicio requeridisimo por el use case',
                description=(
                    'Se utiliza para inicializar el use case'
                ),
                annotation=TransferSkillRepositoryPort,
                default=...
            )
        ]

    async def async_executor(
        self,
        request: TransferInput,
        config: RunnableConfig
    ) -> TransferOutput:
        value = TransferOutput.parse_obj(
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




skills_availables = [
    list_items_computation,
    SkillContribute(),
    SumSkill(),
    TransferSkill(),
]


class AgentFake(AgentBase):
    name: str = 'Adam_Smith'
    job_description: str = '''
    You are a super agent 86
    '''
    options: List[Skill] = skills_availables


def situation_builder(input, config):
    return 'keep focus'

def instructions_transformer(input, config):
    return 'super transformada'

class AgentFakeTransformer(AgentFake):
    """Agente para probar las funciones de transformacion"""
    situation_builder: Optional[SituationBuilderFn] = situation_builder
    instructions_transformer: Optional[InstructionsTransformerFn] = instructions_transformer


def create_message(content: str):
    user_message = UserMessage(
        id='1222',
        timestamp=datetime.now().isoformat(),
        content=content
    )
    input = CollaboratorInputFresh(message=user_message)
    return input

@pytest.fixture
def repository_incomplete_srv():
    """Fixture para proveer el falso repository_srv"""
    # Creamos una clase que tiene sólo uno de los los puertos requeridos
    # Faltaría el de transfer para estar completo
    class RepositoryPort(TransferSkillRepositoryPort):
        pass

    fake_service = create_autospec(
        spec=RepositoryPort,
        instance=True
    )
    # Add finalizer to reset mock after each test
    yield fake_service
    # Cleanup: resetear el mock para el próximo test
    fake_service.reset_mock()


@pytest.fixture
def repository_srv():
    """Fixture para proveer el falso repository_srv"""
    # Creamos una clase que tiene todos los puertos requeridos
    # por los skills en sus config_specs
    class RepositoryPort(SumSkillRepositoryPort, TransferSkillRepositoryPort):
        pass

    fake_service = create_autospec(
        spec=RepositoryPort,
        instance=True
    )
    # Add finalizer to reset mock after each test
    yield fake_service
    # Cleanup: resetear el mock para el próximo test
    fake_service.reset_mock()


@pytest.fixture
def config_fake_llm(repository_srv):
    def real_config(responses, user_name: str = 'Pedrito'):
        return RunnableConfig(
            configurable={
                "llm_srv": FakeLLM(messages=iter(responses)),
                "repository_srv": repository_srv,
                "user_name": user_name,
                "today": datetime.now().isoformat(),
            },
            recursion_limit=10
        )
    return real_config

@pytest.fixture
def config_incomplete(repository_incomplete_srv):
    return RunnableConfig(
        configurable={
            "llm_srv": FakeLLM(messages=iter([])),
            "repository_srv": repository_incomplete_srv,
            "user_name": 'Pedrito',
            "today": datetime.now().isoformat(),
        },
        recursion_limit=10
    )


# @pytest.mark.only
@pytest.mark.asyncio
async def test_repository_incomplete(config_incomplete):
    agent = AgentFake()
    input = create_message(content='hola, sabes cuál es mi nombre?')
    with pytest.raises(ValueError) as exc_info:
        await agent.ainvoke(input, config_incomplete)
    assert 'should be an instance of RepositorySrvProtocol' in str(
        exc_info.value
    )


# @pytest.mark.only
@pytest.mark.asyncio
async def test_hello(config_fake_llm):
    agent = AgentFake()
    input = create_message(content='hola, sabes cuál es mi nombre?')
    result = await agent.ainvoke(input, config_fake_llm(['Tu nombre es Pedrito'], 'Pedrito'))
    assert isinstance(result, CollaboratorOutputResponse)
    content = result.message.content
    assert 'Pedrito' in content


@pytest.mark.only
@pytest.mark.asyncio
async def test_computation_required(config_fake_llm):
    agent = AgentFake()
    input = create_message(content='cuánto es 20 + 14?')
    first_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='sum',
                id='1', 
                args={'number_1': 20, 'number_2': 14}
            ),
        ]
    )
    second_response=AIMessage(
        content="El resultado es 34"
    )
    responses = [first_response, second_response]
    result = await agent.ainvoke(input, config_fake_llm(responses, 'Pedrito'))
    assert isinstance(result, CollaboratorOutputResponse)
    assert '34' in result.message.content


# @pytest.mark.only
@pytest.mark.asyncio
async def test_clarification_required(config_fake_llm):
    agent = AgentFake()
    input = create_message(content='Haz una transferencia de 25$ de mi cuenta corriente a la de ahorro')
    first_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='transfer',
                id='1', 
                args={'from_account': 'corriente', 'to_account': 'ahorro'}
            ),
        ]
    )
    messages = [first_response]
    result = await agent.ainvoke(input, config_fake_llm(messages))
    assert isinstance(result, CollaboratorOutputClarification)
    assert result.clarification_requested.name == 'transfer'


# @pytest.mark.only
@pytest.mark.asyncio
async def test_response_structured(config_fake_llm):
    agent = AgentFake()
    input = create_message(content=(
            'Quiero ver una lista de los tipos'
            ' de cuenta bancaria que existen'))
    first_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='list_items',
                id='1', 
                args={"items": [{"name": "corriente", "description": "cuenta con cheques"}]}
            ),
        ]
    )
    messages = [first_response]
    result = await agent.ainvoke(input, config_fake_llm(messages))
    assert isinstance(result, CollaboratorOutputResponseStructured)
    content_normalized = result.message.content.replace("'", '"')
    list_parsed = ListItemsInput.model_validate_json(content_normalized)
    assert list_parsed.items[0].name == 'corriente'



# @pytest.mark.only
@pytest.mark.asyncio
async def test_contribution(config_fake_llm):
    agent = AgentFake()
    input = create_message(content='quién escribió la novela 100 martirios insoportables')
    first_response = AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name='send_message_to_colleague',
                id='1', 
                args={'to': 'cervantes', 'from': 'Adam_Smith', 'message': "ayudame con esto"}
            ),
        ]
    ) 
    responses = [first_response]
    result = await agent.ainvoke(input, config_fake_llm(responses))
    assert isinstance(result, CollaboratorOutputContribution)
    assert result.contribution.to == 'cervantes'
    assert result.contribution.author == 'Adam_Smith'


# @pytest.mark.only
@pytest.mark.asyncio
async def test_handle_clarification_response(config_fake_llm):
    agent = AgentFake()
    transfer_request = ComputationRequested(
        name='transfer',
        brain_args={
            "from_account": "corriente",
            "to_account": "ahorro",
        },
        computation_id='122222'
    )
    context = ClarificationContext(
        computations_requested=[transfer_request],
        computations_results=[],
        requested_by="Adam_Smith"
    )
    message = ClarificationMessage(
        to='Adam_Smith',
        payload={"confirmation": "y"},
        clarification_context=context,
        timestamp=datetime.now().isoformat(),
        computation_id='122222',
        content=''
    )
    input = CollaboratorInputClarification(
        clarification_message=message
    )
    first_response = AIMessage(
        content="Transferencia realizada"
    )
    responses = [first_response]
    result = await agent.ainvoke(input, config_fake_llm(responses))
    assert isinstance(result, CollaboratorOutputResponse)


# @pytest.mark.only
@pytest.mark.asyncio
async def test_stream_hello(config_fake_llm):
    agent = AgentFake()
    input = create_message(content='hola, sabes cuál es mi nombre?')
    responses = ['Tu nombre es Pedrito']
    events = []
    async for event in agent.astream_events(
        input,
        config=config_fake_llm(responses, 'Pedrito'),
        version="v2",
    ):
        events.append(event)

    last_event = events[-1]
    assert last_event.get('event') == 'on_chain_end'
    result = last_event.get('data', {}).get('output')
    assert isinstance(result, CollaboratorOutputResponse)
    content = result.message.content
    assert 'Pedrito' in content


# @pytest.mark.only
@pytest.mark.asyncio
async def test_instructions_transformer_passed_to_brain(config_fake_llm):
    agent = AgentFakeTransformer()
    brain = agent._brain
    instructions_transformer_fn = brain.instructions_transformer
    assert callable(instructions_transformer_fn) == True
    transformed = brain.instructions_transformer('prueba', config_fake_llm([]))
    assert transformed == 'super transformada'


# @pytest.mark.only
@pytest.mark.asyncio
async def test_situation_builder_passed_to_brain(config_fake_llm):
    agent = AgentFakeTransformer()
    brain = agent._brain
    situation_builder_fn = brain.situation_builder
    assert callable(situation_builder_fn) == True
    transformed = brain.situation_builder('prueba', config_fake_llm([]))
    assert transformed == 'keep focus'