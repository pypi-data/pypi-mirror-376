import structlog
from langchain_core.runnables import (
    RunnableConfig,
)
from langchain_core.runnables.config import (
    merge_configs,
)
from ...skill import (
    ComputationRequested,
    ComputationRequestedWithClarification,
    ComputationResult,
    SkillComputationDirect,
    SkillComputationWithClarification,
)

log = structlog.get_logger()
"Loger para el módulo"



async def execute_computation(
    option: SkillComputationDirect | SkillComputationWithClarification,
    request: ComputationRequested | ComputationRequestedWithClarification,
    config: RunnableConfig,
) -> ComputationResult:
    default_config = RunnableConfig(
        tags=['cbr:skill']
    )
    config_tunned = merge_configs(default_config, config)
    if isinstance(
        option, SkillComputationDirect
    ) and isinstance(request, ComputationRequested):
        result = await option.ainvoke(
            input=request,
            config=config_tunned
        )
    elif isinstance(
        option, SkillComputationWithClarification
    ) and isinstance(request, ComputationRequestedWithClarification):
        result = await option.ainvoke(
            input=request,
            config=config_tunned
        )
    else:
        raise ValueError(
            'option must be a SkillComputationDirect '
            'or SkillComputationWithClarification instance'
        )
    return result