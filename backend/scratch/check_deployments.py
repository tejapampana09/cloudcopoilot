from app.utils.database import SessionLocal
from sqlalchemy import text
import json

db = SessionLocal()
try:
    print("=== Fetching recent deployment tasks ===")
    result = db.execute(text("SELECT deployment_id, status, data FROM deployments ORDER BY created_at DESC LIMIT 5")).fetchall()
    
    for r in result:
        dep_id, status, data_str = r
        print(f"\nDeployment ID: {dep_id}")
        print(f"Status: {status}")
        try:
            data = json.loads(data_str)
            if "error" in data and data["error"]:
                print(f"  Error: {data['error']}")
            if "logs" in data and data["logs"]:
                print("  Logs:")
                for log in data["logs"]:
                    print(f"    [{log.get('stage')}] ({log.get('status')}): {log.get('message')}")
            else:
                print("  No logs found inside data json.")
        except Exception as ex:
            print(f"  Failed to parse json: {ex}")
            print(f"  Raw data: {data_str[:300]}...")
            
except Exception as e:
    print(f"Error querying PG: {e}")
finally:
    db.close()
