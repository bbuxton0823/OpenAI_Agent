"""
Utility functions for web search functionality.
In a production environment, you would replace these with actual API calls.
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from agents import function_tool
from datetime import datetime

@function_tool
def search_web(query: str) -> str:
    """Search the web for information on a given query"""
    # Try to use Google Custom Search if API key is available
    google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    google_cx = os.getenv("GOOGLE_SEARCH_CX")
    
    if google_api_key and google_cx:
        return google_search(query, google_api_key, google_cx)
    
    # Try to use Bing Search if API key is available
    bing_api_key = os.getenv("BING_SEARCH_API_KEY")
    if bing_api_key:
        return bing_search(query, bing_api_key)
    
    # Fall back to mock search
    return mock_search(query)

def google_search(query: str, api_key: str, cx: str) -> str:
    """Perform a search using Google Custom Search API"""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": 5
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()
        
        if "items" not in results:
            return f"No results found for query: {query}"
        
        formatted_results = []
        for item in results["items"]:
            formatted_results.append({
                "title": item.get("title", "No title"),
                "link": item.get("link", "No link"),
                "snippet": item.get("snippet", "No description")
            })
        
        return json.dumps(formatted_results, indent=2)
    except Exception as e:
        return f"Error performing Google search: {str(e)}"

def bing_search(query: str, api_key: str) -> str:
    """Perform a search using Bing Search API"""
    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": query, "count": 5}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        results = response.json()
        
        if "webPages" not in results or "value" not in results["webPages"]:
            return f"No results found for query: {query}"
        
        formatted_results = []
        for item in results["webPages"]["value"]:
            formatted_results.append({
                "title": item.get("name", "No title"),
                "link": item.get("url", "No link"),
                "snippet": item.get("snippet", "No description")
            })
        
        return json.dumps(formatted_results, indent=2)
    except Exception as e:
        return f"Error performing Bing search: {str(e)}"

def mock_search(query: str) -> str:
    """Mock search function for demonstration purposes"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    results = [
        {
            "title": f"Search Results for: {query}",
            "link": "https://example.com/search",
            "snippet": f"This is a mock search result for '{query}'. In a production environment, this would be replaced with actual search results from a search API."
        },
        {
            "title": f"More Information About: {query}",
            "link": "https://example.com/info",
            "snippet": f"Additional information about '{query}'. This is a simulated result for demonstration purposes only."
        },
        {
            "title": f"Latest News on: {query}",
            "link": "https://example.com/news",
            "snippet": f"Latest updates about '{query}' as of {current_date}. This is a mock result."
        }
    ]
    
    return json.dumps(results, indent=2) 