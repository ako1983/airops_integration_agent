integration_agent/
│
├── config/
│   ├── __init__.py
│   └── observability.py
│
├── data/
│   ├── integration_actions.json     # Convert from .txt
│   ├── workflow_context.json        # Already exists
│   └── sample_requests.json         # Create test examples
│
├── src/
│   ├── __init__.py
│   ├── nlp.py                       # Natural Language Understanding
│   ├── action_selector.py           # Action Selection logic
│   ├── graph.py                     # Main LangGraph orchestration
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py
│   │   ├── action.py
│   │   └── workflow.py
│   │
│   └── nodes/
│       ├── __init__.py
│       ├── query_refiner.py
│       ├── planner.py
│       ├── schema_retriever.py
│       ├── generator.py
│       ├── validator.py
│       ├── repair.py
│       ├── workflow_generator.py
│       └── final_output.py
│
├── utils/
│   ├── __init__.py
│   ├── tracking.py
│   └── helpers.py
│
├── tests/
│   ├── __init__.py
│   └── test_integration.py
│
├── examples/
│   └── test_results.md
│
├── main.py                          # Entry point
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore