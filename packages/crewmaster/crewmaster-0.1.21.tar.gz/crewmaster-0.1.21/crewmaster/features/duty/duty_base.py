from abc import (
    abstractmethod
)
import operator
from typing import Annotated, Any, AsyncIterator, Dict, Generic, Optional, Type, TypeVar, List
from ...core.pydantic import (
    BaseModel,
)
from langchain_core.runnables.utils import (
    ConfigurableFieldSpec
)
from langchain_core.runnables import (
    RunnableConfig,
)
from langchain_core.callbacks.manager import (
    CallbackManagerForChainRun
)
from langgraph.graph.state import (
    CompiledStateGraph,
    StateGraph,
)

from ..runnables import (
    WithAsyncInvokeConfigVerified,
    WithAsyncStreamConfigVerified,
    RunnableStreameable,
)


DutyInput = TypeVar('DutyInput', bound=BaseModel)
DutyOutput = TypeVar('DutyOutput', bound=BaseModel)
DutyState = TypeVar('DutyState', bound=BaseModel)


class DutyBase(
    WithAsyncInvokeConfigVerified[DutyInput, DutyOutput],
    WithAsyncStreamConfigVerified[DutyInput, DutyOutput],
    RunnableStreameable[DutyInput, DutyOutput],
    Generic[DutyInput, DutyOutput, DutyState]
):
    """Abstract base class for the duties a collaborator can perform.

    A duty is a responsability that a collaborator fullfill.
    """
    multi_turn: bool = False
    description: str
    state_schema: Type[DutyState]

    @property
    def config_specs(self) -> List[ConfigurableFieldSpec]:
        """Required fields in the configuration for this runnable.

        Returns:
            (list): A list of ConfigurableFieldSpec objects.
        """
        return []

    def invoke(
        self,
        input: DutyInput,
        config: RunnableConfig | None = None
    ) -> DutyOutput:
        """Invokes the duty.

        Raises:
            Exception: Collaborator can only be called asynchronously.
        """
        raise Exception(f'Duty {self.name} can only be called asynchronously')

    def _setup_graph(
        self,
        config_parsed: BaseModel,
        config_raw: RunnableConfig,
    ) -> CompiledStateGraph:
        """Initializes and compiles the state graph.

        Args:
            config_parsed (BaseModel): The parsed configuration.
            config_raw (RunnableConfig): The raw runnable configuration.

        Returns:
            CompiledStateGraph: The compiled state graph.
        """
        init_graph = StateGraph(
            # state_schema=type(DutyState),
            state_schema=self.state_schema,
            config_schema=self.config_schema,
        )
        prepared = self._build_graph(
            graph=init_graph,
            config_parsed=config_parsed,
            config_raw=config_raw
        )
        compiled = prepared.compile()
        # compiled.stream_channels = ["cleaner"]
        return compiled



    def _build_config(
        self,
        config_raw: RunnableConfig
    ) -> RunnableConfig:
        """Builds the runnable configuration.

        Args:
            config_raw (RunnableConfig): The raw runnable configuration.

        Returns:
            RunnableConfig: The configured runnable.
        """
        return config_raw

        
    async def async_invoke_config_parsed(
        self,
        input: DutyInput,
        config_parsed: BaseModel,
        config_raw: RunnableConfig
    ) -> DutyOutput:
        """Asynchronously invokes the duty with a parsed configuration.

        Args:
            input (DutyInput): The input data for the duty.
            config_parsed (BaseModel): The parsed configuration.
            config_raw (RunnableConfig): The raw runnable configuration.

        Returns:
            DutyOutput: The output of the duty.
        """
        graph = self._setup_graph(
            config_parsed=config_parsed,
            config_raw=config_raw
        )
        state = self._rebuild_state(
            input=input,
            config_parsed=config_parsed,
            config_raw=config_raw
        )
        config_tunned = self._build_config(config_raw)

        graph_result = await graph.ainvoke(
            state,
            config_tunned
        )
        result = self._output_acl(
            graph_result,
            config_parsed=config_parsed,
            config_raw=config_raw
        )
        return result

    async def astream_config_parsed(
        self,
        input: DutyInput,
        config_parsed: BaseModel,
        config_raw: RunnableConfig,
        run_manager: CallbackManagerForChainRun,
        **kwargs: Optional[Any],
    ) -> AsyncIterator[Dict[str, Any]]:    
        """Asynchronously streams the output of the collaborator.

        Args:
            input (CollaboratorInput): The input data for the collaborator.
            config_parsed (BaseModel): The parsed configuration.
            config_raw (RunnableConfig): The raw runnable configuration.
            run_manager (CallbackManagerForChainRun): The run manager.
            **kwargs: Optional keyword arguments.

        Yields:
            (dict): The chunks of the output.
        """
        graph = self._setup_graph(
            config_parsed=config_parsed,
            config_raw=config_raw
        )
        state = self._rebuild_state(
            input=input,
            config_parsed=config_parsed,
            config_raw=config_raw
        )
        config_tunned = self._build_config(config_raw)
        iterator = graph.astream(
            state,
            config_tunned,
            output_keys='output'
        )
        async for chunk in iterator:
            yield chunk

    @abstractmethod
    def _rebuild_state(
        self,
        input: DutyInput,
        config_parsed: BaseModel,
        config_raw: RunnableConfig,
    ) -> DutyState:
        """Rebuilds the collaborator's state from the input.

        Args:
            input (CollaboratorInput): The input data for the collaborator.
            config_parsed (BaseModel): The parsed configuration.
            config_raw (RunnableConfig): The raw runnable configuration.

        Raises:
            ValueError: If the type of input is not valid.

        Returns:
            CollaboratorState: The rebuilt collaborator state.
        """
        pass

    @abstractmethod
    def _build_graph(
        self,
        graph: StateGraph,
        config_parsed: BaseModel,
        config_raw: RunnableConfig,
    ) -> StateGraph:
        """Builds the state graph for the collaborator's logic.

        This method must be implemented by all subclasses.

        Args:
            graph (StateGraph): The initial state graph to build upon.
            config_parsed (BaseModel): The parsed configuration.
            config_raw (RunnableConfig): The raw runnable configuration.

        Returns:
            StateGraph: The built state graph.
        """
        pass

    @abstractmethod
    def _output_acl(
        self,
        state: Dict[str, Any],
        config_parsed: BaseModel,
        config_raw: RunnableConfig
    ) -> DutyOutput:
        """Validates the state output and casts it to CollaboratorOutput.

        Args:
            state (dict): The state dictionary returned by the graph.
            config_parsed (BaseModel): The parsed configuration.
            config_raw (RunnableConfig): The raw runnable configuration.

        Raises:
            ValueError: If the state.output is invalid.

        Returns:
            CollaboratorOutput: The casted output.
        """
        pass