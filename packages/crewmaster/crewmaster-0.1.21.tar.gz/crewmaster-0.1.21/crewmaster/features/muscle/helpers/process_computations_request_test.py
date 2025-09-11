from typing import Any, Dict
import pytest
from unittest.mock import AsyncMock, patch

from langchain_core.runnables import RunnableConfig

from .process_computations_request import (
    process_computations_request,
)
from ..muscle_types import (
    MuscleInputComputationRequested,
    ComputationRequested,
)
from ...skill.types import (
    BrainSchemaBase,
    ResultSchemaBase,
    ClarificationSchemaBase,
)
from ...skill.skill_computation import (
    SkillComputationDirect,
)

class FakeBrainSchema(BrainSchemaBase):
    prop: str = ''


class FakeResultSchema(ResultSchemaBase):
    response: str = ''


class FakeClarificationSchema(ClarificationSchemaBase):
    prop: str = ''


class DummyDirect(SkillComputationDirect):
    name: str = "direct-skill"
    brain_args: Dict[str, Any] = dict
    clarification_args: Dict[str, Any] = dict
    computation_id: str = '22222'
    description: str = ''
    brain_schema: FakeBrainSchema = FakeBrainSchema()
    result_schema: FakeResultSchema = FakeResultSchema()

    async def async_executor(self, input, config):
        pass

    async def ainvoke(self, input, config):
        pass

@pytest.mark.asyncio
async def test_process_computations_request_calls_execute_computations_pending():
    # Arrange
    fake_skills = [DummyDirect(), DummyDirect()]
    fake_requested = ComputationRequested(
            name="dummy-skill",
            brain_args={"foo": "bar"},
            computation_id="c1"
        )
    fake_pending = [fake_requested]
    fake_config = RunnableConfig(tags=["x"])
    fake_agent = "agent007"

    fake_input = MuscleInputComputationRequested(
        computations_required=fake_pending
    )

    expected_output = {"status": "ok"}

    # Patch execute_computations_pending in the module where process_computations_request is defined
    with patch(
        "crewmaster.features.muscle.helpers.process_computations_request.execute_computations_pending",
        new=AsyncMock(return_value=expected_output),
    ) as mock_exec:
        # Act
        result = await process_computations_request(
            skills=fake_skills,
            input=fake_input,
            config=fake_config,
            agent_name=fake_agent,
        )

        # Assert
        assert result == expected_output
        mock_exec.assert_awaited_once_with(
            pending=fake_pending,
            results=[],
            skills=fake_skills,
            agent_name=fake_agent,
            config=fake_config,
        )


@pytest.mark.asyncio
async def test_process_computations_request_passes_empty_pending():
    # Arrange
    fake_skills = []
    fake_pending = []
    fake_config = RunnableConfig(tags=["empty"])
    fake_agent = "agent-null"

    fake_input = MuscleInputComputationRequested(
        computations_required=fake_pending
    )
    expected_output = {"no": "jobs"}

    with patch(
        "crewmaster.features.muscle.helpers.process_computations_request.execute_computations_pending",
        new=AsyncMock(return_value=expected_output),
    ) as mock_exec:
        # Act
        result = await process_computations_request(
            skills=fake_skills,
            input=fake_input,
            config=fake_config,
            agent_name=fake_agent,
        )

        # Assert
        assert result == expected_output
        mock_exec.assert_awaited_once_with(
            pending=fake_pending,
            results=[],
            skills=fake_skills,
            agent_name=fake_agent,
            config=fake_config,
        )
