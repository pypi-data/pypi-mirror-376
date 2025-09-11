from typing import (
    List,
)
import structlog
from langchain_core.runnables import (
    RunnableConfig,
)
from ...skill import (
    ComputationRequestedWithClarification,
    SkillComputation,
    SkillComputationWithClarification,
)
from ..muscle_types import (
    MuscleInputClarificationResponse,
    MuscleOutput,
)
from .execute_computation import execute_computation
from .execute_computations_pending import execute_computations_pending

log = structlog.get_logger()
"Loger para el módulo"


async def process_clarification_response(
    skills: List[SkillComputation],
    input: MuscleInputClarificationResponse,
    config: RunnableConfig,
    agent_name: str,
) -> MuscleOutput:
    message = input.clarification_message
    context = message.clarification_context
    requested = context.computations_requested
    results = context.computations_results
    # Buscamos que exista la clarification
    expected = [job for job in requested
                if (
                    job.computation_id == message.computation_id
                )]
    if len(expected) == 0:
        raise ValueError('Clarification received is not expected')
    clarification_request = expected[0]
    # Buscamos el skill asociado
    skill_list = [skill for skill in skills
                  if skill.name == clarification_request.name
                  and isinstance(
                      skill, SkillComputationWithClarification
                    )
                  ]
    if len(skill_list) != 1:
        raise ValueError('Skill not found for clarification')
    computation_requested = ComputationRequestedWithClarification(
        name=clarification_request.name,
        brain_args=clarification_request.brain_args,
        clarification_args=message.payload,
        computation_id=clarification_request.computation_id
    )
    skills_availables = [skill for skill in skills
                          if skill.name == clarification_request.name]
    if len(skills_availables) == 0:
        raise ValueError(
            'No definition available for execute'
            f'{clarification_request.name}'
        )
    option_clarified = skills_availables[0]
    computation_result = await execute_computation(
        option=option_clarified,
        request=computation_requested,
        config=config
    )
    # Sacamos la clarificación ejecutada de requested
    new_pending = [job for job in requested
                   if job.computation_id != message.computation_id]
    # Pasamos la clarificación ejecutada a results
    new_results = results + [computation_result]
    # Llamamos a process_computations para el resto
    result = await execute_computations_pending(
        pending=new_pending,
        results=new_results,
        skills=skills,
        agent_name=agent_name,
        config=config
    )
    return result
