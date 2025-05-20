# config/observability.py
import os
import wandb
from typing import Dict, Any, Optional
os.environ["WANDB_NOTEBOOK_NAME"] = "airops_integration_agent"


class ObservabilityConfig:
    """Configuration for observability tools"""

    def __init__(self):
        # Initialize W&B only
        self.wandb_api_key = os.getenv("WANDB_API_KEY")
        self.wandb_project = os.getenv("WANDB_PROJECT", "airops-integration-agent")

        if self.wandb_api_key:
            wandb.login(key=self.wandb_api_key)
            wandb.init(project=self.wandb_project)

    def log_to_wandb(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """Log metrics to Weights & Biases"""
        if wandb.run:
            wandb.log(metrics, step=step)


