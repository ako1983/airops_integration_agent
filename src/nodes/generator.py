# src/nodes/generator.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Type
from utils.helpers import extract_parameters_from_request


class GeneratorInput(BaseModel):
    action_schema: Dict[str, Any]
    context_variables: Dict[str, Any] = Field(description="Available context variables")
    user_request: str = Field(description="Original user request")


class ActionParameter(BaseModel):
    name: str
    value: Any
    source: str = Field(description="Source of the parameter (user_request, context, default)")


class GeneratorOutput(BaseModel):
    parameters: List[ActionParameter]
    missing_parameters: List[str] = []
    confidence: float = Field(ge=0.0, le=1.0)


class ParameterGeneratorTool(BaseTool):
    name: str = "parameter_generator"
    description: str = "Generates parameters for an integration action based on schema"
    # args_schema removed - using state-based input extraction

    def _run(self, **kwargs) -> Dict[str, Any]:
        # Extract state from kwargs or use kwargs as state
        state = kwargs.get('state', kwargs)
        """
        Generate parameters for the integration action based on schema from state.
        """
        # Extract inputs from state
        action_schema = state.get("action_schema", [])
        context_variables = state.get("context_variables", {})
        user_request = state.get("user_request", "")
        
        # Extract parameters from user request
        extracted_params = extract_parameters_from_request(user_request)

        # Handle case where action_schema is a list or dict
        if isinstance(action_schema, list):
            inputs_schema = action_schema
        else:
            inputs_schema = action_schema.get("inputs_schema", [])
        
        # Get required parameters from schema
        required_params = [
            param for param in inputs_schema
            if param.get("required", False)
        ]

        # Map parameters from context and extracted parameters
        parameters = []
        missing_parameters = []

        for param in inputs_schema:
            param_name = param["name"]
            param_type = param.get("interface", "short_text")

            # Try to find value in extracted parameters
            if param_name in extracted_params:
                parameters.append(ActionParameter(
                    name=param_name,
                    value=extracted_params[param_name],
                    source="user_request"
                ))
                continue

            # Try to match with context variables
            matched = False
            for var_name, var_value in context_variables.items():
                # Check if variable contains the parameter name
                if param_name.lower() in var_name.lower():
                    parameters.append(ActionParameter(
                        name=param_name,
                        value=f"{{{{{var_name}}}}}",  # Use liquid syntax for template
                        source="context"
                    ))
                    matched = True
                    break

            if matched:
                continue

            # If parameter is required and no value found, add to missing list
            if param.get("required", False):
                missing_parameters.append(param_name)
            elif "test_value" in param:
                # Use test value as default
                parameters.append(ActionParameter(
                    name=param_name,
                    value=param["test_value"],
                    source="default"
                ))

        # Calculate confidence based on coverage of required parameters
        confidence = 1.0
        if required_params:
            confidence = (len(required_params) - len(missing_parameters)) / len(required_params)

        # Update state with generated parameters
        new_state = state.copy()
        new_state.update({
            "parameters": [{
                "name": p.name,
                "value": p.value,
                "source": p.source
            } for p in parameters],
            "missing_parameters": missing_parameters,
            "parameter_confidence": confidence
        })
        
        return new_state