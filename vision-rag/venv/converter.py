from fastapi import UploadFile
from docx2pdf import convert
import os
from logger import get_logger

logger = get_logger(__name__)

async def convert_docs_to_pdfs(files: list[UploadFile], folder_path: str):
    """
    Converts uploaded .doc and .docx files to PDFs asynchronously.
    """
    try:
        for file in files:
            if file.filename.lower().endswith(('.doc', '.docx')):
                file_path = os.path.join(folder_path, file.filename)
                pdf_path = os.path.splitext(file_path)[0] + '.pdf'
                
                # Save uploaded file temporarily
                with open(file_path, 'wb') as f:
                    content = await file.read()
                    f.write(content)
                
                # Convert to PDF
                convert(file_path, pdf_path)
                logger.info(f"Converted '{file.filename}' to PDF.")
                
                # Clean up original file
                os.remove(file_path)
                
    except Exception as e:
        logger.error(f"Error converting documents to PDFs: {e}")
        raise 