# nodes/planner.py
from langchain.tools import BaseTool
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel
from typing import Dict, Any, List, Type
from src.nlp import parse_user_request

class PlannerInput(BaseModel):
    refined_query: str
    context: Dict[str, Any]
    integration_actions: List[Dict[str, Any]]

class PlannerOutput(BaseModel):
    platform: str
    action_intent: str
    entity_type: str
    parameters: Dict[str, Any]
    context_variables: List[str]

class PlannerNode(BaseTool):
    name: str = "planner"
    description: str = "Plans the integration action based on refined query"
    # args_schema removed - using state-based input extraction
    
    model_config = {"extra": "allow"}
    
    def __init__(self, llm):
        super().__init__()
        self.llm = llm
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        # Extract state from kwargs or use kwargs as state
        state = kwargs.get('state', kwargs)
        try:
            # Extract inputs from state
            refined_query = state.get("refined_query", state.get("user_request", ""))
            
            if not refined_query:
                new_state = state.copy()
                new_state.update({
                    "platform": None,
                    "action_intent": None,
                    "entity_type": None,
                    "error": "No query to plan"
                })
                return new_state
            
            # Load integration actions
            from utils.helpers import load_integration_actions
            integration_actions = load_integration_actions()
            
            # Use the NLP parser
            parsed = parse_user_request(refined_query, integration_actions)
        except Exception as e:
            new_state = state.copy()
            new_state.update({
                "platform": None,
                "action_intent": None,
                "entity_type": None,
                "error": f"Planning failed: {str(e)}"
            })
            print(f"Planner error: {str(e)}")
            return new_state
        
        # Enhanced parsing with LLM
        context_variables = state.get("context_variables", {})
        prompt = f"""
        Analyze this integration request in detail:
        
        Query: {refined_query}
        Initial Parse: {parsed}
        Available Context: {list(context_variables.keys())}
        
        Identify:
        1. The specific platform
        2. The exact action intent
        3. The entity type
        4. Required parameters and their values
        5. Context variables that should be used
        
        Return a detailed plan.
        """
        
        # Skip LLM call for testing
        enhanced_plan = "Enhanced plan generated"
        
        # Update state with planning results
        new_state = state.copy()
        new_state.update({
            "platform": parsed["platform"],
            "action_intent": parsed["action_intent"],
            "entity_type": parsed["entity_type"],
            "parsed_parameters": parsed["parameters"],
            "identified_context_variables": parsed["context_variables"]
        })
        
        # Debug output
        print(f"Planner parsed: platform={parsed['platform']}, action={parsed['action_intent']}, entity={parsed['entity_type']}")
        
        return new_state