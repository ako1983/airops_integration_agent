# AirOps Integration Agent

## Overview
The AirOps Integration Agent is a prototype system that enables users to configure and execute integration actions (e.g., create a Webflow item, send a Slack notification, post to WordPress) using natural language requests. It leverages workflow context and available integration actions to generate structured, executable workflows.

## Features
- **Natural Language Understanding**: Parses user requests to extract intent, platform, entity type, and parameters.
- **Action Selection**: Matches parsed requests to the most relevant integration action using scoring logic.
- **Schema Retrieval**: Retrieves the schema for the selected action to understand required parameters.
- **Parameter Generation & Validation**: Extracts and validates parameters from the user request and context.
- **Workflow Generation**: Assembles a workflow definition, including necessary data transformations.
- **Observability & Tracking**: Integrates with LangSmith and Weights & Biases for tracing and performance monitoring.
- **Testing**: Includes scripts to test the agent with sample requests and output the generated workflows.

## Project Structure
```
airops_integration_agent/
├── config/
│   └── observability.py
├── data/
│   ├── integration_actions.txt / .json
│   ├── workflow_context.json
│   └── sample_requests.json
├── src/
│   ├── nlp.py
│   ├── action_selector.py
│   ├── graph.py
│   ├── models/
│   │   ├── action.py
│   │   ├── request.py
│   │   └── workflow.py
│   ├── nodes/
│   │   ├── query_refiner.py
│   │   ├── planner.py
│   │   ├── schema_retriever.py
│   │   ├── generator.py
│   │   ├── validator.py
│   │   ├── repair.py
│   │   ├── workflow_generator.py
│   │   └── final_output.py
│   └── tests/
│       ├── test_integration.py
│       └── test_nlp.py
├── utils/
│   ├── helpers.py
│   └── tracking.py
├── main.py
├── requirements.txt
└── README.md
```

## How It Works
1. **User Request Parsing**: The agent parses a natural language request to identify the target platform, action intent, entity type, and parameters.
2. **Action Selection**: It selects the most relevant integration action from available options.
3. **Schema Retrieval**: Retrieves the schema for the selected action to determine required parameters.
4. **Parameter Generation & Validation**: Extracts parameters from the request/context and validates them.
5. **Workflow Generation**: Generates a workflow definition, including any necessary data transformations.
6. **Execution & Output**: Outputs the workflow or requests clarification if needed.

## Example Usage
Run the test script to see the agent in action:
```bash
python main.py
```
This will process sample requests and print the generated workflows and any clarification questions.

## Extending the Agent
- **Add new integrations**: Update `data/integration_actions.txt` or `.json` with new actions.
- **Improve NLP**: Enhance `src/nlp.py` for more robust request parsing.
- **Add nodes**: Implement new workflow steps in `src/nodes/` as needed.

## Observability & Tracking
- **LangSmith**: Used for tracing LLM calls and agent steps.
- **Weights & Biases (wandb)**: Used for performance tracking.

## Requirements
- Python 3.10+
- See `requirements.txt` for dependencies.

## Contributing
1. Fork the repo and create a feature branch.
2. Add or update tests in `src/tests/`.
3. Submit a pull request with a clear description.

## License
MIT License

---

For more details, see the code and docstrings in each module.
