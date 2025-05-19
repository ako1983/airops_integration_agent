# config/observability.py
import os
from langsmith import Client
from langsmith.callbacks.langchain import LangChainCallbackHandler

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
        self.wandb_project = os.getenv("WANDB_PROJECT", "airops")

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