from fastapi import HTTPException
from PIL import Image
from io import BytesIO
import base64
import os
import hashlib
from .logger import get_logger

logger = get_logger(__name__)

async def retrieve_documents(
    RAG,
    query: str,
    session_id: str,
    k: int = 3
) -> list[str]:
    """
    Retrieves relevant documents based on query.
    """
    try:
        logger.info(f"Retrieving documents for query: {query}")
        
        results = RAG.search(query, k=k)
        images = []
        session_images_folder = os.path.join('uploaded_documents', session_id, 'images')
        os.makedirs(session_images_folder, exist_ok=True)
        
        for result in results:
            if result.base64:
                # Process and save image
                image_data = base64.b64decode(result.base64)
                image = Image.open(BytesIO(image_data))
                
                # Generate unique filename
                image_hash = hashlib.md5(image_data).hexdigest()
                image_filename = f"retrieved_{image_hash}.png"
                image_path = os.path.join(session_images_folder, image_filename)
                
                if not os.path.exists(image_path):
                    image.save(image_path, format='PNG')
                    
                images.append(image_path)
                
        logger.info(f"Retrieved {len(images)} images for session {session_id}")
        return images
        
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 