import pytest
from .convert_to_tool_message import (
    convert_to_tool_message,
    ToolMessage,
)

class DummyComputationResult:
    def __init__(self, name, computation_id, result):
        self.name = name
        self.computation_id = computation_id
        self.result = result


def test_convert_to_tool_message_with_string_result():
    value = DummyComputationResult("skill1", "call123", "success")
    message = convert_to_tool_message(value)

    assert isinstance(message, ToolMessage)
    assert message.name == "skill1"
    assert message.tool_call_id == "call123"
    assert message.content == "success"


def test_convert_to_tool_message_with_dict_result():
    value = DummyComputationResult("skill2", "call456", {"status": "ok"})
    message = convert_to_tool_message(value)

    assert isinstance(message, ToolMessage)
    assert message.name == "skill2"
    assert message.tool_call_id == "call456"
    assert message.content == str({"status": "ok"})


def test_convert_to_tool_message_with_numeric_result():
    value = DummyComputationResult("skill3", "call789", 12345)
    message = convert_to_tool_message(value)

    assert isinstance(message, ToolMessage)
    assert message.name == "skill3"
    assert message.tool_call_id == "call789"
    assert message.content == "12345"
