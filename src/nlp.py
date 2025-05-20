# src/nlp.py
from typing import Dict, List, Any

def parse_user_request(user_request: str, integration_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parse a natural language request to identify integration targets and actions.
    
    Args:
        user_request (str): The user's natural language request
        integration_actions (list): Available integration actions
        
    Returns:
        dict: Structured representation of the parsed request
    """
    # Extract unique integrations from available actions
    available_integrations = list(set(action["integration"] for action in integration_actions))
    
    # In a real implementation, this would use an LLM
    # For now, we'll create a simple example
    parsed_request = {
        "platform": None,
        "action_intent": None,
        "entity_type": None,
        "parameters": {},
        "context_variables": [],
        "constraints": []
    }
    
    # Simple keyword matching for demonstration
    request_lower = user_request.lower()
    
    # Identify platform
    for integration in available_integrations:
        if integration.lower() in request_lower:
            parsed_request["platform"] = integration
            break
    
    # Identify action intent
    if "create" in request_lower:
        parsed_request["action_intent"] = "create"
    elif "update" in request_lower:
        parsed_request["action_intent"] = "update"
    elif "list" in request_lower or "get" in request_lower:
        parsed_request["action_intent"] = "list"
    
    # Identify entity type
    if "collection" in request_lower:
        parsed_request["entity_type"] = "collection"
    elif "item" in request_lower:
        parsed_request["entity_type"] = "item"
    elif "post" in request_lower:
        parsed_request["entity_type"] = "post"
    
    return parsed_request