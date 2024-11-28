import os
import json
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import uuid
from typing import Dict, Any, List
from PIL import Image
import fitz  # PyMuPDF
from datetime import datetime
import time
import requests
import torch
from transformers import AutoModelForCausalLM, AutoProcessor
import pymupdf4llm
import pathlib

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")
genai.configure(api_key=api_key)

# Constants for rate limiting (Gemini only)
BATCH_SIZE = 5
SLEEP_BETWEEN_CALLS = 2  # seconds between API calls
SLEEP_BETWEEN_BATCHES = 60  # seconds between batches

# Ollama configuration
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
LLAMA_MODEL = "llama3.2-vision:latest"

def detect_device():
    """Detect the available compute device"""
    if torch.cuda.is_available():
        return 'cuda'
    elif torch.backends.mps.is_available():
        return 'mps'
    else:
        return 'cpu'

class ModelType:
    GEMINI = "gemini"
    LLAMA = "llama"
    QWEN = "qwen"
    LLAMA_PDF = "llama_pdf"  # New option for pymupdf4llm

# Configure Gemini
generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

class PDFBatchProcessor:
    def __init__(self, model_type: str = "llama", data_folder: str = "data", batch_size: int = 5):
        self.model_type = model_type
        self.data_folder = data_folder
        self.batch_size = batch_size
        
        # Set device
        self.device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
        print(f"\nInitializing {model_type} on {self.device}...")
        
        if model_type == ModelType.QWEN:
            try:
                # Check for HF token
                token = os.getenv("HF_TOKEN")
                if not token:
                    print("\nError: HF_TOKEN environment variable not found!")
                    print("Please set your Hugging Face token:")
                    print("1. Get your token from https://huggingface.co/settings/tokens")
                    print("2. Set it in your environment: export HF_TOKEN='your_token'")
                    raise ValueError("HF_TOKEN not found")

                print("Loading Qwen model and processor...")
                model_id = "Qwen/Qwen2-VL-7B-Chat"
                
                # Use AutoModelForVision2Seq or AutoModelForCausalLM depending on version
                try:
                    from transformers import AutoModelForVision2Seq
                    model_class = AutoModelForVision2Seq
                except ImportError:
                    from transformers import AutoModelForCausalLM
                    model_class = AutoModelForCausalLM
                
                self.processor = AutoProcessor.from_pretrained(
                    model_id,
                    token=token,
                    trust_remote_code=True
                )
                
                self.model = model_class.from_pretrained(
                    model_id,
                    token=token,
                    device_map="auto",
                    trust_remote_code=True
                )
                print("Qwen model loaded successfully!")
                
            except Exception as e:
                print(f"\nError initializing Qwen model: {str(e)}")
                print("\nPlease make sure you:")
                print("1. Have a valid Hugging Face token")
                print("2. Have accepted the model terms at https://huggingface.co/Qwen/Qwen2-VL-7B-Chat")
                print("3. Have set the HF_TOKEN environment variable")
                raise
        elif model_type == ModelType.GEMINI:
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-pro',
                generation_config=generation_config,
                safety_settings=safety_settings
            )
        elif model_type == ModelType.LLAMA:
            # No initialization needed for Ollama
            pass
        elif model_type == ModelType.LLAMA_PDF:
            self.parser = PDFParser()
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Create data folder if it doesn't exist
        os.makedirs(self.data_folder, exist_ok=True)
    
    def process_with_qwen(self, prompt: str, image: Image) -> str:
        """Process with Qwen model"""
        inputs = self.processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        ).to(self.device)
        
        output = self.model.generate(
            **inputs,
            max_new_tokens=512
        )
        
        response_text = self.processor.decode(output[0], skip_special_tokens=True)
        return response_text
    
    def call_ollama_api(self, prompt: str, image_path: str) -> str:
        """Call Ollama API for image processing with JSON format"""
        try:
            # Prepare the API request
            url = "http://localhost:11434/api/generate"
            
            # Read image as base64
            with open(image_path, "rb") as image_file:
                import base64
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Add JSON format instruction to prompt
            json_prompt = f"""
            Format the response as valid JSON with three keys: Control_Objectives, Test_Requirements, and Guidance.
            {prompt}
            Format: json
            """
            
            # Prepare the request payload
            payload = {
                "model": "llama3.2-vision",
                "prompt": json_prompt,
                "stream": False,
                "images": [image_base64],
                "format": "json"
            }
            
            # Make the API call
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            # Parse and return the response
            result = response.json()
            return result.get('response', 'No content extracted')
            
        except requests.exceptions.RequestException as e:
            print(f"\nError calling Ollama API: {str(e)}")
            if "Connection refused" in str(e):
                print("\nPlease make sure Ollama is running and the model is installed:")
                print("1. Start Ollama service")
                print("2. Run: ollama pull llama3.2-vision:latest")
            raise
    
    def process_page(self, pdf_doc, page_num: int, output_file: str, all_responses: list) -> Dict:
        """Process a single page and return the JSON response"""
        try:
            print(f"\nProcessing page {page_num + 1}...")
            
            # Convert PDF page to image
            page = pdf_doc[page_num]
            pix = page.get_pixmap()
            
            # Save temporary image
            temp_image_path = os.path.join(self.data_folder, f"temp_page_{page_num}.png")
            pix.save(temp_image_path)
            
            # Load image
            image = Image.open(temp_image_path)
            
            # Create structured prompt for table extraction
            prompt = """Analyze this table from a security requirements document. Focus only on extracting the content within the three-column table structure, ignoring any merged header rows or text outside the table.

For each row in the table, extract:
- Column 1 "Control_Objectives": The control objective ID (e.g., 1.1) and its description
- Column 2 "Test_Requirements": The test requirements with their IDs (e.g., 1.1.a, 1.1.b, etc.)
- Column 3 "Guidance": The guidance text for that row

Format the response as a JSON object with this exact structure:
{
    "table_rows": [
        {
            "control_objective": {
                "id": "1.1",
                "text": "The full text of the control objective"
            },
            "test_requirements": [
                {
                    "id": "1.1.a",
                    "text": "The full text of this test requirement"
                },
                {
                    "id": "1.1.b",
                    "text": "The full text of this test requirement"
                }
            ],
            "guidance": "The full guidance text for this row"
        }
    ]
}

Important:
- Preserve the exact text as shown in the table
- Include all IDs (like 1.1, 1.1.a) exactly as they appear
- Each table row should be a separate object in the table_rows array
- Capture all test requirements for each control objective"""
            
            print(f"Sending request to {self.model_type.upper()} API...")
            
            try:
                if self.model_type == ModelType.GEMINI:
                    response = self.model.generate_content(
                        contents=[prompt, image],
                        stream=False
                    )
                    response_text = response.text if response.text else "No content extracted"
                elif self.model_type == ModelType.QWEN:
                    response_text = self.process_with_qwen(prompt, image)
                else:  # LLAMA
                    response_text = self.call_ollama_api(prompt, temp_image_path)
                
                # Try to parse JSON to verify format
                try:
                    json_content = json.loads(response_text)
                    # Save only the content without metadata
                    all_responses.append(json_content)
                    
                    # Save to file after each successful extraction
                    with open(output_file, 'w') as f:
                        json.dump(all_responses, f, indent=2)
                    
                    print("\nAPI Response Structure:")
                    print(f"Control Objectives: {len(json_content.get('Control_Objectives', []))} items")
                    print(f"Test Requirements: {len(json_content.get('Test_Requirements', []))} items")
                    print(f"Guidance: {len(json_content.get('Guidance', []))} items")
                    
                    return json_content
                    
                except json.JSONDecodeError:
                    print("\nWarning: Response is not in valid JSON format")
                    print("Raw response:")
                    print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                    raise
                
            finally:
                # Clean up temporary image file
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                    
        except Exception as e:
            error_response = {
                "error": str(e),
                "status": "error"
            }
            all_responses.append(error_response)
            
            # Save to file even if there's an error
            with open(output_file, 'w') as f:
                json.dump(all_responses, f, indent=2)
            
            return error_response
    
    def process_pdf_in_batches(self, start_page: int, end_page: int):
        """Process PDF pages in batches and save results"""
        try:
            # Open PDF
            pdf_path = os.path.join(self.data_folder, "PCI-Secure-Software-Standard-v1_2_1.pdf")
            pdf_doc = fitz.open(pdf_path)
            
            # Adjust page numbers to 0-based indexing
            start_idx = start_page - 1
            end_idx = min(end_page - 1, len(pdf_doc) - 1)
            
            # Create output file for raw responses
            output_file = os.path.join(self.data_folder, f"pci_extractions_{self.model_type}_{start_page}-{end_page}.json")
            
            # Initialize or load existing responses
            if os.path.exists(output_file):
                print(f"\nFound existing output file: {output_file}")
                with open(output_file, 'r') as f:
                    all_responses = json.load(f)
                # Find the last processed page
                last_page = max(r['page_number'] for r in all_responses)
                print(f"Resuming from page {last_page + 1}")
                start_idx = last_page
            else:
                print(f"\nStarting new extraction: {output_file}")
                all_responses = []
            
            # Process in batches
            current_batch = []
            
            print(f"\nProcessing pages {start_page} to {end_page}")
            if self.model_type == ModelType.GEMINI:
                print(f"Processing in batches of {self.batch_size}")
                print(f"Sleep intervals: {SLEEP_BETWEEN_CALLS}s between calls, {SLEEP_BETWEEN_BATCHES}s between batches")
            
            for page_num in range(start_idx, end_idx + 1):
                # Process page
                response = self.process_page(pdf_doc, page_num, output_file, all_responses)
                current_batch.append(response)
                
                # If using Gemini and batch is complete, sleep before next batch
                if self.model_type == ModelType.GEMINI and len(current_batch) == self.batch_size and page_num != end_idx:
                    print(f"\nBatch complete. Sleeping for {SLEEP_BETWEEN_BATCHES} seconds...")
                    current_batch = []
                    time.sleep(SLEEP_BETWEEN_BATCHES)
            
            pdf_doc.close()
            print("\nProcessing completed!")
            print(f"Final output saved to: {output_file}")
            
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
    
    def call_ollama_api_for_text(self, prompt: str) -> str:
        """Call Ollama API for text processing with JSON format"""
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": "llama3.1:latest",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', 'No content extracted')
            
        except requests.exceptions.RequestException as e:
            print(f"\nError calling Ollama API: {str(e)}")
            if "Connection refused" in str(e):
                print("\nPlease make sure Ollama is running and the model is installed:")
                print("1. Start Ollama service")
                print("2. Run: ollama pull llama3.1:latest")
            raise
    
    def process_with_pymupdf(self, pdf_doc, page_num: int, output_file: str, all_responses: list) -> Dict:
        """Process a single page using pymupdf4llm and llama3.1"""
        try:
            print(f"\nProcessing page {page_num + 1} with pymupdf4llm...")
            
            # Save current page as temporary PDF
            temp_pdf_path = os.path.join(self.data_folder, f"temp_page_{page_num}.pdf")
            temp_md_path = os.path.join(self.data_folder, f"temp_page_{page_num}.md")
            
            # Extract single page to temporary PDF
            new_doc = fitz.open()
            new_doc.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)
            new_doc.save(temp_pdf_path)
            new_doc.close()
            
            # Convert PDF to markdown
            print("Converting PDF to markdown...")
            md_text = pymupdf4llm.to_markdown(temp_pdf_path)
            
            # Save markdown for reference
            pathlib.Path(temp_md_path).write_bytes(md_text.encode())
            print(f"Markdown saved to: {temp_md_path}")
            
            # Create structured prompt for table extraction
            prompt = f"""
            Analyze this content from a security requirements document. The content is structured in a three-column format:
            Control Objectives, Test Requirements, and Guidance.

            Here's the extracted content in markdown format:
            {md_text}

            Format the response as a JSON object with these exact three keys:
            {{
                "Control_Objectives": [
                    {{
                        "id": "X.X",
                        "title": "Main objective title",
                        "description": "Main objective description",
                        "sub_requirements": [
                            {{
                                "id": "X.X.a",
                                "description": "Sub-requirement description"
                            }}
                        ]
                    }}
                ],
                "Test_Requirements": [
                    {{
                        "id": "X.X.a",
                        "description": "Detailed test requirement"
                    }}
                ],
                "Guidance": [
                    "Guidance text without any modifications"
                ]
            }}
            Format: json
            """
            
            print("Sending request to Ollama API...")
            response_text = self.call_ollama_api_for_text(prompt)
            
            try:
                json_content = json.loads(response_text)
                all_responses.append(json_content)
                
                # Save to file after each successful extraction
                with open(output_file, 'w') as f:
                    json.dump(all_responses, f, indent=2)
                
                print("\nAPI Response Structure:")
                print(f"Control Objectives: {len(json_content.get('Control_Objectives', []))} items")
                print(f"Test Requirements: {len(json_content.get('Test_Requirements', []))} items")
                print(f"Guidance: {len(json_content.get('Guidance', []))} items")
                
                return json_content
                
            except json.JSONDecodeError:
                print("\nWarning: Response is not in valid JSON format")
                print("Raw response:")
                print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                raise
            
        except Exception as e:
            error_response = {
                "error": str(e),
                "status": "error"
            }
            all_responses.append(error_response)
            
            # Save to file even if there's an error
            with open(output_file, 'w') as f:
                json.dump(all_responses, f, indent=2)
            
            return error_response
            
        finally:
            # Clean up temporary files
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

def check_ollama_availability():
    """Check if Ollama is running and has the required model"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            if LLAMA_MODEL in [m.get("name") for m in models]:
                return True
            else:
                print(f"Llama model '{LLAMA_MODEL}' not found in Ollama")
                return False
    except:
        print("Ollama service not available at localhost:11434")
        return False
    return False

def main():
    print("\nPDF Batch Processor")
    print("1. Use Gemini")
    print("2. Use Llama Vision")
    print("3. Use Qwen")
    print("4. Use Llama + pymupdf4llm")
    
    choice = input("\nEnter your choice (1-4): ")
    
    model_type = None
    if choice == "1":
        model_type = ModelType.GEMINI
    elif choice == "2":
        model_type = ModelType.LLAMA
    elif choice == "3":
        model_type = ModelType.QWEN
    elif choice == "4":
        model_type = ModelType.LLAMA_PDF
    else:
        print("Invalid choice!")
        return
    
    processor = PDFBatchProcessor(
        model_type=model_type,
        data_folder="data",
        batch_size=BATCH_SIZE
    )
    
    # Process pages
    start_page = 16
    end_page = 60
    processor.process_pdf_in_batches(start_page, end_page)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
