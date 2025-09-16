import os
import subprocess
import re
import json
from typing import Dict, Any, Optional
from sql import execute_query
from modules.analysis import store_raw_functions_json
from modules.utils import UN_INDEXED_STRING

def extract_functions_from_binary(md5: str) -> Dict[str, Any]:
    """
    Extract functions from binary using Ghidra
    Returns dict with function count and any error information
    """
    # Use MD5 for unique container and file naming
    container_name = f"ghidra-{md5}"
    output_filename = f"output_{md5}.txt"
    
    try:
        # Create for-docker directory if it doesn't exist
        os.makedirs("for-docker", exist_ok=True)
        
        # Copy the file to for-docker directory with md5 name
        file_path = os.path.join("filestore", md5)
        target_path = f"for-docker/{md5}"
        subprocess.run(["cp", file_path, target_path], check=True)
        
        # Check if container with this name already exists and remove it
        try:
            subprocess.run(["docker", "stop", container_name], 
                         capture_output=True, check=False)
            subprocess.run(["docker", "rm", container_name], 
                         capture_output=True, check=False)
        except:
            pass
        
        # Run Ghidra in Docker container with unique name
        docker_run_cmd = [
            "docker", "run", "--init", "-tid", "--rm",
            "--name", container_name,
            "--entrypoint", "bash",
            "-v", f"{os.path.abspath('for-docker')}:/samples",
            "blacktop/ghidra:10"
        ]
        subprocess.run(docker_run_cmd, check=True)
        
        # Create project directory in container
        subprocess.run(
            ["docker", "exec", "-it", container_name, "mkdir", "/proj"],
            check=True
        )
        
        # Run the analysis with unique output file
        analyze_cmd = [
            "docker", "exec", "-it", container_name, "/bin/bash", "-c",
            f"support/analyzeHeadless /proj proj -import /samples/{md5} "
            f"-postscript /samples/ext.py > /samples/{output_filename} 2>&1"
        ]
        subprocess.run(analyze_cmd, check=True)
        
        # Extract the JSON from the unique output file
        output_path = f"for-docker/{output_filename}"
        with open(output_path, "r") as f:
            output = f.read()
        
        # Find the JSON between the markers
        json_match = re.search(r'===REAL JSON OUTPUT===\n(.*?)===END JSON OUTPUT===', 
                             output, re.DOTALL)
        
        if not json_match:
            raise Exception("Could not find JSON output in Ghidra results")
        
        json_data = json.loads(json_match.group(1).strip())
        
        # Clean up container and files
        subprocess.run(["docker", "stop", container_name], check=True)
        subprocess.run(["rm", "-f", target_path], check=True)
        subprocess.run(["rm", "-f", output_path], check=True)
        
        return {
            "success": True,
            "functions_data": json_data,
            "function_count": len(json_data)
        }
        
    except Exception as e:
        # Clean up in case of error
        try:
            subprocess.run(["docker", "stop", container_name], check=False)
            subprocess.run(["rm", "-f", target_path], check=False)
            subprocess.run(["rm", "-f", f"for-docker/{output_filename}"], check=False)
        except:
            pass
        
        return {
            "success": False,
            "error": str(e),
            "function_count": 0
        }

def store_extracted_functions(md5: str, functions_data: Dict[str, Any]) -> int:
    """
    Store extracted functions in database using batch insert
    Returns the number of functions inserted
    """
    if not functions_data:
        return 0
    
    # Prepare batch insert data
    function_records = []
    for func_name, func_data in functions_data.items():
        function_id = f"{md5}_{func_name}"
        desc = func_data.get('desc', '') or UN_INDEXED_STRING
        function_records.append((
            function_id,
            md5,
            func_name,
            func_data.get('c', ''),
            func_data.get('sig', ''),
            desc
        ))
    
    # Batch insert all functions
    query = """
        INSERT INTO functions (id, sample_md5, name, c_code, signature, description)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    try:
        # Execute batch insert
        result = execute_query(query, function_records, batch=True)
        return len(function_records) if result else 0
    except Exception as e:
        print(e)
        print(f"Error inserting functions: {e}")
        return 0

def check_existing_extraction(md5: str) -> Optional[int]:
    """
    Check if functions have already been extracted for this sample
    Returns function count if exists, None if not extracted
    """
    existing_functions = execute_query(
        "SELECT COUNT(*) as count FROM functions WHERE sample_md5 = %s",
        (md5,),
        fetch_one=True
    )
    
    if existing_functions and existing_functions['count'] > 0:
        return existing_functions['count']
    
    return None

def process_extraction(md5: str) -> Dict[str, Any]:
    """
    Complete function extraction process including validation and storage
    Returns dict with success status, message, and function count
    """
    from sql import execute_query
    
    # Retrieve the sample record
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
    
    # Get the file from filestore
    file_path = os.path.join("filestore", md5)
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": "Sample file not found in storage",
            "status_code": 404
        }
    # Check if functions were already extracted
    existing_count = check_existing_extraction(md5)
    if existing_count is not None:
        return {
            "success": True,
            "message": "Functions already extracted",
            "sample_md5": md5,
            "function_count": existing_count,
            "already_extracted": True
        }
    # Extract functions using Ghidra
    extraction_result = extract_functions_from_binary(md5)
    
    if not extraction_result["success"]:
        return {
            "success": False,
            "error": f"Function extraction failed: {extraction_result['error']}",
            "status_code": 500
        }
    
    # Store functions in database using batch insert
    functions_data = extraction_result["functions_data"]
    inserted_count = store_extracted_functions(md5, functions_data)
    
    if inserted_count == 0:
        return {
            "success": False,
            "error": "Failed to store extracted functions in database",
            "status_code": 500
        }
    
    # Store raw JSON dump
    store_raw_functions_json(md5, functions_data)
    
    return {
        "success": True,
        "message": "Successfully extracted functions",
        "sample_md5": md5,
        "function_count": inserted_count,
        "already_extracted": False
    }
