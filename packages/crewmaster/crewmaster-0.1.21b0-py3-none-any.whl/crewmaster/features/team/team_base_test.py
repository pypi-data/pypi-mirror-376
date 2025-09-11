import os
from typing import (
    Any,
    List,
    Literal,
    Optional,
    Type,
)
import pytest
import structlog
from datetime import datetime
from langchain_core.runnables import (
    RunnableConfig,
)
from langchain_core.runnables.utils import (
    ConfigurableFieldSpec
)

from langchain_core.messages import (
    AIMessage,
    ToolCall,
)

from ..helpers.fake_llm import FakeLLM

from ...core.pydantic import (
    BaseModel,
    SecretStr,
    Field,
)
from ..collaborator import (
    ClarificationContext,
    ClarificationMessage,
    CollaboratorInputClarification,
    CollaboratorInputFresh,
    CollaboratorOutputClarification,
    CollaboratorOutputResponse,
    CollaboratorOutputResponseStructured,
    UserMessage,
)
from ..skill import (
    BrainSchemaBase,
    ClarificationSchemaBase,
    ResultSchemaBase,
    SkillInputSchemaBase,
    ComputationRequested,
    Skill,
    SkillComputationDirect,
    SkillComputationWithClarification,
    SkillStructuredResponse,
)
from ..brain.brain_types import (
    SituationBuilderFn,
)
from ..agent.agent_base import AgentBase

from .team_base import TeamBase
from .distribution_strategy import SupervisionStrategy

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


class TransferInput(SkillInputSchemaBase):
    from_account: str
    to_account: str
    confirmation: Literal['y', 'n']


class TransferOutput(ResultSchemaBase):
    result: str
    new_balance: int


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
        value = SumOutput.parse_obj(
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


class TransferSKill(
    SkillComputationWithClarification[
        TransferBrainSchema,
        TransferClarification,
        TransferInput,
        TransferOutput
    ]
):
    name: str = 'transfer'
    description: str = 'transfer money between accounts'
    brain_schema: Type[TransferBrainSchema] = TransferBrainSchema
    result_schema: Type[TransferOutput] = TransferOutput
    skill_input_schema: Type[TransferInput] = TransferInput
    clarification_schema: Type[TransferClarification] = TransferClarification

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
            **brain_input.dict(),
            **clarification_input.dict()
        }
        result = TransferInput.parse_obj(input_with_clarification)
        return result


def situation_builder(input, config):
    return 'keep focus'


tools_availables = [
    sum_computation,
    list_items_computation,
    TransferSKill(),
]


class AgentAdamSmith(AgentBase):
    name: str = 'Adam_Smith'
    job_description: str = 'Expert in Finance and Mathematics'

    public_bio: str = '''
    If the question is about Finance and Mathematics, you handle the answer
    using the tools at your disposition to give the most accurate answer.
    '''

    options: List[Skill] = tools_availables
    situation_builder: Optional[SituationBuilderFn] = situation_builder



class AgentSupervisor(AgentBase):
    name: str = 'Pablo'
    job_description: str = '''
    Select the best team member to answer the user's question
    '''

    public_bio: str = '''
    You are a agent who work in a team trying to answer the questions
    from {user_name}.

    If the questions can be answered by other expert in the team
    use the tool send_message_to_colleague to ask for help.

    '''
    options: List[Skill] = []


def create_message(content: str):
    user_message = UserMessage(
        id='1222',
        timestamp=datetime.now().isoformat(),
        content=content
    )
    input = CollaboratorInputFresh(message=user_message)
    return input

@pytest.fixture
def use_cases_srv():
    """Fixture para proveer el falso llm_srv"""
    result = 'aqui viene un servicio'
    # Add finalizer to reset mock after each test
    yield result

@pytest.fixture
def config_fake_llm(use_cases_srv):
    def real_config(responses):
        config = RunnableConfig(
            configurable={
                "llm_srv": FakeLLM(messages=iter(responses)),
                "use_cases_srv": use_cases_srv,
                "user_name": "Pedrito",
                "today": datetime.now().isoformat(),
                "base_srv_for_transfer": use_cases_srv,
                "base_srv_for_sum": use_cases_srv,
            }
        )
        return config
    return real_config



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


# @pytest.mark.only
@pytest.mark.asyncio
async def test_what_is_my_name(team_base, config_fake_llm):
    input = create_message('hola, cuál es mi nombre?')
    responses = ['tu nombre es Pedrito']
    result = await team_base.ainvoke(input, config_fake_llm(responses))
    assert isinstance(result, CollaboratorOutputResponse)
    content = result.message.content
    assert 'Pedrito' in content


# @pytest.mark.only
@pytest.mark.asyncio
async def test_sum_with_tool(team_base, config_fake_llm):
    input = create_message((
            'una duda de matemáticas, '
            'utilizando el tool llamado "sum", '
            'cuánto es 20 + 14?'
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
                name='sum',
                id='1', 
                args={'number_1': 20, 'number_2': 14}
            ),
        ]
    )

    third_response = AIMessage(
        content="El resultado es 34"
    )
    responses = [first_response, second_response, third_response]
    result = await team_base.ainvoke(input, config_fake_llm(responses))
    assert isinstance(result, CollaboratorOutputResponse)
    content = result.message.content
    assert '34' in content


# @pytest.mark.only
@pytest.mark.asyncio
async def test_response_structured(team_base, config_fake_llm):
    input = create_message((
            'Dile a AdamSmith que Quiero ver una lista de los tipos'
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
    result = await team_base.ainvoke(input, config_fake_llm(responses))
    assert isinstance(result, CollaboratorOutputResponseStructured)
    structure = result.structure
    assert structure == 'list_items'


# @pytest.mark.only
@pytest.mark.asyncio
async def test_clarification_request(team_base, config_fake_llm):
    input = create_message((
            'Usando tool "transfer_money" Haz una transferencia de 25$  '
            ' de mi cuenta corriente a mi cuenta de ahorro'
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
    responses = [first_response, second_response]

    result = await team_base.ainvoke(input, config_fake_llm(responses))
    assert isinstance(result, CollaboratorOutputClarification)


# @pytest.mark.only
@pytest.mark.asyncio
async def test_handle_clarification_response(team_base, config_fake_llm):
    initial_request = UserMessage(
        id='111111',
        timestamp=datetime.now().isoformat(),
        content=(
            'Usando tool "transfer_money" Haz una transferencia de 30$  '
            ' de mi cuenta corriente a mi cuenta de ahorro'
        )
    )
    transfer_request = ComputationRequested(
        name='transfer',
        brain_args={
            "from_account": "corriente",
            "to_account": "ahorro"
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
        clarification_message=message,
        public_messages=[initial_request]
    )
    first_response = AIMessage(
        content="Transferencia realizada"
    )
    responses = [first_response]
    result = await team_base.ainvoke(input, config_fake_llm(responses))
    assert isinstance(result, CollaboratorOutputResponse)


# @pytest.mark.only
@pytest.mark.asyncio
async def test_stream_what_is_my_name(team_base, config_fake_llm):
    input = create_message('hola, cuál es mi nombre?')    
    responses = ['Tu nombre es Pedrito']
    events = []
    async for event in team_base.astream_events(
        input,
        config=config_fake_llm(responses),
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
