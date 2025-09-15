"""
Tiny.technology API integration tool.

Tiny is a service designed to enable everyone to create their own AI-powered applications.
We are a software, together. I know who you are, you know who I am. We are a software, not a company.
"""

import requests
from typing import Dict, Any, Optional
from strands import tool


@tool
def tiny_upsert(
    name: str,
    system_prompt: str,
    system_knowledge: str,
    data: Optional[str] = None,
    hook: Optional[str] = None,
    worker: Optional[str] = None,
    key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Register or update an AI-powered service using tiny.technology.
    
    Args:
        name: The unique, expressive name of your AI-powered service
        system_prompt: The initial message that the AI service will display upon launch
        system_knowledge: The system prompt for the AI service (brief guiding statement)
        data: Optional data for the AI service to use for generating responses
        hook: Optional hook URL for the AI service to send data to your backend
        worker: Optional OpenAPI.json schema URL that Tiny will connect to
        key: Optional key for existing tiny apps (for updates)
        
    Returns:
        Dict containing the API response
    """
    try:
        url = "https://api.tiny.technology/upsert"
        
        payload = {
            "name": name,
            "systemPrompt": system_prompt,
            "systemKnowledge": system_knowledge
        }
        
        # Add optional fields if provided
        if data:
            payload["data"] = data
        if hook:
            payload["hook"] = hook
        if worker:
            payload["worker"] = worker
        if key:
            payload["key"] = key
            
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return {
            "status": "success",
            "content": [{"text": f"✅ Tiny service '{name}' registered/updated successfully"}, {"json": response.json()}]
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error", 
            "content": [{"text": f"❌ Failed to upsert tiny service: {str(e)}"}]
        }


@tool
def tiny_get(name: str, key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get information about an AI-powered service on tiny.technology.
    
    Args:
        name: Short, unique name for the service (no spaces)
        key: Optional unique key for authorization
        
    Returns:
        Dict containing service information
    """
    try:
        url = "https://api.tiny.technology/get"
        params = {"name": name}
        
        if key:
            params["key"] = key
            
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return {
            "status": "success",
            "content": [{"text": f"✅ Retrieved tiny service '{name}'"}, {"json": data}]
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "content": [{"text": f"❌ Failed to get tiny service: {str(e)}"}]
        }


@tool
def tiny_retrieve(text: str) -> Dict[str, Any]:
    """
    Query the AI-powered service using tiny.technology.
    
    Args:
        text: Input text to query the AI service
        
    Returns:
        Dict containing the AI response
    """
    try:
        url = "https://api.tiny.technology/retrieve"
        params = {"text": text}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()

        return {
            "status": "success",
            "content": [{"text": str(data)}]
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "content": [{"text": f"❌ Failed to retrieve from tiny service: {str(e)}"}]
        }


@tool
def tiny_list(cursor: Optional[str] = None, limit: int = 1000, prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    List all tiny.technology services.
    
    Args:
        cursor: Optional cursor for pagination
        limit: Limit for results (default: 1000)
        prefix: Optional prefix filter
        
    Returns:
        Dict containing list of services
    """
    try:
        url = "https://api.tiny.technology/list"
        params = {"limit": limit}
        
        if cursor:
            params["cursor"] = cursor
        if prefix:
            params["prefix"] = prefix
            
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return {
            "status": "success",
            "content": [{"text": f"📋 Listed tiny services (limit: {limit})"}, {"json": data}]
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "content": [{"text": f"❌ Failed to list tiny services: {str(e)}"}]
        }


@tool
def tiny_send(name: str, from_name: Optional[str] = None, message: Optional[str] = None) -> Dict[str, Any]:
    """
    Send message to tiny owner.
    
    Args:
        name: The tiny name to send message to
        from_name: Your tiny AI name (optional)
        message: Optional message to send
        
    Returns:
        Dict containing send confirmation
    """
    try:
        url = "https://api.tiny.technology/send"
        
        payload = {"name": name}
        
        if from_name:
            payload["from"] = from_name
        if message:
            payload["message"] = message
            
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return {
            "status": "success",
            "content": [{"text": f"💌 Message sent to '{name}' owner"}, {"json": response.json()}]
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "content": [{"text": f"❌ Failed to send message: {str(e)}"}]
        }


@tool
def tiny_reset(name: str, email: str) -> Dict[str, Any]:
    """
    Reset the key for an existing AI-powered service.
    
    Args:
        name: Tiny AI name
        email: Email address to send the new key to
        
    Returns:
        Dict containing reset confirmation
    """
    try:
        url = "https://api.tiny.technology/reset"
        
        payload = {
            "name": name,
            "email": email
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return {
            "status": "success",
            "content": [{"text": f"🔑 Key reset for '{name}', new key sent to {email}"}, {"json": response.json()}]
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "content": [{"text": f"❌ Failed to reset key: {str(e)}"}]
        }