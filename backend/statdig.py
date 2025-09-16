import os
import subprocess
import re
import json
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv

from modules.user import (
    create_user, authenticate_user, get_user_by_username, generate_token, 
    verify_token, list_users, User
)
from modules.filestore import store_file, get_file_md5
from modules.analysis import store_raw_functions_json, analyze_with_ai, get_analysis_report, process_analysis, get_analysis_status
from modules.extraction import extract_functions_from_binary, store_extracted_functions, check_existing_extraction, process_extraction
from modules.organiser import start_organiser_agent, get_organiser_status
from modules.supersearch import perform_supersearch, get_search_summary
from modules.utils import (
    ANALYZE_STATE_UPLOADED, ANALYZE_STATE_EXTRACTING, ANALYZE_STATE_EXTRACTED, ANALYZE_STATE_ANALYSING, ANALYZE_STATE_ANALYSED, UN_INDEXED_STRING
)
from sql import execute_query

load_dotenv()

app = FastAPI(title="StatDig API", version="1.0.0")

# CORS configuration - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"

class UserLogin(BaseModel):
    username: str
    password: str

class SearchRequest(BaseModel):
    search_term: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# Authentication dependency
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    username = token_data.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token data"
        )
    
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Authentication endpoints
@app.post("/auth/login", response_model=TokenResponse)
def login(user_data: UserLogin):
    """User login endpoint"""
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    token = generate_token(user)
    return TokenResponse(
        access_token=token,
        user={
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    )

@app.post("/auth/create-user")
def create_user_endpoint(
    user_data: UserCreate,
    admin_user: User = Depends(get_admin_user)
):
    """Create new user (admin only)"""
    username = create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role
    )
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user. Username or email might already exist."
        )
    
    return {"message": "User created successfully", "username": username}

@app.get("/users")
def list_users_endpoint(admin_user: User = Depends(get_admin_user)):
    """List all users (admin only)"""
    users = list_users()
    return {"users": users}

# File management endpoints
@app.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload file endpoint (max 50MB)"""
    MAX_SIZE = 50 * 1024 * 1024
    file_content = file.file.read()
    if len(file_content) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 50MB limit"
        )
    file_md5 = store_file(file_content, file.filename)
    filetype = "unknown"
    file_description = "unknown"
    overview = UN_INDEXED_STRING
    try:
        mime_result = subprocess.run(
            ["file", "-b", "--mime-type", f"filestore/{file_md5}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        filetype = mime_result.stdout.strip() if mime_result.returncode == 0 else "unknown"
        desc_result = subprocess.run(
            ["file", "-b", f"filestore/{file_md5}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        file_description = desc_result.stdout.strip() if desc_result.returncode == 0 else "unknown"
    except Exception:
        filetype = "unknown"
        file_description = "unknown"
    query = """
        INSERT INTO samples (md5, original_filename, file_size, filetype, file_description, uploaded_by, analyze_state, is_public, malicious, overview)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, %s)
    """
    try:
        result = execute_query(
            query,
            (file_md5, file.filename, len(file_content), filetype, file_description, current_user.username, ANALYZE_STATE_UPLOADED, False, overview)
        )
        if result > 0:
            # Insert into sample_details
            execute_query(
                "INSERT INTO sample_details (id, full_report, organiser_data, responder_data) VALUES (%s, %s, %s, %s)",
                (file_md5, UN_INDEXED_STRING, None, None)
            )
            sample = execute_query(
                "SELECT * FROM samples WHERE md5 = %s",
                (file_md5,),
                fetch_one=True
            )
            return {"message": "File uploaded successfully", "sample": sample}
    except Exception as e:
        existing_sample = execute_query(
            "SELECT * FROM samples WHERE md5 = %s",
            (file_md5,),
            fetch_one=True
        )
        if existing_sample:
            return {"message": "File already exists", "sample": existing_sample}
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file information: {str(e)}"
        )

@app.get("/samples")
def list_samples(current_user: User = Depends(get_current_user)):
    """List all sample files with function counts, tags"""
    query = """
        SELECT s.md5, s.original_filename, s.file_size, s.filetype, s.file_description, 
               s.uploaded_by, s.analyze_state, s.is_public, s.malicious, s.created_at, s.overview,
               u.username as uploaded_by_username,
               COALESCE(f.function_count, 0) as function_count
        FROM samples s 
        JOIN users u ON s.uploaded_by = u.username 
        LEFT JOIN (
            SELECT sample_md5, COUNT(*) as function_count 
            FROM functions 
            GROUP BY sample_md5
        ) f ON s.md5 = f.sample_md5
        GROUP BY s.md5, s.original_filename, s.file_size, s.filetype, s.file_description, 
                 s.uploaded_by, s.analyze_state, s.is_public, s.malicious, s.created_at,
                 u.username, f.function_count
        ORDER BY s.created_at DESC
    """
    samples = execute_query(query, fetch_all=True)
    return {"samples": samples or []}

@app.post("/extract/{md5}")
def extract_functions(
    md5: str,
    current_user: User = Depends(get_current_user)
):
    """Extract functions from binary using Ghidra"""
    # Set analyze_state to extracting
    execute_query("UPDATE samples SET analyze_state = %s WHERE md5 = %s", (ANALYZE_STATE_EXTRACTING, md5))
    result = process_extraction(md5)
    if not result["success"]:
        execute_query("UPDATE samples SET analyze_state = %s WHERE md5 = %s", (ANALYZE_STATE_UPLOADED, md5))
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result["error"]
        )
    execute_query("UPDATE samples SET analyze_state = %s WHERE md5 = %s", (ANALYZE_STATE_EXTRACTED, md5))
    return {
        "message": result["message"],
        "sample_md5": result["sample_md5"],
        "function_count": result["function_count"]
    }

@app.post("/analyze/{md5}")
def analyze_sample(
    md5: str,
    current_user: User = Depends(get_current_user)
):
    """Analyze sample using AI"""
    execute_query("UPDATE samples SET analyze_state = %s WHERE md5 = %s", (ANALYZE_STATE_ANALYSING, md5))
    result = process_analysis(md5)
    if not result["success"]:
        execute_query("UPDATE samples SET analyze_state = %s WHERE md5 = %s", (ANALYZE_STATE_EXTRACTED, md5))
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result["error"]
        )
    execute_query("UPDATE samples SET analyze_state = %s WHERE md5 = %s", (ANALYZE_STATE_ANALYSED, md5))
    return {
        "message": result["message"],
        "sample_md5": result["sample_md5"],
        "analysis": result["analysis"]
    }

@app.get("/analyze/{md5}")
def get_analysis(
    md5: str,
    current_user: User = Depends(get_current_user)
):
    """Get existing analysis report and function dump"""
    result = get_analysis_status(md5)
    if not result["success"]:
        raise HTTPException(
            status_code=result.get("status_code", 404),
            detail=result["error"]
        )
    # Also return the function dump (sigfn_tree)
    from modules.analysis import create_function_dump_for_analysis
    sigfn_tree = create_function_dump_for_analysis(md5)
    return {
        "sample_md5": result["sample_md5"],
        "analyze_state": result["analyze_state"],
        "malicious": result["malicious"],
        "is_public": result["is_public"],
        "analysis": result["analysis"],
        "sigfn_tree": sigfn_tree
    }

@app.get("/functions/{md5}")
def get_functions_for_sample(md5: str, current_user: User = Depends(get_current_user)):
    """Return all functions for a sample (authenticated)"""
    rows = execute_query(
        "SELECT name, c_code, signature, description FROM functions WHERE sample_md5 = %s ORDER BY name ASC",
        (md5,),
        fetch_all=True
    )
    return {"functions": rows or []}

@app.post("/organise/{md5}")
def organise_sample(
    md5: str,
    current_user: User = Depends(get_current_user)
):
    """Start organiser agent for sample analysis enrichment"""
    result = start_organiser_agent(md5)
    
    if not result["success"]:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result["error"]
        )
    
    return {
        "message": result["message"],
        "sample_md5": result["sample_md5"],
        "status": result.get("status"),
        "already_organised": result.get("already_organised", False)
    }

@app.get("/organise/{md5}")
def get_organiser_data(
    md5: str,
    current_user: User = Depends(get_current_user)
):
    """Get organiser agent status and data"""
    result = get_organiser_status(md5)
    
    if not result["success"]:
        raise HTTPException(
            status_code=result.get("status_code", 404),
            detail=result["error"]
        )
    
    return {
        "sample_md5": result["sample_md5"],
        "analyze_state": result["analyze_state"],
        "organiser_data": result["organiser_data"]
    }

@app.post("/supersearch")
def supersearch(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Perform intelligent search across samples and functions"""
    try:
        result = perform_supersearch(search_request.search_term)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail="Search failed"
            )
        
        return {
            "search_term": result["search_term"],
            "type": result["type"],
            "results": result["results"],
            "job_id": result["job_id"],
            "total_results": result["total_results"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

@app.get("/supersearch/{job_id}")
def get_supersearch_summary(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get LLM summary for a supersearch job"""
    result = get_search_summary(job_id)
    
    if not result["success"]:
        if result.get("status") == "processing":
            raise HTTPException(
                status_code=202,
                detail="Summary still being generated"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=result["error"]
            )
    
    return {
        "job_id": result["job_id"],
        "summary": result["summary"],
        "status": result["status"]
    }

@app.get("/")
def root():
    """Health check endpoint"""
    return {"message": "StatDig API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)