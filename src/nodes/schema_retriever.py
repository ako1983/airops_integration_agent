# nodes/schema_retriever.py
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, ClassVar

class SchemaRetrieverInput(BaseModel):
    platform: str
    action_intent: str
    entity_type: str

class SchemaRetrieverOutput(BaseModel):
    matched_action: Optional[Dict[str, Any]] = None
    alternatives: List[Dict[str, Any]] = []
    needs_clarification: bool = False

class SchemaRetrieverTool(BaseTool):
    name: ClassVar[str] = "schema_retriever"
    description: ClassVar[str] = "Retrieves the schema for a specified integration action"
    args_schema: ClassVar[type] = SchemaRetrieverInput

    def _run(self, platform: str, action_intent: str, entity_type: str) -> SchemaRetrieverOutput:
        """
        Retrieve the integration action that best matches the intent.
        This bridges our action_selector logic into the LangGraph node.
        """
        from src.models.action import IntegrationAction
        from src.action_selector import calculate_action_relevance
        import json

        # Load integration actions
        with open("data/integration_actions.json", "r") as f:
            actions_data = json.load(f)

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

        return SchemaRetrieverOutput(
            matched_action=scored_actions[0]["action"] if scored_actions else None,
            alternatives=[a["action"] for a in scored_actions[1:3]] if needs_clarification else [],
            needs_clarification=needs_clarification
        )