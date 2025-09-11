from langchain_core.messages import (
    ToolCall,
)
from ...skill import (
    ComputationResult,
)


def convert_to_tool_call(
    value: ComputationResult
) -> ToolCall:
    """Converts a computation result to a `ToolCall`.

    Args:
        value: The computation result to convert.

    Returns:
        ToolCall: A tool call representing the computation request.
    """
    result = ToolCall(
        name=value.name,
        args=value.skill_args.model_dump(),
        id=value.computation_id
    )
    return result
