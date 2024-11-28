import ollama
import json
from datetime import datetime, timedelta
from typing import List, Dict
import csv
import pandas as pd
import os

def enrich_test_requirements(test_requirements: List[str], control_objective: str, guidance: str) -> List[Dict]:
    """
    Enrich test requirements with evidence requests, stakeholders, and due dates
    """
    system_prompt = """You are a security compliance expert. For each test requirement, determine:
    1. What evidence (screenshots, documents, configs) would satisfy this requirement
    2. Which team would be responsible for providing this evidence
    3. Estimate complexity (1-5, where 5 is most complex) to determine timeline
    
    Base your analysis on the control objective, test requirement, and guidance provided.
    Return only valid JSON, no other text."""

    enriched_requirements = []
    
    for req in test_requirements:
        user_prompt = f"""
        Analyze this security requirement and provide:
        1. Specific evidence requests that would satisfy the requirement
        2. The responsible team/stakeholder
        3. Complexity score (1-5)

        Control Objective: {control_objective}
        Test Requirement: {req}
        Guidance: {guidance}

        Format response as JSON:
        {{
            "requirement": "original requirement text",
            "evidence_request": ["list", "of", "specific", "evidence", "requests"],
            "responsible_stakeholder": "team name",
            "complexity": integer 1-5
        }}
        """

        try:
            response = ollama.chat(
                model='qwen2.5:latest',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                format='json'
            )
            
            result = json.loads(response['message']['content'])
            
            # Calculate due date based on complexity
            complexity = result['complexity']
            due_date = datetime.now() + timedelta(days=complexity * 5)
            
            enriched_req = {
                'requirement': req,
                'evidence_request': result['evidence_request'],
                'responsible_stakeholder': result['responsible_stakeholder'],
                'complexity': complexity,
                'due_date': due_date.strftime('%Y-%m-%d')
            }
            
            enriched_requirements.append(enriched_req)
            
        except Exception as e:
            print(f"Error enriching requirement: {e}")
            # Add a basic entry if enrichment fails
            enriched_requirements.append({
                'requirement': req,
                'evidence_request': ['Documentation needed'],
                'responsible_stakeholder': 'To be determined',
                'complexity': 3,
                'due_date': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
            })
    
    return enriched_requirements

def save_as_csv(enriched_data: dict, csv_output_path: str):
    """Convert enriched JSON data to CSV format with combined evidence requests"""
    try:
        # Create a list to hold all rows
        csv_rows = []
        
        # Process each control objective and its requirements
        for row in enriched_data['table_rows']:
            # Handle empty control objective and guidance
            control_objective = row.get('control_objective', '').strip() or 'No control objective specified'
            guidance = row.get('guidance', '').strip() or 'No guidance specified'
            
            # For each test requirement in this control objective
            for test_req in row['test_requirements']:
                # Debug print to see the structure
                print(f"\nProcessing test requirement: {test_req}")
                
                # Clean requirement text - remove bullet points and extra whitespace
                requirement = test_req.get('requirement', '').strip()
                if requirement.startswith('·'):
                    requirement = requirement[1:].strip()
                if not requirement:
                    requirement = 'No requirement specified'
                
                # Ensure evidence_request exists and is a list
                evidence_list = test_req.get('evidence_request', [])
                if not isinstance(evidence_list, list):
                    evidence_list = [str(evidence_list)]
                
                # Filter out empty or None values and clean evidence items
                evidence_list = [e.strip() for e in evidence_list if e and e.strip()]
                
                # Combine all evidence requests into one cell with bullet points
                if evidence_list:
                    combined_evidence = "\n• " + "\n• ".join(evidence_list)
                else:
                    combined_evidence = "No evidence requests specified"
                
                csv_row = {
                    'Control_Objective': control_objective,
                    'Test_Requirement': requirement,
                    'Evidence_Request': combined_evidence,
                    'Responsible_Stakeholder': test_req.get('responsible_stakeholder', 'Not specified').strip(),
                    'Complexity': test_req.get('complexity', 'Not specified'),
                    'Due_Date': test_req.get('due_date', 'Not specified'),
                    'Guidance': guidance
                }
                csv_rows.append(csv_row)
        
        # Convert to DataFrame and save as CSV
        df = pd.DataFrame(csv_rows)
        
        # Reorder columns for better readability
        column_order = [
            'Control_Objective',
            'Test_Requirement',
            'Evidence_Request',
            'Responsible_Stakeholder',
            'Complexity',
            'Due_Date',
            'Guidance'
        ]
        df = df[column_order]
        
        # Clean up any remaining whitespace
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()
        
        # Save to CSV with proper encoding
        df.to_csv(csv_output_path, index=False, encoding='utf-8-sig', lineterminator='\n')
        print(f"\nCSV file saved successfully to {csv_output_path}")
        print(f"Total rows in CSV: {len(df)}")
        
        # Debug: Print first row to verify content
        print("\nFirst row preview:")
        print(df.iloc[0])
        
    except Exception as e:
        print(f"Error saving CSV: {e}")
        # Print more detailed error information
        import traceback
        print(traceback.format_exc())

def process_json_file(input_path: str, output_path: str, csv_output_path: str):
    """Process existing JSON file and add new fields, save as both JSON and CSV"""
    try:
        # Check if enriched JSON already exists
        if os.path.exists(output_path):
            print(f"Found existing enriched JSON at {output_path}")
            with open(output_path, 'r', encoding='utf-8') as f:
                enriched_data = json.load(f)
            print("Skipping enrichment step, proceeding to CSV conversion...")
        else:
            # Read existing JSON and perform enrichment
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Process each row
            enriched_data = {'table_rows': []}
            total_rows = len(data['table_rows'])
            
            for i, row in enumerate(data['table_rows'], 1):
                print(f"\nProcessing row {i}/{total_rows}")
                
                enriched_requirements = enrich_test_requirements(
                    row['test_requirements'],
                    row['control_objective'],
                    row['guidance']
                )
                
                enriched_row = {
                    'control_objective': row['control_objective'],
                    'test_requirements': enriched_requirements,
                    'guidance': row['guidance']
                }
                
                enriched_data['table_rows'].append(enriched_row)
                
                # Save intermediate JSON results
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(enriched_data, f, indent=4, ensure_ascii=False)
        
        # Save final results as CSV
        save_as_csv(enriched_data, csv_output_path)
        
        print(f"\nProcessing complete. Files saved to:")
        print(f"JSON: {output_path}")
        print(f"CSV: {csv_output_path}")
        
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    input_file = "data/docling-pci_extractions_ollama_16-60.json"
    output_file = "data/enriched_pci_extractions.json"
    csv_output_file = "data/enriched_pci_extractions.csv"
    process_json_file(input_file, output_file, csv_output_file)
