import pytest
from langchain.agents.output_parsers.tools import ToolAgentAction
from langchain_core.agents import AgentAction
from .convert_action_to_computation import convert_action_to_computation
from ...skill import ComputationRequested


def test_convert_action_to_computation_with_tool_agent_action_and_dict_input():
    action = ToolAgentAction(
        tool="test_tool",
        tool_input={"param": "value"},
        log="log_data",
        tool_call_id="call-123",
        message_log=[]
    )

    result = convert_action_to_computation(action)

    assert isinstance(result, ComputationRequested)
    assert result.name == "test_tool"
    assert result.computation_id == "call-123"
    assert result.brain_args == {"param": "value"}


def test_convert_action_to_computation_with_tool_agent_action_and_non_dict_input():
    action = ToolAgentAction(
        tool="test_tool",
        tool_input="string_input",
        log="log_data",
        tool_call_id="call-456",
        message_log=[]
    )

    result = convert_action_to_computation(action)

    assert isinstance(result, ComputationRequested)
    assert result.name == "test_tool"
    assert result.computation_id == "call-456"
    assert result.brain_args == {"value": "string_input"}


def test_convert_action_to_computation_with_generic_agent_action_and_dict_input():
    action = AgentAction(
        tool="generic_tool",
        tool_input={"x": 42},
        log="log_data"
    )

    result = convert_action_to_computation(action)

    assert isinstance(result, ComputationRequested)
    assert result.name == "generic_tool"
    assert result.computation_id == ""  # No tool_call_id for generic AgentAction
    assert result.brain_args == {"x": 42}


def test_convert_action_to_computation_with_generic_agent_action_and_non_dict_input():
    action = AgentAction(
        tool="generic_tool",
        tool_input="non_dict_value",
        log="log_data"
    )

    result = convert_action_to_computation(action)

    assert isinstance(result, ComputationRequested)
    assert result.name == "generic_tool"
    assert result.computation_id == ""
    assert result.brain_args == {"value": "non_dict_value"}
