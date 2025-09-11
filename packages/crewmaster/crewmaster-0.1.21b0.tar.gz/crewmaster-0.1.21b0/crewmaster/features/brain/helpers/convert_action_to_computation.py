

from typing import Dict
from langchain.agents.output_parsers.tools import (
    ToolAgentAction
)
from langchain_core.agents import (
    AgentAction,
)
from ...skill import (
    ComputationRequested,
)

def convert_action_to_computation(
    action: AgentAction
) -> ComputationRequested:
    """Converts an agent action to a computation request.

    Args:
        action: The `AgentAction` instance to convert.

    Returns:
        ComputationRequested: A computation request built from the action.
    """
    tool_call_id = action.tool_call_id if (
        isinstance(action, ToolAgentAction)
     ) else ''
    tool_input = action.tool_input if (
                    isinstance(action.tool_input, Dict)
                ) else {"value": action.tool_input}
    result = ComputationRequested(
        name=action.tool,
        computation_id=tool_call_id,
        brain_args=tool_input
    )
    return result
