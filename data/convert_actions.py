import json
import re
import os

def convert_integration_actions():
    """Convert integration_actions.txt to JSON if JSON doesn't exist yet"""
    
    # Check paths
    input_path = "data/integration_actions.txt"
    output_path = "data/integration_actions.json"
    
    # Check if JSON already exists
    if os.path.exists(output_path):
        print(f"JSON file already exists at {output_path}")
        return True
    
    # Check if TXT file exists
    if not os.path.exists(input_path):
        print(f"Error: Text file not found at {input_path}")
        return False
    
    # Read the file
    try:
        with open(input_path, "r") as f:
            content = f.read()
        
        # Extract JSON array
        json_pattern = re.compile(r'\[\s*\{.*\}\s*\]', re.DOTALL)
        json_match = json_pattern.search(content)
        
        if json_match:
            json_str = json_match.group(0)
            actions = json.loads(json_str)
            
            # Save as JSON
            with open(output_path, "w") as f:
                json.dump(actions, f, indent=2)
            print(f"Successfully created {output_path}")
            return True
        else:
            print(f"Failed to extract JSON from {input_path}")
            return False
    except Exception as e:
        print(f"Error processing files: {str(e)}")
        return False

# Run the conversion
if __name__ == "__main__":
    convert_integration_actions()
