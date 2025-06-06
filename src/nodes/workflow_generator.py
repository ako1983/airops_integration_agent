# src/nodes/workflow_generator.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Type
from src.models.workflow import WorkflowDefinition, WorkflowStep, WorkflowInput


class WorkflowGeneratorInput(BaseModel):
    action_schema: Dict[str, Any]
    parameters: List[Dict[str, Any]]
    context_variables: Dict[str, Any]
    user_request: str


class WorkflowGeneratorOutput(BaseModel):
    workflow: Dict[str, Any]  # JSON workflow definition
    transformations_added: List[str] = []
    explanation: str


class WorkflowGeneratorTool(BaseTool):
    name: str = "workflow_generator"
    description: str = "Generates a valid workflow definition for the integration action"
    # args_schema removed - using state-based input extraction

    def _run(self, **kwargs) -> Dict[str, Any]:
        # Extract state from kwargs or use kwargs as state
        state = kwargs.get('state', kwargs)
        """
        Generate a workflow that executes the integration action with proper configurations from state.
        """
        # Extract inputs from state
        action_schema = state.get("action_schema", [])
        parameters = state.get("parameters", [])
        context_variables = state.get("context_variables", {})
        user_request = state.get("user_request", "")
        selected_action = state.get("selected_action", {})
        
        steps = []
        input_schema = []
        transformations_added = []

        # Analyze parameters to determine required transformations
        try:
            param_analysis = self._analyze_parameters(parameters, action_schema or selected_action)
        except Exception as e:
            # Fallback if analysis fails
            param_analysis = {
                "needs_json_parsing": False,
                "json_params": [],
                "needs_data_mapping": False,
                "mapping_params": []
            }

        # Add any necessary transformation steps
        if param_analysis["needs_json_parsing"]:
            steps.append(self._create_json_parser_step(param_analysis["json_params"]))
            transformations_added.append("JSON parsing")

        if param_analysis["needs_data_mapping"]:
            steps.append(self._create_data_mapping_step(param_analysis["mapping_params"]))
            transformations_added.append("Data mapping")

        # Create the main integration step
        try:
            integration_step = self._create_integration_step(action_schema or selected_action, parameters, steps)
            steps.append(integration_step)
        except:
            # Basic fallback integration step
            integration_step = {
                "name": "integration_action",
                "type": "integration",
                "config": {
                    "integration": selected_action.get("integration", "unknown") if selected_action else "unknown",
                    "action": selected_action.get("action", "unknown") if selected_action else "unknown",
                    "parameters": {p.get("name", "unknown"): p.get("value", "") for p in parameters}
                }
            }
            steps.append(integration_step)

        # Create input schema based on required parameters
        try:
            input_schema = self._create_input_schema(parameters, action_schema or selected_action)
        except:
            # Basic fallback input schema
            input_schema = [{"name": p.get("name", "param"), "type": "text", "required": True} for p in parameters]

        # Compile the workflow
        workflow = {
            "input_schema": input_schema,
            "definition": steps
        }

        # Generate explanation
        try:
            explanation = self._generate_explanation(action_schema or selected_action, parameters, transformations_added)
        except:
            explanation = f"Generated workflow for {selected_action.get('integration', 'integration') if selected_action else 'integration'} action with {len(parameters)} parameters"

        # Update state with generated workflow
        new_state = state.copy()
        new_state.update({
            "workflow_definition": workflow,
            "transformations_added": transformations_added,
            "workflow_explanation": explanation
        })
        
        return new_state

    def _analyze_parameters(self, parameters: List[Dict[str, Any]], action_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze parameters to determine required transformations"""
        json_params = []
        mapping_params = []

        # Get expected types from schema
        if action_schema is None:
            inputs_schema = []
        elif isinstance(action_schema, list):
            inputs_schema = action_schema
        else:
            inputs_schema = action_schema.get("inputs_schema", [])
        
        schema_types = {
            param["name"]: param.get("interface", "short_text")
            for param in inputs_schema
        }

        for param in parameters:
            param_name = param["name"]
            param_value = param["value"]
            expected_type = schema_types.get(param_name, "short_text")

            # Check if JSON parsing is needed
            if expected_type == "json" and isinstance(param_value, str) and param["source"] != "user_request":
                json_params.append(param)

            # Check if data mapping is needed (e.g., extracting specific fields from objects)
            if "." in str(param_value) and param["source"] == "context":
                mapping_params.append(param)

        return {
            "needs_json_parsing": bool(json_params),
            "json_params": json_params,
            "needs_data_mapping": bool(mapping_params),
            "mapping_params": mapping_params
        }

    def _create_json_parser_step(self, json_params: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a code step to parse JSON strings"""
        parse_code = """
import json

# Parse JSON parameters
parsed_params = {}
"""

        for param in json_params:
            parse_code += f"""
try:
    parsed_params['{param["name"]}'] = json.loads({param["value"]})
except:
    parsed_params['{param["name"]}'] = {param["value"]}
"""

        parse_code += """
return parsed_params
"""

        return {
            "name": "json_parser",
            "type": "code",
            "config": {
                "language": "python",
                "function": parse_code
            }
        }

    def _create_data_mapping_step(self, mapping_params: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a code step for data mapping transformations"""
        mapping_code = """
# Extract and map data from context
mapped_params = {}
"""

        for param in mapping_params:
            # Extract the path (e.g., "step_1.output.keyword")
            path_parts = str(param["value"]).strip("{{}}").split(".")
            mapping_code += f"""
# Extract {param["name"]} from {param["value"]}
try:
    value = {path_parts[0]}
    for key in {path_parts[1:]}:
        value = value.get(key, None) if isinstance(value, dict) else getattr(value, key, None)
    mapped_params['{param["name"]}'] = value
except:
    mapped_params['{param["name"]}'] = None
"""

        mapping_code += """
return mapped_params
"""

        return {
            "name": "data_mapper",
            "type": "code",
            "config": {
                "language": "python",
                "function": mapping_code
            }
        }

    def _create_integration_step(
            self,
            action_schema: Dict[str, Any],
            parameters: List[Dict[str, Any]],
            previous_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create the main integration step"""
        # Prepare the parameters, referencing previous steps if needed
        integration_params = {}

        for param in parameters:
            param_name = param["name"]
            param_value = param["value"]

            # If the parameter was transformed in a previous step, reference it
            if any(step["name"] == "json_parser" for step in previous_steps) and \
                    param in self._analyze_parameters(parameters, action_schema)["json_params"]:
                integration_params[param_name] = f"{{{{json_parser.output['{param_name}']}}}}"
            elif any(step["name"] == "data_mapper" for step in previous_steps) and \
                    param in self._analyze_parameters(parameters, action_schema)["mapping_params"]:
                integration_params[param_name] = f"{{{{data_mapper.output['{param_name}']}}}}"
            else:
                integration_params[param_name] = param_value

        # Handle special cases for specific integrations
        step_config = self._adapt_integration_config(action_schema, integration_params)

        return {
            "name": f"{action_schema['integration']}_{action_schema['action'].lower().replace(' ', '_')}",
            "type": "integration",
            "config": step_config
        }

    def _adapt_integration_config(self, action_schema: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt the configuration based on the specific integration requirements"""
        integration = action_schema["integration"]
        action = action_schema["action"]

        # Most integrations follow a standard pattern
        config = {
            "integration": f"{{{{{integration}_integration}}}}",
            "action": action,
            "parameters": params
        }

        # Handle special cases based on the integration type
        if integration in ["webflow_v2", "contentful", "notion"]:
            # These integrations might need special formatting
            config["dynamic"] = params
            del config["parameters"]

        return config

    def _create_input_schema(self, parameters: List[Dict[str, Any]], action_schema: Dict[str, Any]) -> List[
        Dict[str, Any]]:
        """Create input schema for the workflow"""
        inputs = []

        # Add integration authentication
        inputs.append({
            "name": f"{action_schema['integration']}_integration",
            "required": True,
            "type": "integration",
            "label": f"{action_schema['integration'].title()} Integration",
            "group_id": "authentication"
        })

        # Add inputs for parameters that need user input
        for param in parameters:
            if param["source"] == "user_request":
                # Find the schema definition for this parameter
                schema_param = next(
                    (p for p in action_schema["inputs_schema"] if p["name"] == param["name"]),
                    None
                )

                if schema_param:
                    inputs.append({
                        "name": param["name"],
                        "required": schema_param.get("required", False),
                        "type": self._map_interface_to_type(schema_param.get("interface", "short_text")),
                        "label": schema_param.get("label", param["name"]),
                        "group_id": "parameters",
                        "placeholder": schema_param.get("placeholder", ""),
                        "test_value": param["value"],
                        "options": schema_param.get("options", None)
                    })

        return inputs

    def _map_interface_to_type(self, interface: str) -> str:
        """Map integration interface types to workflow input types"""
        mapping = {
            "short_text": "short_text",
            "long_text": "long_text",
            "json": "json",
            "single_select": "single_select",
            "number": "number",
            "integration": "integration",
            "dynamic": "json"
        }
        return mapping.get(interface, "short_text")

    def _generate_explanation(
            self,
            action_schema: Dict[str, Any],
            parameters: List[Dict[str, Any]],
            transformations: List[str]
    ) -> str:
        """Generate a human-readable explanation of the workflow"""
        explanation = f"Generated workflow for {action_schema['integration']} - {action_schema['action']}:\n\n"

        # Explain parameter mappings
        explanation += "Parameter Mappings:\n"
        for param in parameters:
            explanation += f"  • {param['name']}: {param['value']} (from {param['source']})\n"

        # Explain transformations
        if transformations:
            explanation += f"\nTransformations Applied:\n"
            for transform in transformations:
                explanation += f"  • {transform}\n"

        # Explain workflow steps
        explanation += "\nWorkflow Steps:\n"
        step_count = 1
        if "JSON parsing" in transformations:
            explanation += f"  {step_count}. Parse JSON parameters\n"
            step_count += 1
        if "Data mapping" in transformations:
            explanation += f"  {step_count}. Map data from context variables\n"
            step_count += 1
        explanation += f"  {step_count}. Execute {action_schema['action']} action\n"

        return explanation