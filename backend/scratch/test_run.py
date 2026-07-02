import os
import sys
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

from app.agents.graph import run_analysis_pipeline
from app.utils.helpers import analysis_tasks

task_id = "test-task-123"
repo_url = "https://github.com/fastapi/fastapi"
# Create a unique temp folder
clone_path = os.path.join("temp_clones", task_id)

# Initialize tasks dict
analysis_tasks[task_id] = {
    "logs": []
}

try:
    res = run_analysis_pipeline(task_id, repo_url, clone_path)
    print("Pipeline Result:")
    print("Status:", res.get("status"))
    print("Error:", res.get("error"))
    print("Logs:")
    for l in res.get("logs", []):
        print(f"[{l.get('agent')}] {l.get('message')} ({l.get('status')})")
except Exception as e:
    import traceback
    print("CRASHED:")
    traceback.print_exc()
