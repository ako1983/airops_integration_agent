# src/graph.py
from langgraph.graph import StateGraph
from langchain_anthropic import ChatAnthropic
from config.observability import ObservabilityConfig
from utils.tracking import PerformanceTracker
from src.nodes.query_refiner import QueryRefinerNode
from src.nodes.planner import PlannerNode
from src.nodes.schema_retriever import SchemaRetrieverTool
from src.nodes.generator import ParameterGeneratorTool
from src.nodes.validator import ParameterValidatorTool
from src.nodes.repair import RepairNode
from src.nodes.workflow_generator import WorkflowGeneratorTool
from src.nodes.final_output import FinalOutputNode
from typing import Dict, Any, TypedDict

# Define the state schema for LangGraph 0.4+
class AgentState(TypedDict):
    user_request: str
    refined_query: str
    selected_action: Dict[str, Any]
    action_schema: Dict[str, Any]
    parameters: list
    validation_result: Dict[str, Any]
    workflow_definition: Dict[str, Any]
    output_result: Dict[str, Any]

def create_enhanced_integration_agent():
    """Create the enhanced integration agent with all components"""

    # Initialize observability
    observability = ObservabilityConfig()
    tracker = PerformanceTracker(observability)

    # Initialize LLM with LangSmith tracing
    llm = ChatAnthropic(
        model="claude-3-opus-20240229",
        # callbacks=[observability.get_langsmith_handler()]
    )

    # Initialize state graph with state schema
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("query_refiner", QueryRefinerNode(llm=llm))
    workflow.add_node("planner", PlannerNode(llm=llm))
    workflow.add_node("schema_retriever", SchemaRetrieverTool())
    workflow.add_node("parameter_generator", ParameterGeneratorTool())
    workflow.add_node("validator", ParameterValidatorTool())
    workflow.add_node("repair", RepairNode(llm=llm))
    workflow.add_node("workflow_generator", WorkflowGeneratorTool())
    workflow.add_node("final_output", FinalOutputNode())

    # Define the flow
    workflow.add_edge("query_refiner", "planner")
    workflow.add_edge("planner", "schema_retriever")
    workflow.add_edge("schema_retriever", "parameter_generator")
    workflow.add_edge("parameter_generator", "validator")

    # Conditional routing
    def validation_router(state: Dict[str, Any]) -> str:
        validation_result = state.get("validation_result", {})
        if validation_result.get("is_valid", False):
            return "workflow_generator"
        else:
            return "repair"

    workflow.add_conditional_edges(
        "validator",
        validation_router,
        {
            "workflow_generator": "workflow_generator",
            "repair": "repair"
        }
    )

    workflow.add_edge("repair", "parameter_generator")
    workflow.add_edge("workflow_generator", "final_output")

    # Set entry point
    workflow.set_entry_point("query_refiner")

    # TODO: Re-enable tracking after fixing wrapper compatibility
    # Apply tracking to all nodes
    # for node_name in workflow.nodes:
    #     original_node = workflow.nodes[node_name]
    #     workflow.nodes[node_name] = tracker.track_execution(node_name)(original_node)

    return workflow.compile()