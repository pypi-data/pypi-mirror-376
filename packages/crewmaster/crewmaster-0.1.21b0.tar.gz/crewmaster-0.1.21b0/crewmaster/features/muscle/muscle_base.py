from typing import (
    List,
    Optional,
)
import structlog
from langchain_core.runnables import (
    RunnableConfig,
)
from langchain_core.runnables.utils import (
    ConfigurableFieldSpec
)
from langchain_core.runnables.config import (
    get_callback_manager_for_config,
)
from langchain_core.load.dump import dumpd

from ...core.pydantic import (
    BaseModel,
)
from ..runnables import (
    WithAsyncInvokeConfigVerified,
    RunnableStreameable,
)
from ..skill import (
    SkillComputation,
)
from .muscle_types import (
    MuscleInput,
    MuscleInputClarificationResponse,
    MuscleInputComputationRequested,
    MuscleOutput,
)
from .helpers import (
    process_clarification_response,
    process_computations_request,

)

log = structlog.get_logger()
"Loger para el módulo"



class MuscleBase(
    WithAsyncInvokeConfigVerified[
        MuscleInput, MuscleOutput
    ],
    RunnableStreameable[
        MuscleInput,
        MuscleOutput
    ],
):
    """Handle the execution of the Skills.

    Handle a queue of pending jobs and make the execution of each one.

    Handle direct computations requested and computation that requires a clarification.

    """
    name: Optional[str] = 'cbr:muscle'
    agent_name: str
    skills: List[SkillComputation] = []

    @property
    def config_specs(self) -> List[ConfigurableFieldSpec]:
        """List configurable fields for this runnable."""
        # Construimos la lista a partir de las opciones
        # con que está trabajando el muscle
        skills_specs = list({spec for skill in self.skills
                              for spec in skill.config_specs})
        return skills_specs

    def invoke(
        self,
        input: MuscleInput,
        config: RunnableConfig | None = None
    ) -> MuscleOutput:
        raise Exception('Muscle can only be invoked asynchronously')

    async def async_invoke_config_parsed(
            self,
            input: MuscleInput,
            config_parsed: BaseModel,
            config_raw: RunnableConfig
    ) -> MuscleOutput:
        callback_manager = get_callback_manager_for_config(config_raw)
        run_manager = callback_manager.on_chain_start(
            serialized=dumpd(self),
            inputs=input,
            name=self.name
        )

        if isinstance(input, MuscleInputComputationRequested):
            result = await process_computations_request(
                skills=self.skills,
                input=input,
                config=config_raw,
                agent_name=self.agent_name
            )
            run_manager.on_chain_end(result)
            return result
        if isinstance(input, MuscleInputClarificationResponse):
            result = await process_clarification_response(
                skills=self.skills,
                input=input,
                config=config_raw,
                agent_name=self.agent_name
            )
            run_manager.on_chain_end(result)
            return result
        raise ValueError(
            'Invalid type for Muscle'
        )
