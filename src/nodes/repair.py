# nodes/repair.py
from langchain_core.tools import BaseTool
from langchain_community.chat_models import ChatAnthropic
from pydantic import BaseModel
from typing import Dict, Any, List, ClassVar

class RepairInput(BaseModel):
    validation_errors: List[Dict[str, str]]
    action_schema: Dict[str, Any]
    parameters: List[Dict[str, Any]]
    user_request: str

class RepairOutput(BaseModel):
    repaired_parameters: List[Dict[str, Any]]
    repair_suggestions: List[str]

class RepairNode(BaseTool):
    name: ClassVar[str] = "repair"
    description: ClassVar[str] = "Repairs invalid parameters based on validation errors"
    args_schema: ClassVar[type] = RepairInput

    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def _run(
        self,
        validation_errors: List[Dict[str, str]],
        action_schema: Dict[str, Any],
        parameters: List[Dict[str, Any]],
        user_request: str
    ) -> RepairOutput:
        prompt = f"""
        Fix these parameter validation errors:
        
        Errors: {validation_errors}
        Current Parameters: {parameters}
        Expected Schema: {action_schema["inputs_schema"]}
        Original Request: {user_request}
        
        Provide corrected parameters that match the schema.
        """

        repair_plan = self.llm.invoke(prompt).content

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

        return RepairOutput(
            repaired_parameters=repaired_parameters,
            repair_suggestions=suggestions
        )