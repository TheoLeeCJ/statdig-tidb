import os
import json
import re
import threading
from typing import Dict, Any, List, Optional
from openai import OpenAI
from sql import execute_query
from modules.utils import ANALYZE_STATE_ORGANISING, ANALYZE_STATE_ORGANISED, ANALYZE_STATE_ANALYSED

def search_impl(arguments: Dict[str, Any]) -> Any:
    """
    Web search implementation for the organiser agent.
    Returns the arguments as-is for built-in function handling.
    """
    return arguments

def extract_significant_functions(report: str) -> List[str]:
    """
    Extract significant function names from the analysis report.
    Looks for ```sigfn_list pattern and extracts comma-separated function names.
    """
    pattern = r'```sigfn_list\s*\n([^`]+)```'
    match = re.search(pattern, report, re.DOTALL)
    
    if not match:
        return []
    
    functions_text = match.group(1).strip()
    # Split by comma and clean up function names
    functions = [func.strip() for func in functions_text.split(',') if func.strip()]
    return functions

def get_function_code(md5: str, function_names: List[str]) -> str:
    """
    Retrieve C code for the specified functions from the database.
    """
    if not function_names:
        return ""
    
    # Create placeholders for the IN clause
    placeholders = ','.join(['%s'] * len(function_names))
    query = f"""
        SELECT name, c_code 
        FROM functions 
        WHERE sample_md5 = %s AND name IN ({placeholders})
        ORDER BY name
    """
    
    params = [md5] + function_names
    functions = execute_query(query, params, fetch_all=True)
    
    if not functions:
        return ""
    
    code_sections = []
    for func in functions:
        code_sections.append(f"// Function: {func['name']}\n{func['c_code']}\n")
    
    return "\n".join(code_sections)

def load_system_prompt() -> str:
    """
    Load the system prompt from organise.txt file.
    """
    try:
        with open("organise.txt", "r", encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "You are a malware analysis assistant. Analyze the provided malware report and enrich it with web search information."

def load_format_template() -> str:
    """
    Load the format template from organise-format.txt file and substitute tags.
    """
    try:
        with open("organise-format.txt", "r", encoding='utf-8') as f:
            template = f.read().strip()
    except FileNotFoundError:
        template = """You have collected various data from the web searches. Now, use the information you have gathered to enrich the malware report you were given, in the JSON specified.

{
  "iocs_table": "",
  "enriched_overview": "",
  "tags": ["tag1", "tag2"],
  "contentful_functions": {
    "function_name": "description"
  }
}"""
    
    # Get existing tags from database
    existing_tags = execute_query(
        "SELECT tagId, tag_content FROM tags ORDER BY tagId",
        fetch_all=True
    )
    
    if existing_tags:
        tags_list = [f"- {tag['tagId']}: {tag['tag_content']}" for tag in existing_tags]
        tags_string = "Existing tags:\n" + "\n".join(tags_list)
    else:
        tags_string = "No existing tags found."
    
    # Substitute {TAGS} placeholder
    return template.replace("{TAGS}", tags_string)

def chat_with_web_search(client: OpenAI, model: str, messages: List[Dict[str, Any]], include_tools: bool = True) -> Dict[str, Any]:
    """
    Perform a chat completion with optional web search capabilities.
    Returns the choice object from the completion.
    """
    for m in messages:
        if "Here is" in m["content"]: print("--omitted--")
        else: print(m)
    
    completion_args = {
        "model": model,
        "messages": messages,
        "temperature": 0.6,
    }
    
    if include_tools:
        completion_args["tools"] = [
            {
                "type": "builtin_function",
                "function": {
                    "name": "$web_search",
                },
            }
        ]
    
    completion = client.chat.completions.create(**completion_args)
    return completion.choices[0]

def run_organiser_agent(md5: str) -> None:
    """
    Run the organiser agent in background to enrich malware analysis.
    This function runs in a separate thread.
    """
    try:
        # Update status to organising
        execute_query(
            "UPDATE samples SET analyze_state = %s WHERE md5 = %s",
            (ANALYZE_STATE_ORGANISING, md5)
        )
        
        # Get the analysis report
        report_row = execute_query(
            "SELECT full_report FROM sample_details WHERE id = %s",
            (md5,),
            fetch_one=True
        )
        
        if not report_row or not report_row['full_report']:
            raise Exception("No analysis report found for this sample")
        
        report = report_row['full_report']
        
        # Extract significant functions
        significant_functions = extract_significant_functions(report)
        function_code = get_function_code(md5, significant_functions)
        
        # Load system prompt
        system_prompt = load_system_prompt()
        
        # Get OpenAI configuration
        model = os.getenv("BIG_MODEL", "gpt-4")
        api_key = os.getenv("BIG_MODEL_KEY")
        base_url = os.getenv("BIG_MODEL_ENDPOINT")
        
        if not api_key:
            raise ValueError("BIG_MODEL_KEY environment variable not set")
        
        # Initialize OpenAI client
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            
        client = OpenAI(**client_kwargs)
        
        # Prepare initial user message
        user_content = f"""Here is the malware analysis report:

{report}

Here are the significant functions' C code:

{function_code}

Please analyze this malware and conduct web searches to gather more intelligence about any indicators of compromise (IOCs) you find."""
        
        # Initialize conversation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        # Store initial messages (excluding the user prompt with report/code)
        messages_to_store = [
            {"role": "system", "content": system_prompt}
        ]
        execute_query(
            "UPDATE sample_details SET organiser_data = %s WHERE id = %s",
            (json.dumps(messages_to_store, indent=2), md5)
        )
        
        # Agentic loop - up to 5 web search iterations
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            # First iteration without tools, subsequent with tools
            include_tools = iteration > 0
            choice = chat_with_web_search(client, model, messages, include_tools)
            finish_reason = choice.finish_reason
            
            if finish_reason == "tool_calls":
                # Add assistant message with tool calls
                messages.append(choice.message.model_dump())
                
                # Process each tool call
                for tool_call in choice.message.tool_calls:
                    tool_call_name = tool_call.function.name
                    tool_call_arguments = json.loads(tool_call.function.arguments)
                    
                    if tool_call_name == "$web_search":
                        print(tool_call_arguments)
                        tool_result = search_impl(tool_call_arguments)
                    else:
                        tool_result = f"Error: unable to find tool by name '{tool_call_name}'"
                    
                    # Add tool result message
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call_name,
                        "content": json.dumps(tool_result),
                    })
                
                # Update database with current progress (excluding initial user prompt)
                messages_to_store = [msg for msg in messages if not (msg.get("role") == "user" and "Here is the malware analysis report:" in msg.get("content", ""))]
                execute_query(
                    "UPDATE sample_details SET organiser_data = %s WHERE id = %s",
                    (json.dumps(messages_to_store, indent=2), md5)
                )
                
                # Continue the conversation
                choice = chat_with_web_search(client, model, messages, include_tools=True)
                messages.append(choice.message.model_dump())
                
                # Add continuation message
                messages.append({
                    "role": "user", 
                    "content": "Thank you. YOU MUST NOW USE THE WEB SEARCH TOOL PROVIDED TO YOU. Execute your previously planned searches which you have yet to execute and summarise your findings."
                })
                
            else:
                # No tool calls, add the message and continue
                messages.append(choice.message.model_dump())
                
                # Add continuation message
                messages.append({
                    "role": "user", 
                    "content": "Thank you. YOU MUST NOW USE THE WEB SEARCH TOOL PROVIDED TO YOU. Execute your previously planned searches which you have yet to execute and summarise your findings."
                })
            
            iteration += 1
            
            # Update database with current progress (excluding initial user prompt)
            messages_to_store = [msg for msg in messages if not (msg.get("role") == "user" and "Here is the malware analysis report:" in msg.get("content", ""))]
            execute_query(
                "UPDATE sample_details SET organiser_data = %s WHERE id = %s",
                (json.dumps(messages_to_store, indent=2), md5)
            )
        
        # Final enrichment request
        format_template = load_format_template()
        messages.append({
            "role": "user",
            "content": format_template
        })
        
        # Get final enriched report in JSON format
        final_completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.6,
            response_format={"type": "json_object"},
            max_tokens=8192
        )
        
        final_response = final_completion.choices[0].message.content
        messages.append(final_completion.choices[0].message.model_dump())
        
        # Update database with final results (excluding initial user prompt)
        messages_to_store = [msg for msg in messages if not (msg.get("role") == "user" and "Here is the malware analysis report:" in msg.get("content", ""))]
        execute_query(
            "UPDATE sample_details SET organiser_data = %s WHERE id = %s",
            (json.dumps(messages_to_store, indent=2), md5)
        )
        
        # Parse and process the final enriched report
        try:
            enriched_data = json.loads(final_response)
            
            # 1. Append IOCs table to full_report
            if enriched_data.get('iocs_table'):
                current_report = execute_query(
                    "SELECT full_report FROM sample_details WHERE id = %s",
                    (md5,),
                    fetch_one=True
                )
                if current_report:
                    updated_report = current_report['full_report'] + "\n\n## IOCs\n\n" + enriched_data['iocs_table']
                    execute_query(
                        "UPDATE sample_details SET full_report = %s WHERE id = %s",
                        (updated_report, md5)
                    )
            
            # 2. Update overview in samples table
            if enriched_data.get('updated_overview'):
                execute_query(
                    "UPDATE samples SET overview = %s WHERE md5 = %s",
                    (enriched_data['updated_overview'], md5)
                )
            
            # 3. Insert/link tags
            if enriched_data.get('tags'):
                from modules.utils import random_id
                for tag_content in enriched_data['tags']:
                    # Check if tag already exists
                    existing_tag = execute_query(
                        "SELECT tagId FROM tags WHERE tag_content = %s",
                        (tag_content,),
                        fetch_one=True
                    )
                    
                    if existing_tag:
                        tag_id = existing_tag['tagId']
                    else:
                        # Create new tag
                        tag_id = random_id()
                        execute_query(
                            "INSERT INTO tags (tagId, tag_content) VALUES (%s, %s)",
                            (tag_id, tag_content)
                        )
                    
                    # Link tag to sample (ignore if already linked)
                    try:
                        execute_query(
                            "INSERT IGNORE INTO tags_sample (tagId, sample_md5) VALUES (%s, %s)",
                            (tag_id, md5)
                        )
                    except:
                        pass  # Ignore if already exists
            
            # 4. Update contentful functions descriptions
            if enriched_data.get('contentful_functions'):
                for func_name, description in enriched_data['contentful_functions'].items():
                    execute_query(
                        "UPDATE functions SET description = %s WHERE sample_md5 = %s AND name = %s",
                        (description, md5, func_name)
                    )
                        
        except json.JSONDecodeError:
            # If JSON parsing fails, just log the error
            print(f"Failed to parse JSON response for {md5}: {final_response}")
        except Exception as e:
            print(f"Error processing enriched data for {md5}: {str(e)}")
        
        # Mark as organised
        execute_query(
            "UPDATE samples SET analyze_state = %s WHERE md5 = %s",
            (ANALYZE_STATE_ORGANISED, md5)
        )
        
    except Exception as e:
        # Log error and reset state
        print(f"Organiser agent failed for {md5}: {str(e)}")
        execute_query(
            "UPDATE samples SET analyze_state = %s WHERE md5 = %s",
            (ANALYZE_STATE_ANALYSED, md5)  # Reset to analyzed state
        )
        # Store error in organiser_data
        error_data = {"error": str(e), "status": "failed"}
        execute_query(
            "UPDATE sample_details SET organiser_data = %s WHERE id = %s",
            (json.dumps(error_data, indent=2), md5)
        )

def start_organiser_agent(md5: str) -> Dict[str, Any]:
    """
    Start the organiser agent in background and return immediately.
    """
    from sql import execute_query
    
    # Check if sample exists and is analyzed
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
    
    # Check if sample has been analyzed
    if sample.get('analyze_state') < ANALYZE_STATE_ANALYSED:
        return {
            "success": False,
            "error": "Sample must be analyzed before organizing. Please run analysis first.",
            "status_code": 400
        }
    
    # Check if already organizing or organized
    if sample.get('analyze_state') == ANALYZE_STATE_ORGANISING:
        return {
            "success": False,
            "error": "Sample is already being organized",
            "status_code": 400
        }
    
    # if sample.get('analyze_state') == ANALYZE_STATE_ORGANISED:
    #     return {
    #         "success": True,
    #         "message": "Sample has already been organized",
    #         "sample_md5": md5,
    #         "already_organised": True
    #     }
    
    try:
        # Start the agent in background thread
        thread = threading.Thread(target=run_organiser_agent, args=(md5,))
        thread.daemon = True
        thread.start()
        
        return {
            "success": True,
            "message": "Organiser agent started successfully",
            "sample_md5": md5,
            "status": "organising"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to start organiser agent: {str(e)}",
            "status_code": 500
        }

def get_organiser_status(md5: str) -> Dict[str, Any]:
    """
    Get the status and data from the organiser agent.
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
    
    # Get organiser data
    details = execute_query(
        "SELECT organiser_data FROM sample_details WHERE id = %s",
        (md5,),
        fetch_one=True
    )
    
    if not details:
        return {
            "success": False,
            "error": "Sample details not found",
            "status_code": 404
        }
    
    organiser_data = None
    if details['organiser_data']:
        try:
            organiser_data = json.loads(details['organiser_data'])
        except json.JSONDecodeError:
            organiser_data = details['organiser_data']
    
    return {
        "success": True,
        "sample_md5": md5,
        "analyze_state": sample.get('analyze_state'),
        "organiser_data": organiser_data
    }