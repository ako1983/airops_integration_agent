# src/nodes/validator.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
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
    name = "parameter_validator"
    description = "Validates parameters against the action schema"
    args_schema = ValidatorInput

    def _run(
            self,
            action_schema: Dict[str, Any],
            parameters: List[Dict[str, Any]]
    ) -> ValidatorOutput:
        """
        Validate parameters against the integration action schema.
        """
        # Create parameter lookup
        param_lookup = {p["name"]: p["value"] for p in parameters}
        errors = []

        # Validate against schema
        for schema_param in action_schema["inputs_schema"]:
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

        return ValidatorOutput(
            is_valid=len(errors) == 0,
            errors=errors
        )

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