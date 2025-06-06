# src/nodes/final_output.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Type


class FinalOutputInput(BaseModel):
    workflow: Dict[str, Any]
    action_schema: Dict[str, Any]
    confidence: float
    explanation: str


class FinalOutputResult(BaseModel):
    status: str
    workflow: Dict[str, Any]
    confidence: float
    explanation: str
    suggestions: List[str] = []
    validation_warnings: List[str] = []


class FinalOutputNode(BaseTool):
    name: str = "final_output"
    description: str = "Prepares the final output for the user"
    # args_schema removed - using state-based input extraction

    def _run(self, **kwargs) -> Dict[str, Any]:
        # Extract state from kwargs or use kwargs as state
        state = kwargs.get('state', kwargs)
        """
        Prepare the final workflow output with validation and suggestions from state.
        """
        # Extract inputs from state
        workflow = state.get("workflow_definition", {})
        action_schema = state.get("action_schema", [])
        confidence = state.get("parameter_confidence", 0.5)
        explanation = state.get("workflow_explanation", "Workflow generated successfully")
        
        validation_warnings = []
        suggestions = []

        # Validate the workflow
        validation_result = self._validate_workflow(workflow)
        if not validation_result["is_valid"]:
            validation_warnings.extend(validation_result["warnings"])

        # Generate suggestions based on confidence and workflow
        if confidence < 0.8:
            suggestions.append("Consider reviewing the parameter mappings for accuracy")

        # Check for missing optional parameters
        optional_params = self._find_unused_optional_params(workflow, action_schema)
        if optional_params:
            suggestions.append(f"Optional parameters available: {', '.join(optional_params)}")

        # Determine status
        status = "success" if confidence >= 0.7 and not validation_warnings else "needs_review"

        # Update state with final output
        new_state = state.copy()
        new_state.update({
            "output_result": {
                "status": status,
                "workflow": workflow,
                "confidence": confidence,
                "explanation": explanation,
                "suggestions": suggestions,
                "validation_warnings": validation_warnings
            }
        })
        
        return new_state

    def _validate_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the workflow structure"""
        warnings = []

        # Check if input_schema exists
        if "input_schema" not in workflow:
            warnings.append("Missing input_schema")

        # Check if definition exists
        if "definition" not in workflow:
            warnings.append("Missing definition")
        elif not workflow["definition"]:
            warnings.append("Definition is empty")

        # Validate step structure
        if "definition" in workflow:
            for i, step in enumerate(workflow["definition"]):
                if "name" not in step:
                    warnings.append(f"Step {i} missing name")
                if "type" not in step:
                    warnings.append(f"Step {i} missing type")
                if "config" not in step:
                    warnings.append(f"Step {i} missing config")

        return {
            "is_valid": len(warnings) == 0,
            "warnings": warnings
        }

    def _find_unused_optional_params(self, workflow: Dict[str, Any], action_schema: Dict[str, Any]) -> List[str]:
        """Find optional parameters that weren't used in the workflow"""
        # Get all parameter names used in the workflow
        used_params = set()

        # Extract from input schema
        if "input_schema" in workflow:
            for input_param in workflow["input_schema"]:
                used_params.add(input_param["name"])

        # Extract from integration step parameters
        for step in workflow.get("definition", []):
            if step["type"] == "integration" and "parameters" in step["config"]:
                used_params.update(step["config"]["parameters"].keys())
            elif step["type"] == "integration" and "dynamic" in step["config"]:
                used_params.update(step["config"]["dynamic"].keys())

        # Find optional parameters not used
        unused_optional = []
        
        # Handle case where action_schema is a list or dict
        if isinstance(action_schema, list):
            inputs_schema = action_schema
        else:
            inputs_schema = action_schema.get("inputs_schema", [])
        
        for param in inputs_schema:
            if not param.get("required", False) and param["name"] not in used_params:
                unused_optional.append(param["name"])

        return unused_optional