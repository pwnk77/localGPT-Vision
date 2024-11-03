# Similar to original but with async support
from fastapi import HTTPException
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import os
from dotenv import load_dotenv
import google.generativeai as genai
from .logger import get_logger

load_dotenv()
logger = get_logger(__name__)

_model_cache = {}

def detect_device():
    if torch.cuda.is_available():
        return 'cuda'
    elif torch.backends.mps.is_available():
        return 'mps'
    else:
        return 'cpu'

async def load_model(model_choice: str):
    """
    Asynchronously loads and caches AI models.
    """
    if model_choice in _model_cache:
        return _model_cache[model_choice]

    try:
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
            
        elif model_choice == 'gemini':
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not found")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            _model_cache[model_choice] = (model, None, None)
            
        elif model_choice == 'gpt4':
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise HTTPException(status_code=500, detail="OPENAI_API_KEY not found")
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            _model_cache[model_choice] = (client, None, None)
            
        elif model_choice == 'llama':
            # Add Llama model implementation
            pass
            
        elif model_choice == 'pixtral':
            # Add Pixtral model implementation
            pass
            
        elif model_choice == 'molmo':
            # Add Molmo model implementation
            pass
            
        logger.info(f"Model {model_choice} loaded and cached.")
        return _model_cache[model_choice]
        
    except Exception as e:
        logger.error(f"Error loading model {model_choice}: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading model: {str(e)}") 