from typing import Any, Dict
import pytest
from unittest.mock import AsyncMock, patch

from ...skill.skill_computation import (
    SkillComputationDirect,
    SkillComputationWithClarification,
)
from ...skill.types import (
    BrainSchemaBase,
    ResultSchemaBase,
    ClarificationSchemaBase,
)
from langchain_core.runnables import (
    RunnableConfig,
)
from ..muscle_types import (
    ComputationRequested,
    ComputationResult,
    ClarificationRequested,
    ClarificationContext,
    MuscleOutputClarification,
    MuscleOutputResults,
)
from .execute_computations_pending import (
    execute_computations_pending,
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


class DummyWithClarification(SkillComputationWithClarification):
    name: str = "clarify-skill"
    brain_args: Dict[str, Any] = dict
    clarification_args: Dict[str, Any] = dict
    computation_id: str = '22222'
    description: str = ''
    brain_schema: FakeBrainSchema = FakeBrainSchema()
    result_schema: FakeResultSchema = FakeResultSchema()
    clarification_schema: FakeClarificationSchema = FakeClarificationSchema()
    skill_input_schema: FakeClarificationSchema = FakeClarificationSchema()

    async def async_executor(self, input, config):
        pass

    async def merge_brain_with_clarification(self, brain_input, clarification_input):
        pass

    async def ainvoke(self, input, config):
        pass


@pytest.mark.asyncio
async def test_empty_pending_returns_existing_results():
    results = [ComputationResult(computation_id="1", name="test", skill_args={}, result={})]
    config = RunnableConfig()

    output = await execute_computations_pending(
        pending=[],
        results=results,
        skills=[],
        agent_name="agent-1",
        config=config
    )

    assert isinstance(output, MuscleOutputResults)
    assert output.computations_requested == []
    assert output.computations_results == results


@pytest.mark.asyncio
async def test_clarification_branch_triggered():
    pending = [
        ComputationRequested(
            name="clarify-skill",
            brain_args={"foo": "bar"},
            computation_id="c1"
        )
    ]
    results = []
    skills = [DummyWithClarification()]
    config = RunnableConfig()

    output = await execute_computations_pending(
        pending=pending,
        results=results,
        skills=skills,
        agent_name="agent-xyz",
        config=config
    )

    assert isinstance(output, MuscleOutputClarification)
    assert isinstance(output.clarification_requested, ClarificationRequested)
    assert output.clarification_requested.name == "clarify-skill"
    assert output.clarification_requested.brain_args == {"foo": "bar"}
    assert isinstance(output.clarification_context, ClarificationContext)
    assert output.clarification_context.computations_requested == pending
    assert output.clarification_context.requested_by == "agent-xyz"


@pytest.mark.asyncio
async def test_direct_computations_only_calls_execute_computation():
    pending = [
        ComputationRequested(
            name="direct-skill",
            brain_args={"a": 1},
            computation_id="c1"
        ),
        ComputationRequested(
            name="direct-skill",
            brain_args={"b": 2},
            computation_id="c2"
        )
    ]
    results = [ComputationResult(computation_id="prev", name="old", skill_args={}, result={})]
    config = RunnableConfig()
    skill = DummyDirect()

    mock_result_1 = ComputationResult(
        computation_id="c1",
        name="direct-skill",
        skill_args={},
        result=FakeResultSchema(response="all is good")
    )
    mock_result_2 = ComputationResult(
        computation_id="c2",
        name="direct-skill",
        skill_args={},
        result=FakeResultSchema(response="will be fine")
    )

    with patch(
        "crewmaster.features.muscle.helpers.execute_computations_pending.execute_computation",
        new=AsyncMock(side_effect=[mock_result_1, mock_result_2])
    ) as mock_exec:
        output = await execute_computations_pending(
            pending=pending,
            results=results,
            skills=[skill],
            agent_name="agent-abc",
            config=config
        )

    assert isinstance(output, MuscleOutputResults)
    assert output.computations_requested == []
    assert len(output.computations_results) == 3  # two new + one old
    assert mock_result_1 in output.computations_results
    assert mock_result_2 in output.computations_results
    # Ensure execute_computation called twice
    assert mock_exec.await_count == 2


@pytest.mark.asyncio
async def test_mixed_options_prioritizes_clarification():
    pending = [
        ComputationRequested(
            name="clarify-skill",
            brain_args={},
            computation_id="1"
        ),
        ComputationRequested(
            name="direct-skill",
            brain_args={},
            computation_id="2"
        ),
    ]
    results = []
    skills = [DummyWithClarification(), DummyDirect()]
    config = RunnableConfig()

    output = await execute_computations_pending(
        pending=pending,
        results=results,
        skills=skills,
        agent_name="agent-priority",
        config=config
    )

    assert isinstance(output, MuscleOutputClarification)
    assert output.clarification_requested.name == "clarify-skill"


@pytest.mark.asyncio
async def test_config_passed_to_execute_computation():
    pending = [
        ComputationRequested(name="direct-skill", brain_args={}, computation_id="x1")
    ]
    results = []
    config = RunnableConfig(tags=["test-tag"])
    skill = DummyDirect()

    mock_result_1 = ComputationResult(computation_id="c1", name="direct-skill", skill_args={}, result=FakeResultSchema(response="all is good"))


    with patch(
        "crewmaster.features.muscle.helpers.execute_computations_pending.execute_computation",
        new=AsyncMock(side_effect=[mock_result_1])
    ) as mock_exec:
        await execute_computations_pending(
            pending=pending,
            results=results,
            skills=[skill],
            agent_name="agent-test",
            config=config
        )

    # Verify that config passed is exactly the one provided
    called_args, called_kwargs = mock_exec.await_args
    assert called_kwargs["config"] == config
