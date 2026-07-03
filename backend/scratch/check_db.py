import sqlite3
import json

db_path = "cloudpilot.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check analyses table
print("=== Analyses Table ===")
try:
    cursor.execute("SELECT task_id, status, data FROM analyses")
    rows = cursor.fetchall()
    for row in rows:
        task_id, status, data = row
        print(f"Task ID: {task_id} | Status: {status}")
        try:
            data_dict = json.loads(data)
            if "error" in data_dict and data_dict["error"]:
                print(f"  Error: {data_dict['error']}")
        except Exception:
            pass
except Exception as e:
    print(f"Error reading analyses table: {e}")

# Check deployments table
print("\n=== Deployments Table ===")
try:
    cursor.execute("SELECT deployment_id, status, data FROM deployments")
    rows = cursor.fetchall()
    for row in rows:
        dep_id, status, data = row
        print(f"Deployment ID: {dep_id} | Status: {status}")
        try:
            data_dict = json.loads(data)
            if "error" in data_dict and data_dict["error"]:
                print(f"  Error: {data_dict['error']}")
            if "logs" in data_dict:
                print(f"  Logs: {data_dict['logs']}")
        except Exception:
            pass
except Exception as e:
    print(f"Error reading deployments table: {e}")

conn.close()
