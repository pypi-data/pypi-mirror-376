from typing import (
    List,
)
import structlog
from langchain_core.runnables import (
    RunnableConfig,
)
from langchain_core.load.dump import dumpd
from ...skill import (
    SkillComputation,
)
from ..muscle_types import (
    MuscleInputComputationRequested,
    MuscleOutput,
)
from .execute_computations_pending import execute_computations_pending

log = structlog.get_logger()
"Loger para el módulo"


async def process_computations_request(
    skills: List[SkillComputation],
    input: MuscleInputComputationRequested,
    config: RunnableConfig,
    agent_name: str,
) -> MuscleOutput:
    pending = input.computations_required
    results = []
    return await execute_computations_pending(
        pending=pending,
        results=results,
        skills=skills,
        agent_name=agent_name,
        config=config
    )
