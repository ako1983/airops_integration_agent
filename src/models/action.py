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