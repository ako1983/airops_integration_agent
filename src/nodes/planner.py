# nodes/planner.py
from langchain.tools import BaseTool
from langchain_community.chat_models import ChatAnthropic  # Fixed import if used
from pydantic import BaseModel
from typing import Dict, Any, List
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
    name = "planner"
    description = "Plans the integration action based on refined query"
    args_schema = PlannerInput
    
    def __init__(self, llm):
        super().__init__()
        self.llm = llm
    
    def _run(
        self,
        refined_query: str,
        context: Dict[str, Any],
        integration_actions: List[Dict[str, Any]]
    ) -> PlannerOutput:
        # Use the NLP parser
        parsed = parse_user_request(refined_query, integration_actions)
        
        # Enhanced parsing with LLM
        prompt = f"""
        Analyze this integration request in detail:
        
        Query: {refined_query}
        Initial Parse: {parsed}
        Available Context: {list(context.keys())}
        
        Identify:
        1. The specific platform
        2. The exact action intent
        3. The entity type
        4. Required parameters and their values
        5. Context variables that should be used
        
        Return a detailed plan.
        """
        
        enhanced_plan = self.llm.invoke(prompt).content
        
        # Merge with initial parse
        return PlannerOutput(
            platform=parsed["platform"],
            action_intent=parsed["action_intent"],
            entity_type=parsed["entity_type"],
            parameters=parsed["parameters"],
            context_variables=parsed["context_variables"]
        )