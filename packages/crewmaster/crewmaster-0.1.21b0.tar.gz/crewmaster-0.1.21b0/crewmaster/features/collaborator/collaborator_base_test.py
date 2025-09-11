import os
import pytest
import structlog
from datetime import datetime

from langchain_core.runnables import (
    RunnableConfig,
)
from langchain_openai import ChatOpenAI
from langgraph.graph.state import (
    StateGraph,
)
from ..helpers.fake_llm import FakeLLM

from ...core.pydantic import (
    SecretStr,
    BaseModel,
)

from .collaborator_input import (
    CollaboratorInputFresh,
)
from .collaborator_ouput import (
    CollaboratorOutputResponse,
)
from .state import (
    CollaboratorState,
)

from .collaborator_base import CollaboratorBase
from .team_membership import (
    TeamMembership,
)
from .message import (
    UserMessage,
    AgentMessage,
)


log = structlog.get_logger()
"Loger para el módulo"

class CollabFake(CollaboratorBase):
    name: str = "raul_collaborator"
    job_description: str = "Probar que todo esté bien"

    def join_team(
        self,
        team_membership: TeamMembership
    ):
        pass

    def _build_graph(
        self,
        graph: StateGraph,
        config_parsed: BaseModel,
        config_raw: RunnableConfig,
    ):
        def executor(input: CollaboratorState):
            output = CollaboratorOutputResponse(
                message=AgentMessage(
                    content="Hola, todo bien por aqui",
                    to="User",
                    author="SuperAgent"
                )
            )
            return {
                "output": output
            }
        graph.add_node(executor)
        graph.set_entry_point('executor')
        return graph


@pytest.fixture
def use_cases_srv():
    """Fixture para proveer el falso llm_srv"""
    result = 'aqui viene un servicio'
    # Add finalizer to reset mock after each test
    yield result


@pytest.fixture
def config_fake_llm(use_cases_srv, user_name: str = 'Pedrito'):
    def real_config(responses):
        config = RunnableConfig(
            configurable={
                "llm_srv": FakeLLM(messages=iter(responses)),
                "use_cases_srv": use_cases_srv,
                "user_name": user_name,
                "today": datetime.now().isoformat(),
            }
        )
        return config
    return real_config

# @pytest.mark.only
@pytest.mark.asyncio
async def test_hello(config_fake_llm):
    collab = CollabFake()
    message = UserMessage(
        id='1222',
        timestamp=datetime.now().isoformat(),
        content='hola'
    )
    input = CollaboratorInputFresh(
        message=message
    )
    responses = ['Hola, Pedrito']
    result = await collab.ainvoke(input, config_fake_llm(responses))
    assert isinstance(result, CollaboratorOutputResponse)


# @pytest.mark.only
@pytest.mark.asyncio
async def test_stream_hello(config_fake_llm):
    collab = CollabFake()
    message = UserMessage(
        id='1222',
        timestamp=datetime.now().isoformat(),
        content='hola'
    )
    input = CollaboratorInputFresh(
        message=message
    )
    responses = ['Hola, Pedrito']
    events = []
    async for event in collab.astream_events(
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
