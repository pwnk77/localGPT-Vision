from docling.document_converter import DocumentConverter
import json
import pathlib
from typing import Dict, List, Literal
import ollama
import os
import re
import requests
from dotenv import load_dotenv
import time
from collections import deque
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Add these constants after imports
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
RATE_LIMIT_REQUESTS = 20  # requests
RATE_LIMIT_WINDOW = 60   # seconds

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.requests = deque()
        self.request_count = 0  # Track total requests in current window
    
    def can_make_request(self) -> bool:
        now = datetime.now()
        
        # Remove requests older than the time window
        while self.requests and (now - self.requests[0]) > timedelta(seconds=self.time_window):
            self.requests.popleft()
            self.request_count = len(self.requests)  # Update count
        
        # Check if we're under the rate limit
        return len(self.requests) < self.max_requests
    
    def add_request(self):
        self.requests.append(datetime.now())
        self.request_count += 1
        
        # If we've hit the rate limit, enforce a full window wait
        if self.request_count >= self.max_requests:
            print(f"\nReached {self.max_requests} requests. Enforcing a full {self.time_window} second cooldown...")
            time.sleep(self.time_window)
            # Clear the queue and reset count after the wait
            self.requests.clear()
            self.request_count = 0
            print("Cooldown complete. Resuming processing...")
    
    def wait_for_next_slot(self):
        while not self.can_make_request():
            # Wait until the oldest request expires
            sleep_time = (self.requests[0] + timedelta(seconds=self.time_window) - datetime.now()).total_seconds()
            if sleep_time > 0:
                print(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                self.requests.popleft()
                self.request_count = len(self.requests)  # Update count

# Create rate limiter instance after the constants
rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)

def convert_pdf_to_markdown(pdf_path: str, output_path: str) -> str:
    """Convert PDF to markdown using Docling"""
    try:
        # Check if markdown file already exists
        if os.path.exists(output_path):
            print("Markdown file already exists, skipping conversion...")
            return pathlib.Path(output_path).read_text(encoding='utf-8')
            
        # Initialize Docling converter
        print("Converting PDF to markdown using Docling...")
        converter = DocumentConverter()
        
        # Convert PDF to Docling document
        result = converter.convert(pdf_path)
        
        # Get markdown text
        md_text = result.document.export_to_markdown()
        
        # Save markdown to file
        pathlib.Path(output_path).write_text(md_text, encoding='utf-8')
        return md_text
    except Exception as e:
        print(f"Error converting PDF to markdown: {e}")
        return None

def call_openrouter(system_prompt: str, user_prompt: str) -> Dict:
    """Make API call to OpenRouter using Gemini"""
    try:
        # Check rate limit before making request
        rate_limiter.wait_for_next_slot()
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:3000",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "google/gemini-pro:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,  # Lower temperature for more consistent output
            "max_tokens": 4000,  # Ensure enough tokens for response
            "response_format": { "type": "json" }  # Request JSON response
        }
        
        print("Making OpenRouter API call...")
        response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=data)
        # Record the request after it's made successfully
        rate_limiter.add_request()
        
        response.raise_for_status()
        
        response_data = response.json()
        print(f"OpenRouter API Status: {response.status_code}")
        
        # Debug response
        if 'choices' not in response_data or not response_data['choices']:
            print("Error: No choices in response")
            print("Response:", response_data)
            return None
            
        content = response_data['choices'][0]['message']['content']
        
        # Try to clean the content if it's not valid JSON
        content = content.strip()
        if not content.startswith('{'):
            # Try to find JSON in the content
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx + 1]
        
        return json.loads(content)
        
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {e}")
        print("Raw content:", content)
        return None
    except Exception as e:
        print(f"Unexpected Error in call_openrouter: {e}")
        return None

def extract_table_data(markdown_text: str, model: Literal["ollama", "openrouter"] = "ollama") -> Dict:
    """Extract table data using specified model"""
    try:
        system_prompt = """You are a table data extraction expert. You will analyze markdown tables from a security requirements document.
        Your output must be valid JSON only, with no additional text or explanation.
        
        Important rules:
        1. Process only the table content provided
        2. Focus on three-column tables with this structure:
           - Column 1: Control Objectives (contains ID and description)
           - Column 2: Test Requirements (contains multiple requirements with IDs)
           - Column 3: Guidance (contains guidance text)
        3. For rows that span multiple cells:
           - Combine all content for that section
           - Maintain proper association with the parent control objective
        4. Extract the complete text without truncation
        5. Keep the exact formatting and full content of each cell
        6. Return valid JSON only
        8. If no valid table is found, return {"table_rows": []}
        9. Never truncate content with ellipsis (...)
        10. Include all text, including long paragraphs
        11. If there is no data, return the json keys with blank values
        """
        
        user_prompt = f"""
        Extract the complete content from the table in the provided text. For each row:
        1. Control Objective: Extract the full text including ID and description as one string
        2. Test Requirements: Extract all requirements with their complete text (including IDs)
        3. Guidance: Extract the complete guidance text without any truncation

        Format as JSON with this structure, below is an example JSON structure for reference:
        {{
            "table_rows": [
                {{
                    "control_objective": "3.4 The software securely deletes sensitive data when required",
                    "test_requirements": [
                        "3.4.a The assessor shall examine software design and implementation evidence and verify that the software includes functionality to securely delete sensitive data when required",
                        "3.4.b The assessor shall examine software test results and verify that sensitive data is securely deleted when required"
                    ],
                    "guidance": "The complete guidance text goes here without any truncation..."
                }}
            ]
        }}

        Important:
        - Include the complete text for each field
        - Do not truncate any content OR generate your own content
        - Only extract the content from the table

        Here's the markdown content to process:
        {markdown_text}
        """
        
        if model == "ollama":
            response = ollama.chat(
                model='qwen2.5:latest',
                messages=[
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user', 
                        'content': user_prompt
                    }
                ],
                format='json'
            )
            return json.loads(response['message']['content'])
        else:  # openrouter
            result = call_openrouter(system_prompt, user_prompt)
            if result is None:
                return {"table_rows": []}
            return result
            
    except Exception as e:
        print(f"Error in extract_table_data: {e}")
        return {"table_rows": []}

def save_json(data: Dict, output_path: str):
    """Save extracted data as JSON"""
    try:
        print(f"\nSaving data to {output_path}")
        print(f"Number of rows to save: {len(data['table_rows'])}")
        
        # Debug: Print the data being saved
        print("Data to be saved (first row):", json.dumps(data['table_rows'][0], indent=2))
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(output_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # First write to a temporary file
        temp_path = output_path + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.flush()  # Ensure data is written to disk
            os.fsync(f.fileno())  # Force write to disk
        
        # Verify the temporary file was written correctly
        if not os.path.exists(temp_path):
            raise Exception("Failed to create temporary file")
            
        # Read back the temporary file to verify it's valid JSON
        with open(temp_path, 'r', encoding='utf-8') as f:
            json.load(f)  # This will raise an exception if JSON is invalid
            
        # If verification passed, rename temp file to final file
        if os.path.exists(output_path):
            os.remove(output_path)  # Remove existing file if it exists
        os.rename(temp_path, output_path)
        
        # Final verification
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            with open(output_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                saved_rows = len(saved_data['table_rows'])
                print(f"File saved and verified. Size: {file_size} bytes, Rows: {saved_rows}")
        else:
            raise Exception("Final file was not created")
            
    except Exception as e:
        print(f"Error saving JSON: {str(e)}")
        print(f"Attempted to save to: {output_path}")
        # Print the data that failed to save
        print("Failed data preview:", json.dumps(data['table_rows'][:2], indent=2))
        # If temp file exists, try to read its contents
        if os.path.exists(temp_path):
            try:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    print("Temp file contents:", f.read())
            except Exception as temp_e:
                print(f"Error reading temp file: {str(temp_e)}")
        raise  # Re-raise the exception to be caught by the caller

def process_chunks(content: str, json_output_path: str, model: str = "ollama"):
    """Process content in chunks divided by image markers"""
    chunks = content.split('<!-- image -->')
    accumulated_data = {"table_rows": []}
    
    total_chunks = len([c for c in chunks if c.strip()])
    processed_chunks = 0
    
    try:
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # Skip empty chunks
                processed_chunks += 1
                print(f"\nProcessing chunk {processed_chunks}/{total_chunks}...")
                
                # Add chunk size debug info
                chunk_size = len(chunk.strip())
                print(f"Chunk size: {chunk_size} characters")
                
                # Extract data from chunk
                chunk_data = extract_table_data(chunk.strip(), model)
                
                if chunk_data and chunk_data.get('table_rows'):
                    # Add chunk results to accumulated data
                    accumulated_data['table_rows'].extend(chunk_data['table_rows'])
                    print(f"Found {len(chunk_data['table_rows'])} rows in chunk {processed_chunks}")
                    
                    # Save intermediate results with error handling
                    try:
                        save_json(accumulated_data, json_output_path)
                    except Exception as e:
                        print(f"Error saving intermediate results: {str(e)}")
                        # Try to save to a backup file
                        backup_path = json_output_path + f'.backup_{processed_chunks}'
                        print(f"Attempting to save to backup file: {backup_path}")
                        try:
                            with open(backup_path, 'w', encoding='utf-8') as f:
                                json.dump(accumulated_data, f, indent=4, ensure_ascii=False)
                        except Exception as backup_e:
                            print(f"Failed to save backup: {str(backup_e)}")
                else:
                    print(f"No valid table data found in chunk {processed_chunks}")
        
        # Save final results
        if accumulated_data['table_rows']:
            print("\nSaving final results...")
            try:
                save_json(accumulated_data, json_output_path)
            except Exception as e:
                print(f"Error saving final results: {str(e)}")
                # Save to a final backup file
                final_backup = json_output_path + '.final_backup'
                with open(final_backup, 'w', encoding='utf-8') as f:
                    json.dump(accumulated_data, f, indent=4, ensure_ascii=False)
                print(f"Saved final backup to: {final_backup}")
            
        return accumulated_data
        
    except Exception as e:
        print(f"Error in process_chunks: {str(e)}")
        if accumulated_data['table_rows']:
            print("Attempting to save partial results...")
            try:
                save_json(accumulated_data, json_output_path + '.error_backup')
            except Exception as save_e:
                print(f"Failed to save error backup: {str(save_e)}")
        return accumulated_data

def main():
    # Define paths
    pdf_path = "data/PCI-Secure-Software-Standard-v1_2_1.pdf"
    markdown_path = "data/docling-pci_requirements.md"
    
    # Get user input for model selection
    while True:
        model_choice = input("Choose model (ollama/openrouter): ").lower()
        if model_choice in ["ollama", "openrouter"]:
            break
        print("Invalid choice. Please enter 'ollama' or 'openrouter'")
    
    # Set output path based on model choice
    json_output_path = f"data/docling-pci_extractions_{model_choice}_16-60.json"
    
    # Get markdown content (convert if needed)
    md_text = convert_pdf_to_markdown(pdf_path, markdown_path)
    
    if md_text:
        # Split content into lines
        lines = md_text.splitlines()
        
        # Extract content between lines 270 and 710
        if len(lines) >= 710:
            core_requirements_content = '\n'.join(lines[270:711])
            
            # Process content in chunks
            print(f"Processing Core Requirements section in chunks using {model_choice}...")
            extracted_data = process_chunks(core_requirements_content, json_output_path, model_choice)
            
            if extracted_data and extracted_data['table_rows']:
                print(f"\nProcessing complete. Total rows extracted: {len(extracted_data['table_rows'])}")
            else:
                print("\nNo table data was extracted")
        else:
            print("Markdown file doesn't have enough lines")
    else:
        print("Failed to convert PDF")

if __name__ == "__main__":
    main()
