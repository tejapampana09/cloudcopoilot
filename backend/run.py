import logging
import uvicorn
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

# Load environmental variables from .env if present
load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
