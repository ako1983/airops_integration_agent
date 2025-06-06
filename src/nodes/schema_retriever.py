# nodes/schema_retriever.py
from langchain.tools import BaseTool
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Type

class SchemaRetrieverInput(BaseModel):
    platform: str
    action_intent: str
    entity_type: str

class SchemaRetrieverOutput(BaseModel):
    matched_action: Optional[Dict[str, Any]] = None
    alternatives: List[Dict[str, Any]] = []
    needs_clarification: bool = False

class SchemaRetrieverTool(BaseTool):
    name: str = "schema_retriever"
    description: str = "Retrieves the schema for a specified integration action"
    # args_schema removed - using state-based input extraction
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        # Extract state from kwargs or use kwargs as state
        state = kwargs.get('state', kwargs)
        """
        Retrieve the integration action that best matches the intent from state.
        """
        try:
            # Extract inputs from state
            platform = state.get("platform", "")
            action_intent = state.get("action_intent", "")
            entity_type = state.get("entity_type", "")
            
            print(f"Schema retriever inputs: platform='{platform}', action='{action_intent}', entity='{entity_type}'")
            
            if not platform:
                new_state = state.copy()
                new_state.update({
                    "selected_action": None,
                    "action_schema": [],
                    "needs_action_clarification": True,
                    "error": "No platform identified"
                })
                return new_state
        except Exception as e:
            new_state = state.copy()
            new_state.update({
                "selected_action": None,
                "action_schema": [],
                "needs_action_clarification": True,
                "error": f"Schema retrieval failed: {str(e)}"
            })
            return new_state
        
        from src.models.action import IntegrationAction
        from src.action_selector import calculate_action_relevance
        from utils.helpers import load_integration_actions
        
        # Load integration actions
        actions_data = load_integration_actions()
            
        # Filter actions by platform
        platform_actions = [
            action for action in actions_data 
            if action["integration"].lower() == platform.lower()
        ]
        
        if not platform_actions:
            return SchemaRetrieverOutput(
                matched_action=None,
                alternatives=[],
                needs_clarification=False
            )
        
        # Create a mock parsed request for compatibility with action_selector
        mock_parsed_request = {
            "platform": platform,
            "action_intent": action_intent,
            "entity_type": entity_type,
            "parameters": {}
        }
        
        # Score and rank actions using our existing logic
        scored_actions = []
        for action in platform_actions:
            score = calculate_action_relevance(action, mock_parsed_request)
            scored_actions.append({
                "action": action,
                "score": score
            })
        
        # Sort by score
        scored_actions.sort(key=lambda x: x["score"], reverse=True)
        
        # Determine if clarification is needed
        needs_clarification = False
        if len(scored_actions) > 1:
            if scored_actions[0]["score"] - scored_actions[1]["score"] < 0.3:
                needs_clarification = True
        
        # Update state with selected action and schema
        new_state = state.copy()
        if scored_actions:
            selected_action = scored_actions[0]["action"]
            print(f"Selected action: {selected_action.get('integration', 'unknown')} - {selected_action.get('action', 'unknown')}")
            new_state.update({
                "selected_action": selected_action,
                "action_schema": selected_action.get("inputs_schema", []),
                "action_alternatives": [a["action"] for a in scored_actions[1:3]] if needs_clarification else [],
                "needs_action_clarification": needs_clarification
            })
        else:
            print(f"No actions found for platform '{platform}'")
            new_state.update({
                "selected_action": None,
                "action_schema": [],
                "needs_action_clarification": True
            })
        
        return new_state