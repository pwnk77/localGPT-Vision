from fastapi import UploadFile
from byaldi import RAGMultiModalModel
from .converter import convert_docs_to_pdfs
from .logger import get_logger
import os
import re
import unicodedata
from fastapi import HTTPException

logger = get_logger(__name__)

def secure_filename(filename):
    """
    Replacement for werkzeug.utils.secure_filename
    """
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    filename = re.sub(r'[^\w\s.-]', '', filename).strip()
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename

async def index_documents(
    files: list[UploadFile], 
    session_id: str,
    folder_path: str,
    index_path: str,
    indexer_model: str = 'vidore/colpali'
) -> RAGMultiModalModel:
    """
    Indexes uploaded documents using Byaldi RAG model.
    """
    try:
        logger.info(f"Starting document indexing for session: {session_id}")
        
        # Create session folder
        os.makedirs(folder_path, exist_ok=True)
        
        # Save uploaded files
        saved_files = []
        for file in files:
            if file.filename:
                file_path = os.path.join(folder_path, secure_filename(file.filename))
                with open(file_path, 'wb') as f:
                    content = await file.read()
                    f.write(content)
                saved_files.append(file_path)
                logger.info(f"Saved file: {file_path}")
        
        if not saved_files:
            raise HTTPException(status_code=400, detail="No valid files uploaded")
        
        # Convert documents if needed
        await convert_docs_to_pdfs(files, folder_path)
        
        # Initialize RAG model
        RAG = RAGMultiModalModel.from_pretrained(indexer_model)
        if RAG is None:
            raise ValueError(f"Failed to initialize RAG model with {indexer_model}")
            
        # Index documents
        RAG.index(
            input_path=folder_path,
            index_name=session_id,
            store_collection_with_index=True,
            overwrite=True
        )
        
        logger.info(f"Indexing completed for session {session_id}")
        return RAG
        
    except Exception as e:
        logger.error(f"Error during indexing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))