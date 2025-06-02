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