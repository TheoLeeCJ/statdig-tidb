import os
import json
import threading
from typing import Dict, Any, List, Optional
from openai import OpenAI
from sql import execute_query
from modules.utils import UN_INDEXED_STRING, random_id

# In-memory store for background job results
search_results_store = {}

def classify_search_term(search_term: str) -> str:
    """
    Classify search term as exact match (IOC) or semantic match (technique/behavior)
    Returns: 'exact' or 'semantic'
    """
    # Get OpenAI configuration
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
        
        system_prompt = """You are a malware analysis assistant. Your job is to classify search terms.

If the search term looks like:
- An exact indicator of compromise (IOC) like IP addresses, domain names, file hashes, registry keys, file paths
- A specific string or identifier that should be matched exactly
- A precise technical term or function name
Then respond with: CLASS_EXACT

If the search term looks like:
- A behavior or technique description
- A general concept or capability
- Something that should be matched semantically/conceptually
Then respond with: CLASS_SEMANTIC

Only respond with CLASS_EXACT or CLASS_SEMANTIC."""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Classify this search term: {search_term}"}
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        response_content = response.choices[0].message.content
        
        if "CLASS_EXACT" in response_content:
            return "exact"
        elif "CLASS_SEMANTIC" in response_content:
            return "semantic"
        else:
            # Default to semantic for ambiguous cases
            return "semantic"
            
    except Exception as e:
        print(f"Error classifying search term: {e}")
        # Default to semantic on error
        return "semantic"

def search_functions_semantic(search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Perform semantic vector search on functions table
    """
    query = """
        SELECT name, description, c_code, sample_md5, 
               VEC_COSINE_DISTANCE(description_vec, EMBED_TEXT("tidbcloud_free/amazon/titan-embed-text-v2", %s)) AS distance 
        FROM functions
        WHERE description != %s
        ORDER BY distance ASC
        LIMIT %s
    """
    
    results = execute_query(query, (search_term, UN_INDEXED_STRING, limit), fetch_all=True)
    
    # Stop at first UN_INDEXED_STRING if found
    filtered_results = []
    for result in results or []:
        if result['description'] == UN_INDEXED_STRING:
            break
        filtered_results.append({
            'type': 'function',
            'name': result['name'],
            'description': result['description'],
            'c_code': result['c_code'],
            'sample_md5': result['sample_md5'],
            'score': 1.0 - result['distance']  # Convert distance to similarity
        })
    
    return filtered_results

def search_samples_semantic(search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Perform semantic vector search on samples table with tags
    """
    query = """
        SELECT s.md5, s.original_filename, s.filetype, s.file_description, 
               s.overview, s.malicious, s.analyze_state,
               VEC_COSINE_DISTANCE(s.overview_vec, EMBED_TEXT("tidbcloud_free/amazon/titan-embed-text-v2", %s)) AS distance,
               GROUP_CONCAT(t.tag_content SEPARATOR ', ') as tags
        FROM samples s
        LEFT JOIN tags_sample ts ON s.md5 = ts.sample_md5
        LEFT JOIN tags t ON ts.tagId = t.tagId
        WHERE s.overview != %s
        GROUP BY s.md5, s.original_filename, s.filetype, s.file_description, 
                 s.overview, s.malicious, s.analyze_state, distance
        ORDER BY distance ASC
        LIMIT %s
    """
    
    results = execute_query(query, (search_term, UN_INDEXED_STRING, limit), fetch_all=True)
    
    # Stop at first UN_INDEXED_STRING if found
    filtered_results = []
    for result in results or []:
        if result['overview'] == UN_INDEXED_STRING:
            break
        filtered_results.append({
            'type': 'sample',
            'md5': result['md5'],
            'original_filename': result['original_filename'],
            'filetype': result['filetype'],
            'file_description': result['file_description'],
            'overview': result['overview'],
            'malicious': result['malicious'],
            'analyze_state': result['analyze_state'],
            'tags': result['tags'] or '',
            'score': 1.0 - result['distance']  # Convert distance to similarity
        })
    
    return filtered_results

def search_functions_exact(search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Perform fulltext search on functions table
    """
    query = """
        SELECT name, description, c_code, sample_md5,
               fts_match_word(%s, description) as similarity
        FROM functions
        WHERE fts_match_word(%s, description)
        ORDER BY fts_match_word(%s, description) DESC
        LIMIT %s
    """
    
    results = execute_query(query, (search_term, search_term, search_term, limit), fetch_all=True)
    
    return [{
        'type': 'function',
        'name': result['name'],
        'description': result['description'],
        'c_code': result['c_code'],
        'sample_md5': result['sample_md5'],
        'score': result['similarity']
    } for result in results or []]

def search_samples_exact(search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Perform fulltext search on samples table with tags
    Split into two queries to avoid FTS_MATCH_WORD constraints
    """
    # First query: Get samples with fulltext search
    samples_query = """
        SELECT md5, original_filename, filetype, file_description, 
               overview, malicious, analyze_state,
               fts_match_word(%s, overview) as similarity
        FROM samples
        WHERE fts_match_word(%s, overview)
        ORDER BY fts_match_word(%s, overview) DESC
        LIMIT %s
    """
    
    sample_results = execute_query(samples_query, (search_term, search_term, search_term, limit), fetch_all=True)
    
    if not sample_results:
        return []
    
    # Extract MD5s for tag lookup
    md5_list = [result['md5'] for result in sample_results]
    
    # Second query: Get tags for these samples
    if md5_list:
        placeholders = ','.join(['%s'] * len(md5_list))
        tags_query = f"""
            SELECT ts.sample_md5, GROUP_CONCAT(t.tag_content SEPARATOR ', ') as tags
            FROM tags_sample ts
            JOIN tags t ON ts.tagId = t.tagId
            WHERE ts.sample_md5 IN ({placeholders})
            GROUP BY ts.sample_md5
        """
        
        tag_results = execute_query(tags_query, md5_list, fetch_all=True)
        
        # Create a mapping of md5 -> tags
        tags_map = {row['sample_md5']: row['tags'] for row in tag_results or []}
    else:
        tags_map = {}
    
    # Combine results
    final_results = []
    for result in sample_results:
        final_results.append({
            'type': 'sample',
            'md5': result['md5'],
            'original_filename': result['original_filename'],
            'filetype': result['filetype'],
            'file_description': result['file_description'],
            'overview': result['overview'],
            'malicious': result['malicious'],
            'analyze_state': result['analyze_state'],
            'tags': tags_map.get(result['md5'], ''),
            'score': result['similarity']
        })
    
    return final_results

def merge_and_sort_results(functions: List[Dict[str, Any]], samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge function and sample results, sort by score descending
    """
    all_results = functions + samples
    return sorted(all_results, key=lambda x: x['score'], reverse=True)

def generate_llm_summary(search_term: str, results: List[Dict[str, Any]], job_id: str) -> None:
    """
    Background job to generate LLM summary of search results
    """
    try:
        # Prepare context from results
        context_parts = []
        
        for result in results[:5]:  # Use top 5 results for context
            if result['type'] == 'function':
                context_parts.append(f"Function: {result['name']}\nDescription: {result['description']}")
            else:  # sample
                context_parts.append(f"Sample: {result['original_filename']}\nOverview: {result['overview']}")
        
        if not context_parts:
            search_results_store[job_id] = "No relevant results found for the search term."
            return
        
        context = "\n\n".join(context_parts)
        
        # Get OpenAI configuration
        model = os.getenv("BIG_MODEL", "gpt-4")
        api_key = os.getenv("BIG_MODEL_KEY")
        base_url = os.getenv("BIG_MODEL_ENDPOINT")
        
        if not api_key:
            search_results_store[job_id] = "AI analysis unavailable: API key not configured"
            return
        
        # Initialize OpenAI client
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            
        client = OpenAI(**client_kwargs)
        
        system_prompt = """You are a malware analysis expert. Based on the search results provided, give a concise 3-5 sentence summary that directly addresses the user's search query. Focus on the most relevant findings and their significance in malware analysis context."""
        
        user_prompt = f"""Search term: "{search_term}"

Search results:
{context}

Provide a 3-5 sentence summary of what these results tell us about the search term in the context of malware analysis."""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        
        summary = response.choices[0].message.content
        search_results_store[job_id] = summary
        
    except Exception as e:
        print(f"Error generating LLM summary for job {job_id}: {e}")
        search_results_store[job_id] = f"Error generating summary: {str(e)}"

def perform_supersearch(search_term: str) -> Dict[str, Any]:
    """
    Main supersearch function that orchestrates the search process
    """
    try:
        # Generate unique job ID for background processing using random_id
        job_id = random_id()
        
        # Classify search term
        search_type = classify_search_term(search_term)
        
        # Perform appropriate search
        if search_type == "semantic":
            function_results = search_functions_semantic(search_term)
            sample_results = search_samples_semantic(search_term)
        else:  # exact
            function_results = search_functions_exact(search_term)
            sample_results = search_samples_exact(search_term)
        
        # Merge and sort results
        merged_results = merge_and_sort_results(function_results, sample_results)
        
        # Start background job for LLM summary
        thread = threading.Thread(target=generate_llm_summary, args=(search_term, merged_results, job_id))
        thread.daemon = True
        thread.start()
        
        return {
            "success": True,
            "search_term": search_term,
            "type": search_type,
            "results": merged_results,
            "job_id": job_id,
            "total_results": len(merged_results)
        }
    except Exception as e:
        print(e)
        return {
            "success": False
        }

def get_search_summary(job_id: str) -> Dict[str, Any]:
    """
    Get the LLM summary for a search job and clean up
    """
    if job_id not in search_results_store:
        return {
            "success": False,
            "error": "Job not found or still processing",
            "status": "processing"
        }
    
    # Get result and clean up
    summary = search_results_store.pop(job_id)
    
    return {
        "success": True,
        "job_id": job_id,
        "summary": summary,
        "status": "completed"
    }