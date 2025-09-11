from datetime import datetime
import json
from typing import Any
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
import pytest
from fastapi.testclient import TestClient
import structlog

from ..agent.agent_base import AgentBase
from ..crew.crew_base import CrewBase
from ..team.distribution_strategy import SupervisionStrategy
from ..team.team_base import TeamBase
from .crew_router_base import (
    CrewRouterBase,
)
from .auth import (
    PublicAccessStrategy,
)
from langchain_community.chat_models.fake import FakeListChatModel

from .crew_settings import CrewSettings

log = structlog.get_logger()
"Loger para el módulo"

class FakeLLM(FakeListChatModel):
    def bind_tools(
            self,
            tools: Any,
            **kwargs: Any,
    ):
        return self


class AgentTests(AgentBase):
    name: str = 'Cervantes'
    job_description: str = '''
    Answer questions about literature
    '''

@pytest.fixture
def team_base():
    agent_tests = AgentTests()
    team = TeamBase(
        name='primer_team',
        job_description='Answer user questions',
        distribution_strategy=SupervisionStrategy(
            supervisor=agent_tests
        ),
        members=[
            agent_tests,
        ]
    )
    return team

@pytest.fixture
def fake_llm():
    fake_llm = FakeLLM(responses=["Hola, welcome a crewmaster!"])
    yield fake_llm


@pytest.fixture
def reset_sse_starlette_appstatus_event():
    """
    Fixture that resets the appstatus event in the sse_starlette app.

    Should be used on any test that uses sse_starlette to stream events.
    """
    # See https://github.com/sysid/sse-starlette/issues/59
    from sse_starlette.sse import AppStatus

    AppStatus.should_exit_event = None

@pytest.fixture
def build_settings():
    settings = CrewSettings(
        llm_api_key_open_ai="12345678900",
        llm_model_open_ai="fake_model",
    )
    yield settings


@pytest.fixture
def crew_base(team_base):
    crew = CrewBase(
        team=team_base
    )
    return crew


@pytest.fixture
def setup_router(fake_llm, build_settings, crew_base):
    router = CrewRouterBase(
        runnable=crew_base,
        settings=build_settings,
        auth_strategy=PublicAccessStrategy(),
        llm=fake_llm
    )
    yield router.fastapi_router

@pytest.fixture
def build_metadata():
    def _config_metadata(thread_id: str):
        return {
            "thread_id": thread_id
        }
    yield _config_metadata

@pytest.fixture
def http_client(
    setup_router,
    reset_sse_starlette_appstatus_event
):
    client = TestClient(
        app=setup_router
    )
    yield client

@pytest.mark.asyncio
async def test_stream_simple_fresh(
    http_client,
    build_metadata,
):
    user_message = {
        "id": "2222",
        "timestamp": datetime.now().isoformat(),
        "content": "hola"
    }
    user_input = {
        "type": "http.input.fresh",
        "message": user_message
    }
    thread_id = "11111"
    metadata = build_metadata(thread_id)
    event_filter = {
        "scope": 'answer',
        "moments": ['end'],
        "format": 'compact'
    }
    data = {
        "data": user_input,
        "metadata": metadata,
        "event_filter": event_filter
    }
    serialized = json.dumps(data)
    headers = {"Authorization": "churrinPeladinDeTokencin"}
    response = http_client.post(
        "/crew_events",
        data=serialized,
        headers=headers
    )
    assert response.status_code == 200
    assert 'event: error' not in response.text
    assert 'event: data' in response.text
    assert 'event: end' in response.text
    assert 'welcome a crewmaster' in response.text
