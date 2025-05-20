# file_check.py
import os
import sys

def check_project_structure():
    """Verify the project structure and imports"""
    # Current directory and Python path
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}\n")
    
    # Essential directories
    essential_dirs = ["src", "config", "data", "utils", "tests"]
    print("Checking essential directories:")
    for dir_name in essential_dirs:
        exists = os.path.isdir(dir_name)
        print(f"  {dir_name}: {'✓' if exists else '✗'}")
    
    # Essential files
    essential_files = [
        "main.py",
        "src/__init__.py",
        "src/nlp.py",
        "src/action_selector.py",
        "src/graph.py",
        "src/nodes/query_refiner.py",
        "src/nodes/planner.py",
        "src/nodes/schema_retriever.py",
        "config/observability.py",
        "data/workflow_context.json"
    ]
    
    print("\nChecking essential files:")
    for file_path in essential_files:
        exists = os.path.isfile(file_path)
        print(f"  {file_path}: {'✓' if exists else '✗'}")
    
    # Import test
    print("\nTesting critical imports:")
    try:
        import src.nlp
        print("  src.nlp: ✓")
    except ImportError as e:
        print(f"  src.nlp: ✗ ({str(e)})")
    
    try:
        from src.graph import create_enhanced_integration_agent
        print("  src.graph.create_enhanced_integration_agent: ✓")
    except ImportError as e:
        print(f"  src.graph.create_enhanced_integration_agent: ✗ ({str(e)})")
    
    # Test integration actions
    print("\nChecking integration actions:")
    txt_exists = os.path.isfile("data/integration_actions.txt")
    json_exists = os.path.isfile("data/integration_actions.json")
    print(f"  integration_actions.txt: {'✓' if txt_exists else '✗'}")
    print(f"  integration_actions.json: {'✓' if json_exists else '✗'}")
    
    # Summary
    print("\nProject structure diagnosis:")
    if all([os.path.isdir(d) for d in essential_dirs]) and all([os.path.isfile(f) for f in essential_files]):
        print("✅ Basic project structure looks good!")
    else:
        print("⚠️ Some expected files or directories are missing.")
    
    if not json_exists and txt_exists:
        print("ℹ️ Run the conversion script to create integration_actions.json from the .txt file")
    elif not json_exists and not txt_exists:
        print("❌ Neither integration_actions.json nor .txt file found. These are required!")

if __name__ == "__main__":
    check_project_structure()