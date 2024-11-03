from fastapi import HTTPException
from PIL import Image
from .model_loader import load_model
import base64
import os
from logger import get_logger
from io import BytesIO

logger = get_logger(__name__)

async def generate_response(
    images: list[str],
    query: str,
    session_id: str,
    resized_height: int = 280,
    resized_width: int = 280,
    model_choice: str = 'qwen'
) -> str:
    """
    Generates response using the selected model.
    """
    try:
        logger.info(f"Generating response using model '{model_choice}'")
        
        # Validate images
        valid_images = [img for img in images if os.path.exists(img)]
        if not valid_images:
            raise HTTPException(status_code=400, detail="No valid images found")
            
        # Load model
        model_data = await load_model(model_choice)
        
        # Process images
        processed_images = []
        for img_path in valid_images:
            image = Image.open(img_path)
            image = image.resize((resized_width, resized_height))
            processed_images.append(image)
        
        # Generate response based on model type
        if model_choice == 'qwen':
            model, processor, device = model_data
            inputs = processor(
                text=query,
                images=processed_images,
                return_tensors="pt"
            ).to(device)
            output = model.generate(**inputs, max_new_tokens=512)
            response_text = processor.decode(output[0], skip_special_tokens=True)
            
        elif model_choice == 'gemini':
            model, _, _ = model_data
            contents = [{"text": query}]
            for img in processed_images:
                img_bytes = BytesIO()
                img.save(img_bytes, format='PNG')
                contents.append({
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": base64.b64encode(img_bytes.getvalue()).decode()
                    }
                })
            response = model.generate_content(contents)
            response_text = response.text
            
        elif model_choice == 'gpt4':
            client, _, _ = model_data
            messages = [{"role": "user", "content": [{"type": "text", "text": query}]}]
            for img in processed_images:
                img_bytes = BytesIO()
                img.save(img_bytes, format='PNG')
                base64_image = base64.b64encode(img_bytes.getvalue()).decode()
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                })
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=500
            )
            response_text = response.choices[0].message.content
            
        # Add other model implementations as needed
        
        logger.info(f"Response generated for session {session_id}")
        return response_text
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 