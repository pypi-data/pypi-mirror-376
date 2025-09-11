import operator
import pytest
from typing import Annotated, Any, Dict, List, Type, cast
from langchain_core.runnables import (
    RunnableConfig,
)
from langgraph.graph.state import (
    CompiledStateGraph,
    StateGraph,
)
import structlog

from .duty_base import DutyBase
from ...core.pydantic import (
    BaseModel,
)

log = structlog.get_logger()
"Loger para el módulo"


class Input(BaseModel):
    request: str

class Output(BaseModel):
    response: str

class State(BaseModel):
    messages: Annotated[
        List[str],
        operator.add
    ] = []
    final_output: str = ''



def fake_start(
    state: State,
    config: RunnableConfig        
):
    log.info('entramos al start')
    return {'final_output': 'temporal'}
    

def fake_node(
    state: State,
    config: RunnableConfig
):
    log.info('pase por el fake_node', s=State)
    return {'final_output': 'Buen viaje'}


def cleaner(
    state: State,
    config: RunnableConfig
):
    return {"final_output": state.final_output}



class DutyFake(DutyBase[Input, Output, State]):

    state_schema: Type[State] = State

    def _rebuild_state(
        self,
        input: Input,
        config_parsed: BaseModel,
        config_raw: RunnableConfig,
    ) -> State:        
        # return {"messages": [input.request]}

        return State(messages=[input.request], final_output='')


    def _build_graph(
        self,
        graph: StateGraph,
        config_parsed: BaseModel,
        config_raw: RunnableConfig,
    ) -> StateGraph:
        graph.add_node('fake_start', fake_start)     # type: ignore
        graph.add_node('fake_node', fake_node)     # type: ignore
        graph.set_entry_point('fake_start')
        graph.add_edge('fake_start', 'fake_node')
        graph.add_edge('fake_node', 'cleaner')
        graph.add_node('cleaner', cleaner)
        graph.set_finish_point('cleaner')
        return graph


    def _output_acl(
        self,
        state: Dict[str, Any],
        config_parsed: BaseModel,
        config_raw: RunnableConfig
    ) -> Output:
        log.info('que nos llega al acl', sta=state)
        result = state.get("final_output")
        if result is None:
            raise ValueError('Invalid state.final_output on output_acl')
        output = Output.model_validate({"response": result})        
        return output


@pytest.mark.asyncio
async def test_create_duty():
    duty = DutyFake(
        name='Conversar',
        description="hablar con el usuario",
    )

    assert duty.name == 'Conversar'
    config = RunnableConfig(configurable={})
    result = await duty.ainvoke(Input(request='hola'), config)
    assert isinstance(result, Output)
    assert result.response == 'Buen viaje'
    log.info('result', r=result)

