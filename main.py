from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from bson import ObjectId
from datetime import datetime
from typing import Dict, Any
import json
import logging
import traceback
from pymongo import MongoClient
from fetch import fetch_formatted_data, get_all_collections, JSONEncoder
from pydantic import BaseModel


# Add this class for request validation
class DataEntry(BaseModel):
    description: str
    type: str
    time: str


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

        # Fetch all documents and sort by time in descending order
        docs = list(collection.find().sort("time", -1))

        # Convert ObjectId to string and format dates
        formatted_docs = []
        for doc in docs:
            formatted_doc = {}
            for key, value in doc.items():
                if key == "_id":
                    formatted_doc[key] = str(value)
                elif isinstance(value, datetime):
                    # Format datetime to a more readable string
                    formatted_doc[key] = value.strftime("%Y-%m-%d %H:%M:%S")
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")
    finally:
        if client:
            client.close()


@app.get("/table")
async def table_view(request: Request, collection: str = "data"):
    try:
        # Get data using the fetch module
        formatted_docs = fetch_formatted_data(collection)
        collections = get_all_collections()

        # Convert to JSON string with custom encoder
        json_data = json.dumps(formatted_docs, cls=JSONEncoder, indent=2)

        return templates.TemplateResponse(
            "table.html",
            {
                "request": request,
                "collection": collection,
                "collections": collections,
                "formatted_docs": formatted_docs,
                "json_data": json_data,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/add-data")
async def add_data(data: DataEntry) -> Dict[str, Any]:
    client = None
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["telegram-secretary-bot"]
        collection = db["data"]

        # Convert string time to datetime object
        time_obj = datetime.fromisoformat(data.time)

        # Create document to insert
        document = {
            "description": data.description,
            "type": data.type,
            "time": time_obj,
            "created_at": datetime.utcnow(),
        }

        # Insert the document
        result = collection.insert_one(document)

        return {
            "status": "success",
            "message": "Data added successfully",
            "id": str(result.inserted_id),
        }
    except Exception as e:
        logging.error(f"Error adding data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add data: {str(e)}")
    finally:
        if client:
            client.close()


@app.on_event("shutdown")
async def shutdown_event():
    analyzer.close_connection()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
