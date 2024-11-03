from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import json
from datetime import datetime

from .indexer import index_documents
from .retriever import retrieve_documents
from .responder import generate_response
from .logger import get_logger

# Initialize FastAPI app
app = FastAPI(title="briefcase-vision-rag-engine")
logger = get_logger(__name__)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure folders
UPLOAD_FOLDER = 'uploaded_documents'
SESSION_FOLDER = 'sessions'
INDEX_FOLDER = os.path.join(os.getcwd(), '.byaldi')

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SESSION_FOLDER, exist_ok=True)
os.makedirs(INDEX_FOLDER, exist_ok=True)

# Global RAG models dictionary
RAG_models = {}

# Pydantic models for request/response
class SessionCreate(BaseModel):
    name: Optional[str] = "Untitled Session"

class SessionRename(BaseModel):
    new_name: str

class ChatQuery(BaseModel):
    query: str
    model_choice: str = "qwen"
    resized_height: int = 280
    resized_width: int = 280

class Settings(BaseModel):
    indexer_model: str = "vidore/colpali"
    generation_model: str = "qwen"
    resized_height: int = 280
    resized_width: int = 280

# Helper functions
def get_session_data(session_id: str) -> dict:
    session_file = os.path.join(SESSION_FOLDER, f"{session_id}.json")
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            return json.load(f)
    return {"chat_history": [], "session_name": "Untitled Session", "indexed_files": []}

def save_session_data(session_id: str, data: dict):
    session_file = os.path.join(SESSION_FOLDER, f"{session_id}.json")
    with open(session_file, 'w') as f:
        json.dump(data, f)

# Endpoints
@app.post("/api/sessions/create")
async def create_session(session_data: SessionCreate):
    session_id = str(uuid.uuid4())
    session_data_dict = {
        "session_name": session_data.name,
        "chat_history": [],
        "indexed_files": [],
        "created_at": datetime.now().isoformat()
    }
    save_session_data(session_id, session_data_dict)
    return {"session_id": session_id, "data": session_data_dict}

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    data = get_session_data(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    try:
        # Remove session file
        session_file = os.path.join(SESSION_FOLDER, f"{session_id}.json")
        if os.path.exists(session_file):
            os.remove(session_file)

        # Remove uploaded documents
        session_uploads = os.path.join(UPLOAD_FOLDER, session_id)
        if os.path.exists(session_uploads):
            import shutil
            shutil.rmtree(session_uploads)

        # Remove from RAG models
        RAG_models.pop(session_id, None)

        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/sessions/{session_id}/rename")
async def rename_session(session_id: str, rename_data: SessionRename):
    data = get_session_data(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    data["session_name"] = rename_data.new_name
    save_session_data(session_id, data)
    return {"message": "Session renamed successfully"}

@app.post("/api/documents/upload")
async def upload_documents(
    session_id: str,
    files: List[UploadFile] = File(...),
    indexer_model: str = "vidore/colpali"
):
    try:
        folder_path = os.path.join(UPLOAD_FOLDER, session_id)
        index_path = os.path.join(INDEX_FOLDER, session_id)
        
        RAG = await index_documents(
            files=files,
            session_id=session_id,
            folder_path=folder_path,
            index_path=index_path,
            indexer_model=indexer_model
        )
        
        RAG_models[session_id] = RAG
        
        # Update session data
        session_data = get_session_data(session_id)
        session_data["indexed_files"].extend([file.filename for file in files])
        save_session_data(session_id, session_data)
        
        return {
            "success": True,
            "message": "Files indexed successfully",
            "indexed_files": session_data["indexed_files"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/{session_id}/query")
async def chat_query(session_id: str, query_data: ChatQuery):
    try:
        # Get RAG model
        rag_model = RAG_models.get(session_id)
        if not rag_model:
            raise HTTPException(status_code=404, detail="Session not initialized")
        
        # Retrieve relevant documents
        retrieved_images = await retrieve_documents(
            RAG=rag_model,
            query=query_data.query,
            session_id=session_id
        )
        
        # Generate response
        response = await generate_response(
            images=retrieved_images,
            query=query_data.query,
            session_id=session_id,
            resized_height=query_data.resized_height,
            resized_width=query_data.resized_width,
            model_choice=query_data.model_choice
        )
        
        # Update chat history
        session_data = get_session_data(session_id)
        session_data["chat_history"].append({
            "role": "user",
            "content": query_data.query,
            "timestamp": datetime.now().isoformat()
        })
        session_data["chat_history"].append({
            "role": "assistant",
            "content": response,
            "images": retrieved_images,
            "timestamp": datetime.now().isoformat()
        })
        save_session_data(session_id, session_data)
        
        return {
            "response": response,
            "images": retrieved_images
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/{session_id}/history")
async def get_chat_history(session_id: str):
    data = get_session_data(session_id)
    return {"chat_history": data["chat_history"]}

@app.get("/api/settings")
async def get_settings():
    # You might want to store these in a database or config file
    return Settings()

@app.put("/api/settings")
async def update_settings(settings: Settings):
    # Update settings (implement storage mechanism as needed)
    return settings

@app.get("/api/documents/{session_id}")
async def get_indexed_files(session_id: str):
    data = get_session_data(session_id)
    return {"indexed_files": data["indexed_files"]}

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up FastAPI application")
    # Load existing indexes if needed
    # Initialize any required resources

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down FastAPI application")
    # Cleanup resources if needed
