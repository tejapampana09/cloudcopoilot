from app.utils.database import SessionLocal
from sqlalchemy import text
import json

db = SessionLocal()
try:
    # Query the last 5 records from analyses table
    print("=== Fetching recent analysis tasks ===")
    result = db.execute(text("SELECT task_id, status, data FROM analyses ORDER BY created_at DESC LIMIT 5")).fetchall()
    
    for r in result:
        task_id, status, data_str = r
        print(f"\nTask ID: {task_id}")
        print(f"Status: {status}")
        try:
            data = json.loads(data_str)
            if "error" in data and data["error"]:
                print(f"Error Message: {data['error']}")
            else:
                print("No error details inside data json.")
        except Exception as ex:
            print(f"Failed to parse json: {ex}")
            print(f"Raw data: {data_str[:300]}...")
            
except Exception as e:
    print(f"Error querying PG: {e}")
finally:
    db.close()
