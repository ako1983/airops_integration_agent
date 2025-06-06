# src/nodes/validator.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Type
import json


class ValidatorInput(BaseModel):
    action_schema: Dict[str, Any]
    parameters: List[Dict[str, Any]]


class ValidationError(BaseModel):
    parameter: str
    error: str
    suggestion: Optional[str] = None


class ValidatorOutput(BaseModel):
    is_valid: bool
    errors: List[ValidationError] = []


class ParameterValidatorTool(BaseTool):
    name: str = "parameter_validator"
    description: str = "Validates parameters against the action schema"
    # args_schema removed - using state-based input extraction

    def _run(self, **kwargs) -> Dict[str, Any]:
        # Extract state from kwargs or use kwargs as state
        state = kwargs.get('state', kwargs)
        """
        Validate parameters against the integration action schema from state.
        """
        # Extract inputs from state
        action_schema = state.get("action_schema", [])
        parameters = state.get("parameters", [])
        
        # Handle case where action_schema is a list or dict
        if isinstance(action_schema, list):
            inputs_schema = action_schema
        else:
            inputs_schema = action_schema.get("inputs_schema", [])
        
        # Create parameter lookup
        param_lookup = {p["name"]: p["value"] for p in parameters}
        errors = []

        # Validate against schema
        for schema_param in inputs_schema:
            param_name = schema_param["name"]

            # Check if required parameter is missing
            if schema_param.get("required", False) and param_name not in param_lookup:
                errors.append(ValidationError(
                    parameter=param_name,
                    error="Required parameter is missing",
                    suggestion="Please provide a value for this parameter"
                ))
                continue

            # Skip validation for optional parameters that aren't set
            if param_name not in param_lookup:
                continue

            value = param_lookup[param_name]
            interface = schema_param.get("interface", "short_text")

            # Type validation based on interface
            if interface == "number" and not (
                    isinstance(value, (int, float)) or str(value).replace(".", "", 1).isdigit()):
                errors.append(ValidationError(
                    parameter=param_name,
                    error=f"Expected a number, got: {value}",
                    suggestion="Please provide a numeric value"
                ))

            elif interface == "json" and not self._is_valid_json(value):
                errors.append(ValidationError(
                    parameter=param_name,
                    error=f"Expected valid JSON, got: {value}",
                    suggestion="Please provide a properly formatted JSON object"
                ))

            elif interface == "single_select" and schema_param.get("options") and value not in schema_param["options"]:
                errors.append(ValidationError(
                    parameter=param_name,
                    error=f"Value '{value}' not in allowed options: {schema_param['options']}",
                    suggestion=f"Please select one of the allowed options: {schema_param['options']}"
                ))

        # Update state with validation results
        new_state = state.copy()
        new_state.update({
            "validation_result": {
                "is_valid": len(errors) == 0,
                "errors": [{
                    "parameter": e.parameter,
                    "error": e.error,
                    "suggestion": e.suggestion
                } for e in errors]
            }
        })
        
        return new_state

    def _is_valid_json(self, value):
        """Check if a value is valid JSON or a valid JSON string"""
        if isinstance(value, (dict, list)):
            return True

        if isinstance(value, str):
            try:
                json.loads(value)
                return True
            except:
                return False

        return False