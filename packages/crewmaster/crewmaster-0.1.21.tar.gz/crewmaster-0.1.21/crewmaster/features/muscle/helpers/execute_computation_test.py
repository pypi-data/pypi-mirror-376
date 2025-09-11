from typing import Any, Dict
import pytest
from unittest.mock import AsyncMock

import structlog

from ...skill.types import (
    BrainSchemaBase,
    ResultSchemaBase,
    ClarificationSchemaBase,
)
from .execute_computation import ( 
    execute_computation,
    SkillComputationDirect,
    SkillComputationWithClarification,
    ComputationRequested,
    ComputationRequestedWithClarification,
    ComputationResult,
    RunnableConfig,
)

log = structlog.get_logger()
"Loger para el módulo"


class FakeBrainSchema(BrainSchemaBase):
    prop: str = ''


class FakeResultSchema(ResultSchemaBase):
    response: str = ''


class FakeClarificationSchema(ClarificationSchemaBase):
    prop: str = ''


# Concrete test subclasses to bypass abstract base class restrictions
class FakeSkillComputationDirect(SkillComputationDirect):
    name: str = 'fake_op'
    brain_args: Dict[str, Any] = dict
    clarification_args: Dict[str, Any] = dict
    computation_id: str = '22222'
    description: str = ''
    brain_schema: FakeBrainSchema = FakeBrainSchema()
    result_schema: FakeResultSchema = FakeResultSchema()

    async def async_executor(self, input, config):
        pass  # not used in tests


class FakeSkillComputationWithClarification(SkillComputationWithClarification):
    name: str = 'fake_op'
    brain_args: Dict[str, Any] = dict
    clarification_args: Dict[str, Any] = dict
    computation_id: str = '22222'
    description: str = ''
    brain_schema: FakeBrainSchema = FakeBrainSchema()
    result_schema: FakeResultSchema = FakeResultSchema()
    clarification_schema: FakeClarificationSchema = FakeClarificationSchema()
    skill_input_schema: FakeClarificationSchema = FakeClarificationSchema()

    async def async_executor(self, skill_args, config):
        pass  # not used in tests

    async def merge_brain_with_clarification(self, brain_input, clarification_input):
        pass  # not used in tests


@pytest.mark.asyncio
async def test_execute_computation_direct_success():
    option = FakeSkillComputationDirect()
    mock_ainvoke = AsyncMock(return_value=ComputationResult(
        computation_id="123",
        name="test-skill",
        skill_args={"foo": "bar"},
        result=FakeResultSchema.model_validate({'response': 'all is good'})
    ))
    object.__setattr__(option, "ainvoke", mock_ainvoke)
    request = ComputationRequested(
        name="test-skill",
        brain_args={"foo": "bar"},
        computation_id="123"
    )
    config = RunnableConfig(tags=["custom"])
    execution = await execute_computation(option, request, config)
    mock_ainvoke.assert_awaited_once()
    assert isinstance(execution, ComputationResult)
    assert execution.computation_id == "123"
    assert execution.result.response == 'all is good'


@pytest.mark.asyncio
async def test_execute_computation_with_clarification_success():
    option = FakeSkillComputationWithClarification()
    mock_ainvoke = AsyncMock(return_value=ComputationResult(
        computation_id="456",
        name="test-skill-clarification",
        skill_args={"foo": "baz"},
        result={"response": 'all is good'}
    ))
    object.__setattr__(option, "ainvoke", mock_ainvoke)

    request = ComputationRequestedWithClarification(
        name="test-skill-clarification",
        brain_args={"foo": "baz"},
        clarification_args={"extra": "info"},
        computation_id="456"
    )
    config = RunnableConfig(tags=["clarification"])

    result = await execute_computation(option, request, config)

    mock_ainvoke.assert_awaited_once()
    assert isinstance(result, ComputationResult)
    assert result.computation_id == "456"
    # assert result.result["output"] == 99


@pytest.mark.asyncio
async def test_execute_computation_invalid_option_request_pair():
    option = FakeSkillComputationDirect()
    request = ComputationRequestedWithClarification(
        name="wrong",
        brain_args={},
        clarification_args={},
        computation_id="999"
    )
    config = RunnableConfig()

    with pytest.raises(ValueError) as exc:
        await execute_computation(option, request, config)

    assert "option must be a SkillComputationDirect" in str(exc.value)


@pytest.mark.asyncio
async def test_execute_computation_merges_config():
    option = FakeSkillComputationDirect()
    mock_ainvoke = AsyncMock(return_value=ComputationResult(
        computation_id="merge-test",
        name="merge-skill",
        skill_args={},
        result={}
    ))
    object.__setattr__(option, "ainvoke", mock_ainvoke)

    request = ComputationRequested(
        name="merge-skill",
        brain_args={},
        computation_id="merge-test"
    )

    # This config should be merged with default_config(tags=["cbr:skill"])
    passed_config = RunnableConfig(tags=["user-tag"], metadata={"foo": "bar"})

    await execute_computation(option, request, passed_config)

    # Check that ainvoke was called with a config that has BOTH tags
    called_config = mock_ainvoke.call_args.kwargs["config"]
    assert "cbr:skill" in called_config.get('tags')
    assert "user-tag" in called_config.get('tags')
    assert called_config.get('metadata')["foo"] == "bar"