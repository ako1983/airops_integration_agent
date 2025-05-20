# test_nlp.py

import json
from src.nlp import parse_user_request

def test_nlp_component():
    print("Testing Natural Language Understanding...")
    
    # Load a sample of integration actions
    with open("data/integration_actions.json", "r") as f:
        integration_actions = json.load(f)
    
    # Test cases - simple requests
    test_requests = [
        "Create a new Webflow collection item with title 'New SEO Post'",
        "Send a message to Slack channel #general about our traffic increase",
        "Update the WordPress post with our SEO keywords",
        "Create a Google Doc with our content strategy"
    ]
    
    for request in test_requests:
        print(f"\nTesting request: '{request}'")
        parsed = parse_user_request(request, integration_actions)
        print(f"Platform: {parsed['platform']}")
        print(f"Action Intent: {parsed['action_intent']}")
        print(f"Entity Type: {parsed['entity_type']}")
        print(f"Parameters: {parsed['parameters']}")