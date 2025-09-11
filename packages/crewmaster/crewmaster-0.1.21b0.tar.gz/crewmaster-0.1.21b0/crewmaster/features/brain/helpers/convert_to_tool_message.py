from langchain_core.messages import (
    ToolMessage,
)
from ...skill import (
    ComputationResult,
    Skill,
)

def convert_to_tool_message(
    value: ComputationResult
) -> ToolMessage:
    """Converts a computation result to a `ToolMessage`.

    Args:
        value: The computation result to convert.

    Returns:
        ToolMessage: A tool message containing the computation result.
    """
    converted = ToolMessage(
        name=value.name,
        tool_call_id=value.computation_id,
        content=str(value.result)
    )
    return converted