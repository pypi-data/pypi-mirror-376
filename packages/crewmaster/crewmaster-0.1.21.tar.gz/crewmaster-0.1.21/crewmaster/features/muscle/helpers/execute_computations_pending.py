from typing import (
    List,
)
import structlog
from langchain_core.runnables import (
    RunnableConfig,
)

from .execute_computation import execute_computation
from langchain_core.load.dump import dumpd
from ...collaborator import (
    ClarificationContext,
    ClarificationRequested,
)
from ...skill import (
    ComputationRequested,
    ComputationResult,
    SkillComputation,
    SkillComputationWithClarification,
)
from ..muscle_types import (
    MuscleOutput,
    MuscleOutputResults,
    MuscleOutputClarification,
)

log = structlog.get_logger()
"Loger para el módulo"


async def execute_computations_pending(
    pending: List[ComputationRequested],
    results: List[ComputationResult],
    skills: List[SkillComputation],
    agent_name: str,
    config: RunnableConfig
) -> MuscleOutput:
    if pending is None or len(pending) == 0:
        return MuscleOutputResults(
            computations_requested=[],
            computations_results=results
        )
    # Buscamos si alguna opcion requiere clarification
    map_skills = {option.name: option for option in skills}
    clarifications = [job for job in pending
                      # if map_options[job.name].require_clarification]
                      if isinstance(
                          map_skills[job.name],
                          SkillComputationWithClarification
                      )]
    if len(clarifications) > 0:
        computation = clarifications[0]
        clarification = ClarificationRequested(
            name=computation.name,
            clarification_id=computation.computation_id,
            brain_args=computation.brain_args
        )
        context = ClarificationContext(
            computations_requested=pending,
            computations_results=results,
            requested_by=agent_name
        )
        response = MuscleOutputClarification(
            clarification_requested=clarification,
            clarification_context=context
        )
        return response
    # Si llegamos aquí sólo hay computaciones directas
    requested = pending
    direct_results = [await execute_computation(
        option=map_skills[job.name],
        request=job,
        config=config
    ) for job in requested]
    all_results = direct_results + results
    return MuscleOutputResults(
        computations_requested=[],
        computations_results=all_results
    )

