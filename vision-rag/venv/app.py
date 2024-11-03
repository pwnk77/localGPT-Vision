from indexer import index_documents
from retriever import retrieve_documents
from responder import generate_response
from logger import get_logger

# Change these imports
from indexer import index_documents  # Remove 'models.'
from retriever import retrieve_documents  # Remove 'models.'
from responder import generate_response  # Remove 'models.'
from logger import get_logger

# rest of the file remains the same... 