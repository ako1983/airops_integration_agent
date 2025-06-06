# nodes/repair.py
from langchain.tools import BaseTool
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel
from typing import Dict, Any, List, Type

class RepairInput(BaseModel):
    validation_errors: List[Dict[str, str]]
    action_schema: Dict[str, Any]
    parameters: List[Dict[str, Any]]
    user_request: str

class RepairOutput(BaseModel):
    repaired_parameters: List[Dict[str, Any]]
    repair_suggestions: List[str]

class RepairNode(BaseTool):
    name: str = "repair"
    description: str = "Repairs invalid parameters based on validation errors"
    # args_schema removed - using state-based input extraction
    
    model_config = {"extra": "allow"}
    
    def __init__(self, llm):
        super().__init__()
        self.llm = llm
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        # Extract state from kwargs or use kwargs as state
        state = kwargs.get('state', kwargs)
        # Extract inputs from state
        validation_result = state.get("validation_result", {})
        validation_errors = validation_result.get("errors", [])
        action_schema = state.get("action_schema", [])
        parameters = state.get("parameters", [])
        user_request = state.get("user_request", "")
        
        # Handle case where action_schema is a list or dict
        if isinstance(action_schema, list):
            inputs_schema = action_schema
        else:
            inputs_schema = action_schema.get("inputs_schema", [])
        
        prompt = f"""
        Fix these parameter validation errors:
        
        Errors: {validation_errors}
        Current Parameters: {parameters}
        Expected Schema: {inputs_schema}
        Original Request: {user_request}
        
        Provide corrected parameters that match the schema.
        """
        
        # Skip LLM call for testing
        repair_plan = "Repair plan generated"
        
        # Apply repairs
        repaired_parameters = parameters.copy()
        suggestions = []
        
        for error in validation_errors:
            param_name = error["parameter"]
            suggestion = error.get("suggestion", "Please check this parameter")
            suggestions.append(f"{param_name}: {suggestion}")
            
            # Simple repair logic (in production, this would be more sophisticated)
            if "Required parameter is missing" in error["error"]:
                # Add a placeholder for missing required params
                repaired_parameters.append({
                    "name": param_name,
                    "value": f"{{{{{param_name}}}}}",  # Liquid template placeholder
                    "source": "repair"
                })
        
        # Update state with repaired parameters
        new_state = state.copy()
        new_state.update({
            "parameters": repaired_parameters,
            "repair_suggestions": suggestions,
            "repair_applied": True
        })
        
        return new_state