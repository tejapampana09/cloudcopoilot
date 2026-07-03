from app.utils.database import SessionLocal
from sqlalchemy import text
import json

db = SessionLocal()
try:
    print("=== Fetching console logs of the most recent failed deployment ===")
    result = db.execute(text("SELECT deployment_id, status, data FROM deployments WHERE status = 'failed' ORDER BY created_at DESC LIMIT 1")).fetchone()
    
    if result:
        dep_id, status, data_str = result
        print(f"Deployment ID: {dep_id}")
        data = json.loads(data_str)
        print(f"Error field: {data.get('error')}")
        
        console = data.get("console", [])
        print(f"Total console output lines: {len(console)}")
        print("=== Console Output (Last 30 lines) ===")
        for line in console[-30:]:
            print(line)
    else:
        print("No failed deployments found.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
