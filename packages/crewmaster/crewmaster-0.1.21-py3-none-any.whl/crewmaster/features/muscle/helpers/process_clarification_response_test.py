import pytest
from unittest.mock import AsyncMock, patch
from langchain_core.runnables import RunnableConfig

from ...skill import (
    ComputationRequestedWithClarification,
    ComputationRequested,
    SkillComputationWithClarification,
)
from ..muscle_types import (
    MuscleInputClarificationResponse,
    ClarificationMessage,
    ClarificationContext,
    MuscleOutput,
)
from .process_clarification_response import (
    process_clarification_response,
)


class DummySkill(SkillComputationWithClarification):
    """Minimal concrete subclass for testing."""
    name: str = "skill1"
    brain_args: dict = {}
    clarification_args: dict = {}
    computation_id: str = "comp-1"
    description: str = ""
    brain_schema: dict = {}
    result_schema: dict = {}
    clarification_schema: dict = {}
    skill_input_schema: dict = {}

    async def async_executor(self, *a, **kw):
        pass

    async def merge_brain_with_clarification(self, *a, **kw):
        pass


@pytest.mark.asyncio
async def test_raises_if_no_matching_computation_id():
    skill = DummySkill()
    context = ClarificationContext(
        computations_requested=[],  # No pending jobs
        computations_results=[],
        requested_by="agent-x"
    )
    message = ClarificationMessage(
        clarification_context=context,
        clarification_id="clarif-1",
        computation_id="not-found",
        payload={"key": "val"},
        content='',
        to='pablo',
        timestamp='2025-09-09'
    )
    input_data = MuscleInputClarificationResponse(clarification_message=message)
    config = RunnableConfig()

    with pytest.raises(ValueError, match="Clarification received is not expected"):
        await process_clarification_response(
            skills=[skill],
            input=input_data,
            config=config,
            agent_name="agent-x"
        )


@pytest.mark.asyncio
async def test_raises_if_no_matching_skill():
    # Prepare a pending computation but no matching SkillComputationWithClarification
    pending = [
        ComputationRequested(
            name="skill1",
            brain_args={},
            clarification_args={},
            computation_id="comp-1"
        )
    ]
    context = ClarificationContext(
        computations_requested=pending,
        computations_results=[],
        requested_by="agent-x"
    )
    message = ClarificationMessage(
        clarification_context=context,
        clarification_id="clarif-1",
        computation_id="comp-1",
        payload={"key": "val"},
        content='',
        to='pablo',
        timestamp='2025-09-09'
    )
    input_data = MuscleInputClarificationResponse(clarification_message=message)
    config = RunnableConfig()

    with pytest.raises(ValueError, match="Skill not found for clarification"):
        await process_clarification_response(
            skills=[],  # no SkillComputationWithClarification
            input=input_data,
            config=config,
            agent_name="agent-x"
        )


@pytest.mark.asyncio
async def test_successful_process_flow():
    skill = DummySkill()
    skill.name = "skill1"

    # Pending job matches computation_id
    pending_job = ComputationRequested(
        name="skill1",
        brain_args={"foo": "bar"},
        clarification_args={},
        computation_id="comp-1"
    )
    context = ClarificationContext(
        computations_requested=[pending_job],
        computations_results=[],
        requested_by="agent-x"
    )
    message = ClarificationMessage(
        clarification_context=context,
        clarification_id="clarif-1",
        computation_id="comp-1",
        payload={"extra": "info"},
        content='',
        to='pablo',
        timestamp='2025-09-09'
    )
    input_data = MuscleInputClarificationResponse(clarification_message=message)
    config = RunnableConfig()

    fake_result = {"result": "done"}
    fake_final_output = {"final": "output"}

    with patch(
        "crewmaster.features.muscle.helpers.process_clarification_response.execute_computation",
        new=AsyncMock(return_value=fake_result)
    ) as mock_exec_comp, patch(
        "crewmaster.features.muscle.helpers.process_clarification_response.execute_computations_pending",
        new=AsyncMock(return_value=fake_final_output)
    ) as mock_exec_pending:
        output = await process_clarification_response(
            skills=[skill],
            input=input_data,
            config=config,
            agent_name="agent-x"
        )

    # Assert execute_computation called with ComputationRequestedWithClarification
    called_request = mock_exec_comp.call_args[1]["request"]
    assert isinstance(called_request, ComputationRequestedWithClarification)
    assert called_request.clarification_args == {"extra": "info"}

    # Assert execute_computations_pending called with updated pending and results
    args, kwargs = mock_exec_pending.call_args
    assert kwargs["pending"] == []
    assert kwargs["results"] == [fake_result]
    assert output == fake_final_output
