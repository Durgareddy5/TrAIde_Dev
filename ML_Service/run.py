import uvicorn
import os

PORT = int(os.getenv("PORT", 8001))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)