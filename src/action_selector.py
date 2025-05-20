# src/action_selector.py
from typing import Dict, List, Any

def select_integration_action(parsed_request: Dict[str, Any], integration_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Select the most appropriate integration action based on the parsed request.
    """
    # Filter actions by platform
    platform_actions = [
        action for action in integration_actions 
        if action["integration"].lower() == parsed_request["platform"].lower()
    ]
    
    if not platform_actions:
        return {
            "status": "error",
            "message": f"No actions available for platform: {parsed_request['platform']}",
            "action": None,
            "confidence": 0.0
        }
    
    # Score each action
    scored_actions = []
    for action in platform_actions:
        score = calculate_action_relevance(action, parsed_request)
        scored_actions.append({
            "action": action,
            "score": score
        })
    
    # Sort actions by score
    scored_actions.sort(key=lambda x: x["score"], reverse=True)
    
    # Get the best matching action
    best_match = scored_actions[0]
    
    # Determine if clarification is needed
    needs_clarification = False
    if len(scored_actions) > 1:
        if scored_actions[0]["score"] - scored_actions[1]["score"] < 0.3:
            needs_clarification = True
    
    return {
        "status": "success" if best_match["score"] > 0.5 else "low_confidence",
        "action": best_match["action"],
        "confidence": best_match["score"],
        "alternatives": [a["action"] for a in scored_actions[1:3]] if needs_clarification else [],
        "needs_clarification": needs_clarification
    }

def calculate_action_relevance(action: Dict[str, Any], parsed_request: Dict[str, Any]) -> float:
    """Calculate how relevant an action is to the parsed request."""
    score = 0.0
    
    action_name = action["action"].lower()
    action_intent = parsed_request["action_intent"].lower() if parsed_request["action_intent"] else ""
    entity_type = parsed_request["entity_type"].lower() if parsed_request["entity_type"] else ""
    
    # Check if action name contains intent words
    if action_intent and action_intent in action_name:
        score += 0.4
    
    # Check if action name contains entity type
    if entity_type and entity_type in action_name:
        score += 0.4
    
    # Check parameter overlap
    request_params = set(parsed_request["parameters"].keys())
    action_params = set(param["name"] for param in action["inputs_schema"])
    param_overlap = len(request_params.intersection(action_params))
    
    # Normalize parameter overlap score
    if len(request_params) > 0:
        score += 0.2 * (param_overlap / len(request_params))
    
    return min(score, 1.0)