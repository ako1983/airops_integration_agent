# main.py
import sys
import os

from dotenv import load_dotenv
load_dotenv()  # Load variables from .env file

# Get the absolute path to the project root (directory containing main.py)
# project_root = os.path.dirname(os.path.abspath(__file__)) # or via getcwd
project_root = os.path.dirname(os.getcwd())
sys.path.insert(0, project_root)

import json
from src.graph import create_enhanced_integration_agent
from utils.helpers import load_integration_actions, load_workflow_context


def test_integration_agent():
    """
    Test the AirOps Integration Agent with sample natural language requests.

    - Loads integration actions and workflow context.
    - Runs the agent on each test request.
    - Prints status, confidence, workflow, and clarification questions.
    - Saves all results to 'examples/test_results.json'.

    Returns:
        List of results for each test request.
    """
    
    # Load data
    integration_actions = load_integration_actions()
    workflow_context = load_workflow_context()
    
    # Test cases
    test_requests = [
        {
            "request": "Create a new Webflow collection item using the top keyword from our SEO analysis",
            "context": workflow_context
        },
        {
            "request": "Send a Slack notification about our traffic increase",
            "context": workflow_context
        },
        {
            "request": "Generate a WordPress post about our best performing page",
            "context": workflow_context
        }
    ]
    
    # Initialize agent
    agent = create_enhanced_integration_agent()
    
    # Run tests
    results = []
    for test in test_requests:
        print(f"\n{'='*50}")
        print(f"Testing: {test['request']}")
        print(f"{'='*50}")
        
        try:
            result = agent.run({
                "user_request": test["request"],
                "context": test["context"],
                "integration_actions": integration_actions
            })
            
            print(f"Status: {result.get('status', 'Unknown')}")
            print(f"Confidence: {result.get('confidence', 0.0):.2f}")
            
            if result.get('workflow'):
                print("\nGenerated Workflow:")
                print(json.dumps(result['workflow'], indent=2))
            
            if result.get('clarification_questions'):
                print("\nClarification Needed:")
                for q in result['clarification_questions']:
                    print(f"- {q['question']}")
            
            results.append({
                "request": test["request"],
                "result": result
            })
            
        except Exception as e:
            print(f"Error: {str(e)}")
            results.append({
                "request": test["request"],
                "error": str(e)
            })
    
    # Save results
    with open("examples/test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    test_integration_agent()
