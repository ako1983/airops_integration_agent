# # Integration Agent for AirOps
# 
# This artifact contains the complete code for the Integration Agent prototype, a system that helps users configure integration actions using natural language requests and leverages context variables from workflow data.
# 
# ## Project Structure
# 
# ### ```
# integration_agent/
# │
# ├── config/
# │   ├── __init__.py
# │   └── observability.py
# │
# ├── data/
# │   ├── integration_actions.json
# │   ├── workflow_context.json
# │   └── sample_requests.json
# │
# ├── src/
# │   ├── __init__.py
# │   ├── nlp.py
# │   ├── action_selector.py
# │   ├── graph.py
# │   │
# │   ├── models/
# │   │   ├── __init__.py
# │   │   ├── request.py
# │   │   ├── action.py
# │   │   └── workflow.py
# │   │
# │   └── nodes/
# │       ├── __init__.py
# │       ├── query_refiner.py
# │       ├── planner.py
# │       ├── schema_retriever.py
# │       ├── generator.py
# │       ├── validator.py
# │       ├── repair.py
# │       ├── workflow_generator.py
# │       └── final_output.py
# │
# ├── utils/
# │   ├── __init__.py
# │   ├── tracking.py
# │   └── helpers.py
# │
# ├── tests/
# │   ├── __init__.py
# │   └── test_integration.py
# │
# ├── main.py
# ├── requirements.txt
# ├── README.md
# ├── .env.example
# └── .gitignore
# ### ```
# 
# ## Core Components:
# 
# ### 1. Natural Language Understanding (src/nlp.py)
# ### ### ```python 
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
# ### ```

### 2. Action Selection (src/action_selector.py)
# ### ### ```python 
# src/action_selector.py
from typing import Dict, List, Any

def select_integration_action(parsed_request: Dict[str, Any], integration_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Select the most appropriate integration action based on the parsed request.
    """
    # Filter actions by platform
    platform_actions = [
        action for action in integration_actions 
        if action["integration"].lower() == parsed_request["platform"].lower()
    ]
    
    if not platform_actions:
        return {
            "status": "error",
            "message": f"No actions available for platform: {parsed_request['platform']}",
            "action": None,
            "confidence": 0.0
        }
    
    # Score each action
    scored_actions = []
    for action in platform_actions:
        score = calculate_action_relevance(action, parsed_request)
        scored_actions.append({
            "action": action,
            "score": score
        })
    
    # Sort actions by score
    scored_actions.sort(key=lambda x: x["score"], reverse=True)
    
    # Get the best matching action
    best_match = scored_actions[0]
    
    # Determine if clarification is needed
    needs_clarification = False
    if len(scored_actions) > 1:
        if scored_actions[0]["score"] - scored_actions[1]["score"] < 0.3:
            needs_clarification = True
    
    return {
        "status": "success" if best_match["score"] > 0.5 else "low_confidence",
        "action": best_match["action"],
        "confidence": best_match["score"],
        "alternatives": [a["action"] for a in scored_actions[1:3]] if needs_clarification else [],
        "needs_clarification": needs_clarification
    }

def calculate_action_relevance(action: Dict[str, Any], parsed_request: Dict[str, Any]) -> float:
    """Calculate how relevant an action is to the parsed request."""
    score = 0.0
    
    action_name = action["action"].lower()
    action_intent = parsed_request["action_intent"].lower() if parsed_request["action_intent"] else ""
    entity_type = parsed_request["entity_type"].lower() if parsed_request["entity_type"] else ""
    
    # Check if action name contains intent words
    if action_intent and action_intent in action_name:
        score += 0.4
    
    # Check if action name contains entity type
    if entity_type and entity_type in action_name:
        score += 0.4
    
    # Check parameter overlap
    request_params = set(parsed_request["parameters"].keys())
    action_params = set(param["name"] for param in action["inputs_schema"])
    param_overlap = len(request_params.intersection(action_params))
    
    # Normalize parameter overlap score
    if len(request_params) > 0:
        score += 0.2 * (param_overlap / len(request_params))
    
    return min(score, 1.0)
# ### ```

### 3. Models (src/models/action.py)
### ### ### ```python  
# src/models/action.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

class ActionParameter(BaseModel):
    """Model for an integration action parameter"""
    name: str
    interface: str
    label: str
    hint: Optional[str] = None
    required: bool = False
    group_id: Optional[str] = "no-group"
    test_value: Optional[Any] = None
    options: Optional[List[str]] = None

class IntegrationAction(BaseModel):
    """Model for an integration action"""
    integration: str
    action: str
    definition: List[Dict[str, Any]]
    inputs_schema: List[ActionParameter]
    
    class Config:
        arbitrary_types_allowed = True

class SelectedAction(BaseModel):
    """Model for a selected action with confidence score"""
    action: IntegrationAction
    confidence: float = Field(ge=0.0, le=1.0)
    alternatives: List[IntegrationAction] = []
    needs_clarification: bool = False
### ```

### 4. Models (src/models/request.py)
### ### ### ```python  
# src/models/request.py
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class ParsedRequest(BaseModel):
    """Model for a parsed user request"""
    platform: Optional[str] = None
    action_intent: Optional[str] = None
    entity_type: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context_variables: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)

class IntegrationRequest(BaseModel):
    """Complete integration request with context"""
    user_request: str
    parsed_request: ParsedRequest
    context: Dict[str, Any]
    selected_action: Optional[Dict[str, Any]] = None
### ```

### 5. Models (src/models/workflow.py)
### ### ### ```python  
# src/models/workflow.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

class WorkflowInput(BaseModel):
    """Model for workflow input parameters"""
    name: str
    required: bool = True
    type: str  # "short_text", "long_text", "json", "single_select", "number"
    label: str
    group_id: str = "no-group"
    placeholder: Optional[str] = None
    test_value: Optional[Any] = None
    options: Optional[List[str]] = None

class StepConfig(BaseModel):
    """Model for step configuration"""
    # Fields vary by step type, using dict for flexibility
    pass

class WorkflowStep(BaseModel):
    """Model for a workflow step"""
    name: str
    type: str  # "text", "llm", "code", "integration", etc.
    config: Dict[str, Any]

class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""
    input_schema: List[WorkflowInput]
    definition: List[WorkflowStep]
### ```

### 6. Parameter Generation (src/nodes/generator.py)
### ### ```python 
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
### ```

### 7. Schema Retriever (src/nodes/schema_retriever.py)
### ### ```python 
# src/nodes/schema_retriever.py
from langchain.tools import BaseTool
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SchemaRetrieverInput(BaseModel):
    platform: str
    action_intent: str
    entity_type: str

class SchemaRetrieverOutput(BaseModel):
    matched_action: Optional[Dict[str, Any]] = None
    alternatives: List[Dict[str, Any]] = []
    needs_clarification: bool = False

class SchemaRetrieverTool(BaseTool):
    name = "schema_retriever"
    description = "Retrieves the schema for a specified integration action"
    args_schema = SchemaRetrieverInput
    
    def _run(self, platform: str, action_intent: str, entity_type: str) -> SchemaRetrieverOutput:
        """
        Retrieve the integration action that best matches the intent.
        This bridges our action_selector logic into the LangGraph node.
        """
        from src.models.action import IntegrationAction
        from src.action_selector import calculate_action_relevance
        import json
        
        # Load integration actions
        with open("data/integration_actions.json", "r") as f:
            actions_data = json.load(f)
            
        # Filter actions by platform
        platform_actions = [
            action for action in actions_data 
            if action["integration"].lower() == platform.lower()
        ]
        
        if not platform_actions:
            return SchemaRetrieverOutput(
                matched_action=None,
                alternatives=[],
                needs_clarification=False
            )
        
        # Create a mock parsed request for compatibility with action_selector
        mock_parsed_request = {
            "platform": platform,
            "action_intent": action_intent,
            "entity_type": entity_type,
            "parameters": {}
        }
        
        # Score and rank actions using our existing logic
        scored_actions = []
        for action in platform_actions:
            score = calculate_action_relevance(action, mock_parsed_request)
            scored_actions.append({
                "action": action,
                "score": score
            })
        
        # Sort by score
        scored_actions.sort(key=lambda x: x["score"], reverse=True)
        
        # Determine if clarification is needed
        needs_clarification = False
        if len(scored_actions) > 1:
            if scored_actions[0]["score"] - scored_actions[1]["score"] < 0.3:
                needs_clarification = True
        
        return SchemaRetrieverOutput(
            matched_action=scored_actions[0]["action"] if scored_actions else None,
            alternatives=[a["action"] for a in scored_actions[1:3]] if needs_clarification else [],
            needs_clarification=needs_clarification
        )
### ```

### 8. Validation Node (src/nodes/validator.py)
### ### ```python 
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
            if interface == "number" and not (isinstance(value, (int, float)) or str(value).replace(".", "", 1).isdigit()):
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
### ```

### 9. Workflow Generation (src/nodes/workflow_generator.py)
### ### ```python 
# src/nodes/workflow_generator.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from models.workflow import WorkflowDefinition, WorkflowStep, WorkflowInput

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
    name = "workflow_generator"
    description = "Generates a valid workflow definition for the integration action"
    args_schema = WorkflowGeneratorInput
    
    def _run(
        self, 
        action_schema: Dict[str, Any], 
        parameters: List[Dict[str, Any]],
        context_variables: Dict[str, Any],
        user_request: str
    ) -> WorkflowGeneratorOutput:
        """
        Generate a workflow that executes the integration action with proper configurations.
        """
        steps = []
        input_schema = []
        transformations_added = []
        
        # Analyze parameters to determine required transformations
        param_analysis = self._analyze_parameters(parameters, action_schema)
        
        # Add any necessary transformation steps
        if param_analysis["needs_json_parsing"]:
            steps.append(self._create_json_parser_step(param_analysis["json_params"]))
            transformations_added.append("JSON parsing")
            
        if param_analysis["needs_data_mapping"]:
            steps.append(self._create_data_mapping_step(param_analysis["mapping_params"]))
            transformations_added.append("Data mapping")
        
        # Create the main integration step
        integration_step = self._create_integration_step(action_schema, parameters, steps)
        steps.append(integration_step)
        
        # Create input schema based on required parameters
        input_schema = self._create_input_schema(parameters, action_schema)
        
        # Compile the workflow
        workflow = {
            "input_schema": input_schema,
            "definition": steps
        }
        
        # Generate explanation
        explanation = self._generate_explanation(action_schema, parameters, transformations_added)
        
        return WorkflowGeneratorOutput(
            workflow=workflow,
            transformations_added=transformations_added,
            explanation=explanation
        )
    
    def _analyze_parameters(self, parameters: List[Dict[str, Any]], action_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze parameters to determine required transformations"""
        json_params = []
        mapping_params = []
        
        # Get expected types from schema
        schema_types = {
            param["name"]: param.get("interface", "short_text") 
            for param in action_schema["inputs_schema"]
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
    
    def _create_input_schema(self, parameters: List[Dict[str, Any]], action_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
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
### ```

### 10. Final Output (src/nodes/final_output.py)
### ### ```python 
# src/nodes/final_output.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

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
    name = "final_output"
    description = "Prepares the final output for the user"
    args_schema = FinalOutputInput
    
    def _run(
        self, 
        workflow: Dict[str, Any], 
        action_schema: Dict[str, Any],
        confidence: float,
        explanation: str
    ) -> FinalOutputResult:
        """
        Prepare the final workflow output with validation and suggestions.
        """
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
        
        return FinalOutputResult(
            status=status,
            workflow=workflow,
            confidence=confidence,
            explanation=explanation,
            suggestions=suggestions,
            validation_warnings=validation_warnings
        )
    
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
        for param in action_schema["inputs_schema"]:
            if not param.get("required", False) and param["name"] not in used_params:
                unused_optional.append(param["name"])
        
        return unused_optional
### ```

### 11. Query Refiner (src/nodes/query_refiner.py)
### ### ```python 
# src/nodes/query_refiner.py
from langchain.tools import BaseTool
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class QueryRefinementInput(BaseModel):
    user_request: str
    available_integrations: List[str]
    context_variables: Dict[str, Any]

class ClarificationQuestion(BaseModel):
    question: str
    options: List[str] = []
    reason: str

class RefinedQuery(BaseModel):
    original_query: str
    refined_query: str
    extracted_entities: Dict[str, Any]
    confidence: float
    needs_clarification: bool
    clarification_questions: List[ClarificationQuestion] = []

class QueryRefinerNode(BaseTool):
    """
    Implements the query exploration pattern to evaluate, improve, and clarify user requests
    """
    name = "query_refiner"
    description = "Evaluates and refines user queries for better integration matching"
    args_schema = QueryRefinementInput
    
    def __init__(self, llm: ChatAnthropic):
        super().__init__()
        self.llm = llm
    
    def _run(
        self, 
        user_request: str, 
        available_integrations: List[str],
        context_variables: Dict[str, Any]
    ) -> RefinedQuery:
        """
        Analyze and refine the user's request
        """
        # Step 1: Initial Analysis
        analysis_prompt = f"""
        Analyze this integration request and determine if it's clear enough to proceed:
        
        REQUEST: "{user_request}"
        
        AVAILABLE INTEGRATIONS: {', '.join(available_integrations)}
        AVAILABLE CONTEXT VARIABLES: {list(context_variables.keys())}
        
        Consider:
        1. Is the target integration clear?
        2. Is the action intent obvious?
        3. Are all necessary parameters specified or available in context?
        4. Is there any ambiguity that needs clarification?
        
        Return a JSON object with:
        - is_clear: boolean
        - ambiguities: list of unclear aspects
        - missing_info: list of missing information
        - suggested_refinement: improved version of the query
        """
        
        analysis = self.llm.invoke(analysis_prompt).content
        
        # Step 2: Generate Clarification Questions if needed
        clarification_questions = []
        
        if not analysis.get("is_clear", True):
            clarification_prompt = f"""
            Generate clarification questions for these ambiguities:
            
            AMBIGUITIES: {analysis.get("ambiguities", [])}
            MISSING INFO: {analysis.get("missing_info", [])}
            
            For each unclear aspect, create a question with:
            - A clear, user-friendly question
            - Possible options (if applicable)
            - The reason why this clarification is needed
            
            Return a JSON list of clarification questions.
            """
            
            questions = self.llm.invoke(clarification_prompt).content
            clarification_questions = [ClarificationQuestion(**q) for q in questions]
        
        # Step 3: Refine the Query
        refinement_prompt = f"""
        Refine this user request to be more specific and actionable:
        
        ORIGINAL: "{user_request}"
        SUGGESTED IMPROVEMENTS: {analysis.get("suggested_refinement", "")}
        
        Create a refined version that:
        1. Clearly specifies the integration platform
        2. Explicitly states the action to perform
        3. References available context variables where appropriate
        4. Removes ambiguity
        
        Also extract key entities (platform, action, parameters) from the request.
        
        Return a JSON object with:
        - refined_query: the improved query
        - extracted_entities: dict of identified entities
        - confidence: 0.0-1.0 score
        """
        
        refinement = self.llm.invoke(refinement_prompt).content
        
        return RefinedQuery(
            original_query=user_request,
            refined_query=refinement.get("refined_query", user_request),
            extracted_entities=refinement.get("extracted_entities", {}),
            confidence=refinement.get("confidence", 0.5),
            needs_clarification=len(clarification_questions) > 0,
            clarification_questions=clarification_questions
        )
### ```

### 12. LangGraph Definition (src/graph.py)
### ### ```python 
# src/graph.py
from langgraph.graph import StateGraph
from langchain_anthropic import ChatAnthropic
from config.observability import ObservabilityConfig
from utils.tracking import PerformanceTracker
from nodes.query_refiner import QueryRefinerNode
from nodes.planner import PlannerNode
from nodes.schema_retriever import SchemaRetrieverTool
from nodes.generator import ParameterGeneratorTool
from nodes.validator import ParameterValidatorTool
from nodes.repair import RepairNode
from nodes.workflow_generator import WorkflowGeneratorTool
from nodes.final_output import FinalOutputNode
from typing import Dict, Any

def create_enhanced_integration_agent():
    """Create the enhanced integration agent with all components"""
    
    # Initialize observability
    observability = ObservabilityConfig()
    tracker = PerformanceTracker(observability)
    
    # Initialize LLM with LangSmith tracing
    llm = ChatAnthropic(
        model="claude-3-opus-20240229",
        callbacks=[observability.get_langsmith_handler()]
    )
    
    # Initialize state graph
    workflow = StateGraph()
    
    # Add all nodes
    workflow.add_node("query_refiner", QueryRefinerNode(llm=llm))
    workflow.add_node("planner", PlannerNode(llm=llm))
    workflow.add_node("schema_retriever", SchemaRetrieverTool())
    workflow.add_node("parameter_generator", ParameterGeneratorTool())
    workflow.add_node("validator", ParameterValidatorTool())
    workflow.add_node("repair", RepairNode(llm=llm))
    workflow.add_node("workflow_generator", WorkflowGeneratorTool())
    workflow.add_node("final_output", FinalOutputNode())
    
    # Define the flow
    workflow.add_edge("query_refiner", "planner")
    workflow.add_edge("planner", "schema_retriever")
    workflow.add_edge("schema_retriever", "parameter_generator")
    workflow.add_edge("parameter_generator", "validator")
    
    # Conditional routing
    def validation_router(state: Dict[str, Any]) -> str:
        if state["validator_output"]["is_valid"]:
            return "workflow_generator"
        else:
            return "repair"
    
    workflow.add_conditional_edges(
        "validator",
        validation_router,
        {
            "workflow_generator": "workflow_generator",
            "repair": "repair"
        }
    )
    
    workflow.add_edge("repair", "parameter_generator")
    workflow.add_edge("workflow_generator", "final_output")
    
    # Set entry point
    workflow.set_entry_point("query_refiner")
    
    # Apply tracking to all nodes
    for node_name in workflow.nodes:
        original_node = workflow.nodes[node_name]
        workflow.nodes[node_name] = tracker.track_execution(node_name)(original_node)
    
    return workflow.compile()
### ```

### 13. Main Testing Script (main.py)
### ### ```python 
# main.py
import json
from src.graph import create_enhanced_integration_agent
from utils.helpers import load_integration_actions, load_workflow_context

def test_integration_agent():
    """Test the integration agent with sample requests"""
    
    # Load data
    integration_actions = load_integration_actions()
    workflow_context = load_workflow_context()
    
    # Test cases
    test_requests = [
        {
            "request": "Create a new Webflow collection item using the top keyword from our SEO analysis",
            "context": workflow_context
        },
        {
            "request": "Send a Slack notification about our traffic increase",
            "context": workflow_context
        },
        {
            "request": "Create a WordPress post about our best performing page",
            "context": workflow_context
        }
    ]
    
    # Initialize agent
    agent = create_enhanced_integration_agent()
    
    # Run tests
    results = []
    for test in test_requests:
        print(f"\n{'='*50}")
        print(f"Testing: {test['request']}")
        print(f"{'='*50}")
        
        try:
            result = agent.run({
                "user_request": test["request"],
                "context": test["context"],
                "integration_actions": integration_actions
            })
            
            print(f"Status: {result.get('status', 'Unknown')}")
            print(f"Confidence: {result.get('confidence', 0.0):.2f}")
            
            if result.get('workflow'):
                print("\nGenerated Workflow:")
                print(json.dumps(result['workflow'], indent=2))
            
            if result.get('clarification_questions'):
                print("\nClarification Needed:")
                for q in result['clarification_questions']:
                    print(f"- {q['question']}")
            
            results.append({
                "request": test["request"],
                "result": result
            })
            
        except Exception as e:
            print(f"Error: {str(e)}")
            results.append({
                "request": test["request"],
                "error": str(e)
            })
    
    # Save results
    with open("examples/test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    test_integration_agent()
### ```

### 14. Helper Functions (utils/helpers.py)
### ### ```python 
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
### ```

### 15. Observability Config (config/observability.py)
### ### ```python 
# config/observability.py
import os
from langsmith import Client
from langchain.callbacks import LangSmithCallbackHandler
import wandb
from typing import Dict, Any, Optional

class ObservabilityConfig:
    """Configuration for observability tools"""
    
    def __init__(self):
        # Initialize LangSmith
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT", "integration-agent")
        self.langsmith_client = Client(api_key=self.langsmith_api_key)
        
        # Initialize Weights & Biases
        self.wandb_api_key = os.getenv("WANDB_API_KEY")
        self.wandb_project = os.getenv("WANDB_PROJECT", "airops-integration-agent")
        
        if self.wandb_api_key:
            wandb.login(key=self.wandb_api_key)
            wandb.init(project=self.wandb_project)
    
    def get_langsmith_handler(self) -> LangSmithCallbackHandler:
        """Get LangSmith callback handler for tracing"""
        return LangSmithCallbackHandler(
            project_name=self.langsmith_project,
            client=self.langsmith_client
        )
    
    def log_to_wandb(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """Log metrics to Weights & Biases"""
        if wandb.run:
            wandb.log(metrics, step=step)
### ```

### 16. Performance Tracking (utils/tracking.py)
### ### ```python 
# utils/tracking.py
from typing import Dict, Any, Optional
import time
from functools import wraps

class PerformanceTracker:
    """Track performance metrics for the integration agent"""
    
    def __init__(self, observability_config):
        self.config = observability_config
        self.metrics = {}
    
    def track_execution(self, step_name: str):
        """Decorator to track execution time and success rate"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    execution_time = time.time() - start_time
                    
                    # Log to W&B
                    self.config.log_to_wandb({
                        f"{step_name}_execution_time": execution_time,
                        f"{step_name}_success": success,
                        f"{step_name}_error": error
                    })
                    
                    # Store metrics
                    if step_name not in self.metrics:
                        self.metrics[step_name] = {
                            "executions": 0,
                            "successes": 0,
                            "total_time": 0.0
                        }
                    
                    self.metrics[step_name]["executions"] += 1
                    if success:
                        self.metrics[step_name]["successes"] += 1
                    self.metrics[step_name]["total_time"] += execution_time
            
            return wrapper
        return decorator
### ```
#
# ## Testing Instructions
#
# 1. **Set up environment**:
#    - Create and activate a virtual environment
#    - Install dependencies: `pip install -r requirements.txt`
#    - Configure `.env` with API keys
#
# 2. **Convert integration_actions.txt to JSON**:
#    - Import json and regex
#    - Extract the JSON array from the content
#    - Save it as data/integration_actions.json
#
# 3. **Run the tests**:
#    - Start with individual components: `python -c "from src.nlp import parse_user_request; ..."`
#    - Run full integration test: `python main.py`
#
# 4. **Check results**:
#    - Review terminal output
#    - Examine generated workflows in examples/test_results.json
#    - View traces in LangSmith dashboard
#    - Check metrics in W&B dashboard
