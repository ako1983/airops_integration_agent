import json
import re

# Read the file
with open("data/integration_actions.txt", "r") as f:
    content = f.read()

# Extract JSON array
json_pattern = re.compile(r'\[\s*\{.*\}\s*\]', re.DOTALL)
json_match = json_pattern.search(content)

if json_match:
    json_str = json_match.group(0)
    actions = json.loads(json_str)

    # Save as JSON
    with open("data/integration_actions.json", "w") as f:
        json.dump(actions, f, indent=2)
    print("Successfully created integration_actions.json")
else:
    print("Failed to extract JSON from integration_actions.txt")