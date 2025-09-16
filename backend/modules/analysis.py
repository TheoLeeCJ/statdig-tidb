import os
import json
import re
from typing import Optional, Dict, Any
from openai import OpenAI
from modules.utils import (
    ANALYZE_STATE_ANALYSED, UN_INDEXED_STRING
)

def store_raw_functions_json(md5: str, functions_data: Dict[str, Any]) -> str:
    """
    Store the raw JSON data from function extraction
    Returns the JSON content as string
    """
    # Save raw JSON to filestore as dump_(md5)
    dump_filename = f"dump_{md5}"
    json_content = json.dumps(functions_data, indent=2)
    
    # Store the raw JSON file
    with open(f"filestore/{dump_filename}", "w", encoding='utf-8') as f:
        f.write(json_content)
    
    return json_content

def create_function_dump_for_analysis(md5: str) -> Optional[str]:
    """
    Read raw JSON and convert to formatted dump for AI analysis
    Returns the formatted dump content as string or None if file not found
    """
    dump_filename = f"dump_{md5}"
    dump_path = f"filestore/{dump_filename}"
    try:
        with open(dump_path, "r", encoding='utf-8') as f:
            functions_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    # Convert to formatted dump (sigfn_tree style)
    dump_content = ""
    for func_name, func_data in functions_data.items():
        dump_content += f"{func_name}\n"
        if 'calls' in func_data and func_data['calls']:
            for callee in func_data['calls']:
                dump_content += f"├─ {callee}\n"
        dump_content += "\n"
    return dump_content

def analyze_with_ai(md5: str) -> Optional[str]:
    """
    Analyze the functions using OpenAI chat completion
    Sends raw JSON data directly to the LLM
    Returns the analysis response or None if failed
    """
    # Read the system prompt
    try:
        with open("ingest.txt", "r") as f:
            system_prompt = f.read().strip()
    except FileNotFoundError:
        system_prompt = "Analyze this binary dump for malicious behavior and provide a detailed report."
    
    # Get raw JSON data instead of formatted dump
    functions_data = get_raw_functions_json(md5)
    if not functions_data:
        return None
    
    user_message = json.dumps(functions_data, indent=2)
    
    # Get OpenAI configuration from environment
    model = os.getenv("BIG_MODEL", "gpt-4")
    api_key = os.getenv("BIG_MODEL_KEY")
    base_url = os.getenv("BIG_MODEL_ENDPOINT")
    
    if not api_key:
        raise ValueError("BIG_MODEL_KEY environment variable not set")
    
    try:
        # Initialize OpenAI client
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            
        client = OpenAI(**client_kwargs)
        
        # Make the chat completion request
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.5,
            max_tokens=8192
        )
        
        analysis_content = response.choices[0].message.content
        
        # Remove <think>...</think> block if present
        analysis_content = re.sub(r'<think>.*?</think>', '', analysis_content, flags=re.DOTALL).strip()
        
        # Save the response to sample_details table
        from sql import execute_query
        report_to_store = analysis_content if analysis_content else UN_INDEXED_STRING
        if not report_to_store.strip():
            report_to_store = UN_INDEXED_STRING
        execute_query(
            "UPDATE sample_details SET full_report = %s WHERE id = %s",
            (report_to_store, md5)
        )
        
        # Parse verdict
        verdict_match = re.search(r'```verdict\s*Malicious\s*=\s*(True|False|Uncertain)', analysis_content, re.IGNORECASE)
        verdict = verdict_match.group(1) if verdict_match else None
        
        # Update malicious field in samples
        if verdict:
            from sql import execute_query
            execute_query(
                "UPDATE samples SET malicious = %s WHERE md5 = %s",
                (verdict, md5)
            )
        
        return analysis_content
        
    except Exception as e:
        print(f"Error calling AI model: {e}")
        return None

def get_analysis_report(md5: str) -> Optional[str]:
    """
    Retrieve existing analysis report from sample_details
    """
    from sql import execute_query
    row = execute_query(
        "SELECT full_report FROM sample_details WHERE id = %s",
        (md5,),
        fetch_one=True
    )
    if row:
        return row['full_report']
    return None

def get_raw_functions_json(md5: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve raw functions JSON data from filestore
    """
    dump_filename = f"dump_{md5}"
    dump_path = f"filestore/{dump_filename}"
    
    try:
        with open(dump_path, "r", encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def process_analysis(md5: str) -> Dict[str, Any]:
    """
    Complete analysis process including validation and AI analysis
    Returns dict with success status, message, and analysis content
    """
    from sql import execute_query
    
    # Check if sample exists
    sample = execute_query(
        "SELECT * FROM samples WHERE md5 = %s",
        (md5,),
        fetch_one=True
    )
    
    if not sample:
        return {
            "success": False,
            "error": f"Sample with MD5 {md5} not found",
            "status_code": 404
        }
    
    # Check if already analyzed
    if sample.get('analyze_state') == ANALYZE_STATE_ANALYSED:
        existing_report = get_analysis_report(md5)
        if existing_report:
            return {
                "success": True,
                "message": "Analysis already completed",
                "sample_md5": md5,
                "analysis": existing_report,
                "already_analyzed": True
            }
    
    # Check if functions have been extracted
    function_count = execute_query(
        "SELECT COUNT(*) as count FROM functions WHERE sample_md5 = %s",
        (md5,),
        fetch_one=True
    )
    
    if not function_count or function_count['count'] == 0:
        return {
            "success": False,
            "error": "Functions must be extracted before analysis. Please run extraction first.",
            "status_code": 400
        }
    
    try:
        # Perform AI analysis
        analysis_result = analyze_with_ai(md5)
        
        if not analysis_result:
            return {
                "success": False,
                "error": "AI analysis failed",
                "status_code": 500
            }
        
        # Mark sample as analyzed (handled in endpoint)
        return {
            "success": True,
            "message": "Analysis completed successfully",
            "sample_md5": md5,
            "analysis": analysis_result,
            "already_analyzed": False
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}",
            "status_code": 500
        }

def get_analysis_status(md5: str) -> Dict[str, Any]:
    """
    Get analysis status and report for a sample
    Returns dict with success status and analysis data
    """
    from sql import execute_query
    
    # Check if sample exists
    sample = execute_query(
        "SELECT * FROM samples WHERE md5 = %s",
        (md5,),
        fetch_one=True
    )
    
    if not sample:
        return {
            "success": False,
            "error": f"Sample with MD5 {md5} not found",
            "status_code": 404
        }
    # Get analysis report
    report = get_analysis_report(md5)
    if not report:
        return {
            "success": False,
            "error": "Analysis report not found. Please run analysis first.",
            "status_code": 404
        }
    return {
        "success": True,
        "sample_md5": md5,
        "analyze_state": sample.get('analyze_state', 0),
        "malicious": sample.get('malicious'),
        "is_public": sample.get('is_public', False),
        "analysis": report
    }