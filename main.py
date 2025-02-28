from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel
import logging
import traceback
import json
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
from bson import ObjectId
from datetime import datetime

from llm import MongoDBLLMAnalyzer

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

# Initialize the LLM analyzer
try:
    analyzer = MongoDBLLMAnalyzer(
        connection_string="mongodb://localhost:27017/", db_name="restaurant"
    )
    logging.info("MongoDB LLM Analyzer initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize MongoDB LLM Analyzer: {str(e)}")
    raise

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


class AnalysisRequest(BaseModel):
    collection_name: str
    question: str
    context: str = ""  # Optional chat history context


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
        collections = analyzer.db.list_collection_names()
        return {"status": "healthy", "collections": collections}
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Database connection error: {str(e)}"
        )


@app.post("/analyze")
async def analyze_data(request: AnalysisRequest):
    try:
        logging.info(
            f"Received analysis request for collection '{request.collection_name}', question: '{request.question}'"
        )
        logging.info(f"Context length: {len(request.context.split(chr(10)))} messages")

        # Determine which collection to query based on the question
        collection_name = request.collection_name
        question = request.question.lower()

        # If the question is about restaurant info, history, etc. and not specifically about food
        if any(
            keyword in question
            for keyword in [
                "restaurant",
                "history",
                "about",
                "founded",
                "owner",
                "awards",
            ]
        ):
            # Check if the "about" collection exists and has data
            about_info = analyzer.get_collection_info("about")
            if about_info["exists"] and about_info["document_count"] > 0:
                collection_name = "about"
                logging.info(
                    f"Switching to 'about' collection based on question content"
                )

        collection_info = analyzer.get_collection_info(collection_name)
        if not collection_info["exists"]:
            return {
                "analysis": f"Sorry, I don't have information about '{collection_name}'"
            }

        if collection_info["document_count"] == 0:
            return {"analysis": f"The '{collection_name}' collection is empty."}

        response = analyzer.analyze_collection_with_llm(
            collection_name=collection_name,
            question=request.question,
            context=request.context,
        )

        logging.info(
            f"Successfully generated analysis response from {collection_name} collection"
        )
        return {"analysis": response}
    except Exception as e:
        error_msg = f"Error analyzing data: {str(e)}"
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/collections")
async def list_collections():
    try:
        collections = analyzer.db.list_collection_names()
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collection/{collection_name}")
async def get_collection_info(collection_name: str):
    try:
        info = analyzer.get_collection_info(collection_name)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/table")
async def get_table_info(
    request: Request, collection: str = "tables"
):  # Fixed parameter order
    try:
        # Get all collection names
        collections = analyzer.db.list_collection_names()

        # Get the specified collection
        collection_data = analyzer.db[collection]
        docs = list(collection_data.find())  # Get all documents

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

        # Format the raw data with proper indentation
        json_data = json.dumps(formatted_docs, indent=2, ensure_ascii=False)

        # Return template response with context
        return templates.TemplateResponse(
            "table.html",
            {
                "request": request,  # Required by FastAPI
                "collection": collection,
                "collections": collections,
                "json_data": json_data,
                "formatted_docs": formatted_docs,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    analyzer.close_connection()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
