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