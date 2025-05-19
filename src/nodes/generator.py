# src/nodes/generator.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
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
    name = "parameter_generator"
    description = "Generates parameters for an integration action based on schema"
    args_schema = GeneratorInput

    def _run(
            self,
            action_schema: Dict[str, Any],
            context_variables: Dict[str, Any],
            user_request: str
    ) -> GeneratorOutput:
        """
        Generate parameters for the integration action based on schema.
        """
        # Extract parameters from user request
        extracted_params = extract_parameters_from_request(user_request)

        # Get required parameters from schema
        required_params = [
            param for param in action_schema["inputs_schema"]
            if param.get("required", False)
        ]

        # Map parameters from context and extracted parameters
        parameters = []
        missing_parameters = []

        for param in action_schema["inputs_schema"]:
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

        return GeneratorOutput(
            parameters=parameters,
            missing_parameters=missing_parameters,
            confidence=confidence
        )