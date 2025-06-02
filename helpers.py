# utils/helpers.py
import json
from typing import Dict, List, Any

def load_integration_actions() -> List[Dict[str, Any]]:
    """Load integration actions from JSON file"""
    with open("data/integration_actions.json", "r") as f:
        return json.load(f)

def load_workflow_context() -> Dict[str, Any]:
    """Load workflow context from JSON file"""
    with open("data/workflow_context.json", "r") as f:
        return json.load(f)

def extract_parameters_from_request(request: str) -> Dict[str, Any]:
    """Extract parameters from a natural language request"""
    # Simple implementation - in production this would use NLP
    parameters = {}
    
    # Look for quoted strings as potential values
    import re
    quoted_strings = re.findall(r'"([^"]*)"', request)
    
    # Common parameter patterns
    if "title" in request.lower() and quoted_strings:
        parameters["title"] = quoted_strings[0]
    
    if "name" in request.lower() and quoted_strings:
        parameters["name"] = quoted_strings[0]
    
    return parameters

def resolve_context_variable(variable_path: str, context: Dict[str, Any]) -> Any:
    """
    Resolve a context variable path like 'step_1.output.keyword'
    """
    parts = variable_path.split('.')
    value = context
    
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    
    return value