import pytest
from .convert_to_tool_call import convert_to_tool_call


class DummySkillArgs:
    """A dummy object with a model_dump method to simulate Pydantic models."""
    def __init__(self, data):
        self._data = data

    def model_dump(self):
        return self._data


class DummyComputationResult:
    def __init__(self, name, computation_id, skill_args):
        self.name = name
        self.computation_id = computation_id
        self.skill_args = skill_args


def test_convert_to_tool_call_with_basic_data():
    skill_args = DummySkillArgs({"param1": "value1"})
    value = DummyComputationResult("skill1", "call123", skill_args)

    tool_call = convert_to_tool_call(value)

    assert tool_call.get("name") == "skill1"
    assert tool_call.get("id") == "call123"
    assert tool_call.get("args") == {"param1": "value1"}


def test_convert_to_tool_call_with_empty_args():
    skill_args = DummySkillArgs({})
    value = DummyComputationResult("skill2", "call456", skill_args)

    tool_call = convert_to_tool_call(value)

    assert tool_call.get("name") == "skill2"
    assert tool_call.get("id") == "call456"
    assert tool_call.get("args") == {}


def test_convert_to_tool_call_with_complex_args():
    skill_args = DummySkillArgs({"param": [1, 2, 3], "nested": {"key": "val"}})
    value = DummyComputationResult("skill3", "call789", skill_args)

    tool_call = convert_to_tool_call(value)

    assert tool_call.get("name") == "skill3"
    assert tool_call.get("id") == "call789"
    assert tool_call.get("args") == {"param": [1, 2, 3], "nested": {"key": "val"}}
