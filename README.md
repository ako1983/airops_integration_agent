# Integration Agent for AirOps

A prototype AI agent that helps users configure integration actions using natural language requests and available context variables. Built with LangGraph, Claude AI, and includes observability through LangSmith and Weights & Biases.

## 🚀 Features

- **Natural Language Understanding**: Parse user requests to identify integration intents
- **Smart Action Selection**: Match user requests to available integration actions
- **Parameter Configuration**: Automatically map context variables to action parameters
- **Workflow Generation**: Create valid AirOps workflow definitions
- **Query Refinement**: Clarify ambiguous requests before processing
- **Full Observability**: Track performance with LangSmith and W&B

## 📋 Prerequisites

- Python 3.8+
- API Keys for:
  - Anthropic (Claude)
  - LangSmith
  - Weights & Biases (optional)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd integration_agent