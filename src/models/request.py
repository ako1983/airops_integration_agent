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