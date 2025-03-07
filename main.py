from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import logging
import traceback
from fastapi.templating import Jinja2Templates
from pathlib import Path
from bson import ObjectId
from datetime import datetime
from pymongo import MongoClient
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()

# Create static directory if it doesn't exist
static_dir = Path("static")
if not static_dir.exists():
    static_dir.mkdir(parents=True)

# Mount static files - mount before other routes
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory=".")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add favicon endpoint
@app.get("/favicon.ico")
async def favicon():
    favicon_path = static_dir / "favicon.ico"
    if not favicon_path.exists():
        # If favicon doesn't exist, create a default transparent one
        from PIL import Image

        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        img.save(favicon_path, "ICO")
    return FileResponse(favicon_path)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = f"Unhandled error: {str(exc)}"
    logging.error(error_msg)
    logging.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": error_msg},
    )


@app.get("/")
async def root():
    return FileResponse("index.html")


@app.get("/health")
async def health_check():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["telegram-secretary-bot"]
        collections = db.list_collection_names()
        client.close()
        return {"status": "healthy", "collections": collections}
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Database connection error: {str(e)}"
        )


@app.get("/telegram-data")
async def get_telegram_data() -> Dict[str, Any]:
    client = None
    try:
        # Create a new client connection to telegram-secretary-bot database
        client = MongoClient("mongodb://localhost:27017/")
        db = client["telegram-secretary-bot"]
        collection = db["data"]

        # Fetch all documents
        docs = list(collection.find())

        # Convert ObjectId to string and format dates
        formatted_docs = []
        for doc in docs:
            formatted_doc = {}
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    formatted_doc[key] = str(value)
                elif isinstance(value, datetime):
                    formatted_doc[key] = value.isoformat()
                else:
                    formatted_doc[key] = value
            formatted_docs.append(formatted_doc)

        return {
            "status": "success",
            "count": len(formatted_docs),
            "data": formatted_docs,
        }
    except Exception as e:
        logging.error(f"Error fetching telegram data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch data from telegram-secretary-bot: {str(e)}",
        )
    finally:
        if client:
            client.close()


@app.on_event("shutdown")
async def shutdown_event():
    analyzer.close_connection()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
