# models/model_loader.py

import os
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from transformers import MllamaForConditionalGeneration
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from logger import get_logger

logger = get_logger(__name__)

# Optional imports with error handling
try:
    from vllm import LLM
    from vllm.sampling_params import SamplingParams
    VLLM_AVAILABLE = True
except ImportError:
    logger.warning("VLLM not available. Some GPU functions will be limited.")
    VLLM_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    logger.warning("Groq not available.")
    GROQ_AVAILABLE = False

# Cache for loaded models
_model_cache = {}

def detect_device():
    """
    Detects the best available device (CUDA, MPS, or CPU).
    """
    if torch.cuda.is_available():
        return 'cuda'
    elif torch.backends.mps.is_available():
        return 'mps'
    else:
        return 'cpu'

def load_model(model_choice):
    """
    Loads and caches the specified model.
    """
    global _model_cache

    if model_choice in _model_cache:
        logger.info(f"Model '{model_choice}' loaded from cache.")
        return _model_cache[model_choice]

    if model_choice == 'qwen':
        device = detect_device()
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            "Qwen/Qwen2-VL-7B-Instruct",
            torch_dtype=torch.float16 if device != 'cpu' else torch.float32,
            device_map="auto"
        )
        processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")
        model.to(device)
        _model_cache[model_choice] = (model, processor, device)
        logger.info("Qwen model loaded and cached.")
        return _model_cache[model_choice]

    elif model_choice == 'gemini':
        # Load Gemini model
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-002')
        return model, None

    elif model_choice == 'llama-vision':
        device = detect_device()
        model_id = "alpindale/Llama-3.2-11B-Vision-Instruct"
        model = MllamaForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if device != 'cpu' else torch.float32,
            device_map="auto"
        )
        processor = AutoProcessor.from_pretrained(model_id)
        model.to(device)
        _model_cache[model_choice] = (model, processor, device)
        logger.info("Llama-Vision model loaded and cached.")
        return _model_cache[model_choice]
    
    elif model_choice == 'groq-llama-vision':
        if not GROQ_AVAILABLE:
            raise ImportError("Groq package not installed. Please install with 'pip install groq'")
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        client = Groq(api_key=api_key)
        _model_cache[model_choice] = client
        logger.info("Groq Llama Vision model loaded and cached.")
        return _model_cache[model_choice]
    
    else:
        logger.error(f"Invalid model choice: {model_choice}")
        raise ValueError("Invalid model choice.")
