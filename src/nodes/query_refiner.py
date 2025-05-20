# src/nodes/query_refiner.py
from langchain_core.tools import BaseTool
from langchain_community.chat_models import ChatAnthropic
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, ClassVar

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
    name: ClassVar[str] = "query_refiner"  # Add type annotation with ClassVar
    description: ClassVar[str] = "Evaluates and refines user queries for better integration matching"  # Add type annotation
    args_schema: ClassVar[type] = QueryRefinementInput  # Add type annotation

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