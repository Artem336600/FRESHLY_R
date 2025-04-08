import os
import requests
import json
import logging
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_recommendations(theme: str, supabase) -> Tuple[List[dict], Optional[str]]:
    """
    Get product recommendations based on a theme using DeepSeek API.
    
    Args:
        theme (str): The theme to get recommendations for
        supabase: Supabase client instance
        
    Returns:
        Tuple[List[dict], Optional[str]]: List of recommendations and optional error message
    """
    try:
        # Input validation
        if not theme or not isinstance(theme, str):
            return [], "Invalid theme provided"
            
        # Get API key from environment
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return [], "API key not found in environment variables"
            
        # Construct the prompt
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful shopping assistant that recommends products based on themes. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": f"""Recommend 5 products for the theme: {theme}. 
Format your response as a JSON array with objects containing these exact fields:
- name: string (product name)
- description: string (brief product description)
- explanation: string (why this product is recommended)

Example format:
[
    {{
        "name": "Product Name",
        "description": "Product description",
        "explanation": "Why this product is recommended"
    }}
]

Return ONLY the JSON array, nothing else."""
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Make API request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            return [], f"Failed to get recommendations: {response.status_code}"
            
        # Parse response
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        # Log the raw content for debugging
        logger.info(f"Raw API response content: {content}")
        
        # Extract recommendations from content
        try:
            # Try to find JSON array in the content
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                recommendations = json.loads(json_str)
            else:
                recommendations = json.loads(content)
                
            if not isinstance(recommendations, list):
                recommendations = [recommendations]
                
            # Add placeholder image URLs
            for rec in recommendations:
                rec["image_url"] = "https://via.placeholder.com/150"
                
            return recommendations, None
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse recommendations: {e}\nContent: {content}")
            return [], "Failed to parse recommendations from API response"
            
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return [], f"Request failed: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return [], f"An unexpected error occurred: {str(e)}" 