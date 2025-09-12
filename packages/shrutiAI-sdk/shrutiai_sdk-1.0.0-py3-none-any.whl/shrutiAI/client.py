"""
Main client class for shrutiAI SDK
"""

import requests
import json
from typing import Dict, List, Optional, Any
from .exceptions import ShrutiAIError, AuthenticationError, RateLimitError, NotFoundError, ValidationError


class ShrutiAIClient:
    """
    Client for interacting with shrutiAI API

    Usage:
        client = ShrutiAIClient(api_key="your-api-key")
        users = client.get_users()
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.myservice.com/v1"):
        """
        Initialize the API client
        
        Args:
            api_key: Your API key for authentication
            base_url: Base URL for the API (default: https://api.myservice.com/v1)
        """
        if not api_key:
            raise AuthenticationError("API key is required")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'shrutiAI-SDK/1.0.0'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to the API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests

        Returns:
            Dict containing the JSON response

        Raises:
            ShrutiAIError: For various API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle different HTTP status codes
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key", response.status_code, response)
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded", response.status_code, response)
            elif response.status_code == 404:
                raise NotFoundError("Resource not found", response.status_code, response)
            elif response.status_code == 422:
                raise ValidationError("Invalid request data", response.status_code, response)
            elif not response.ok:
                raise ShrutiAIError(f"API request failed: {response.text}", response.status_code, response)

            # Try to parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"message": response.text}

        except requests.RequestException as e:
            raise ShrutiAIError(f"Network error: {str(e)}")
    
    # User Management Methods
    def get_users(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get list of users
        
        Args:
            limit: Number of users to return (default: 10)
            offset: Number of users to skip (default: 0)
            
        Returns:
            List of user dictionaries
        """
        params = {'limit': limit, 'offset': offset}
        response = self._make_request('GET', '/users', params=params)
        return response.get('data', [])
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get a specific user by ID
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User dictionary
        """
        response = self._make_request('GET', f'/users/{user_id}')
        return response.get('data', {})
    
    def create_user(self, name: str, email: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            name: User's name
            email: User's email address
            **kwargs: Additional user data
            
        Returns:
            Created user dictionary
        """
        data = {'name': name, 'email': email, **kwargs}
        response = self._make_request('POST', '/users', json=data)
        return response.get('data', {})
    
    def update_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an existing user
        
        Args:
            user_id: The user's unique identifier
            **kwargs: Fields to update
            
        Returns:
            Updated user dictionary
        """
        response = self._make_request('PUT', f'/users/{user_id}', json=kwargs)
        return response.get('data', {})
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            True if deletion was successful
        """
        self._make_request('DELETE', f'/users/{user_id}')
        return True
    
    # Posts Management Methods
    def get_posts(self, user_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of posts
        
        Args:
            user_id: Filter posts by user ID (optional)
            limit: Number of posts to return (default: 10)
            
        Returns:
            List of post dictionaries
        """
        params = {'limit': limit}
        if user_id:
            params['user_id'] = user_id
            
        response = self._make_request('GET', '/posts', params=params)
        return response.get('data', [])
    
    def create_post(self, title: str, content: str, user_id: str) -> Dict[str, Any]:
        """
        Create a new post
        
        Args:
            title: Post title
            content: Post content
            user_id: ID of the user creating the post
            
        Returns:
            Created post dictionary
        """
        data = {'title': title, 'content': content, 'user_id': user_id}
        response = self._make_request('POST', '/posts', json=data)
        return response.get('data', {})
    
    # Analytics Methods
    def get_analytics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get analytics data for a date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Analytics data dictionary
        """
        params = {'start_date': start_date, 'end_date': end_date}
        response = self._make_request('GET', '/analytics', params=params)
        return response.get('data', {})
    
    # Utility Methods
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status
        
        Returns:
            Health status dictionary
        """
        response = self._make_request('GET', '/health')
        return response
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get API information and version
        
        Returns:
            API info dictionary
        """
        response = self._make_request('GET', '/info')
        return response
