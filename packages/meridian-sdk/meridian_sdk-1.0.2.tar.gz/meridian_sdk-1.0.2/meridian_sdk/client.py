"""
Meridian API SDK - Python Client Library
Complete SDK for testing and integrating with the Meridian External API
"""

import httpx
import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class APIResponse:
    """Structured API response wrapper"""
    success: bool
    data: Any
    status_code: int
    headers: Dict[str, str]
    error: Optional[str] = None


class MeridianAPIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message: str, status_code: int = None, response: Dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class MeridianAPI:
    """
    Meridian API SDK Client
    
    Provides easy access to all Meridian External API endpoints with
    proper error handling, retries, and response formatting.
    """
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str = "https://dashboard.trymeridian.dev",
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # API endpoints
        self.endpoints = {
            'search': f'{self.base_url}/api/v1/search',
            'usage': f'{self.base_url}/api/v1/usage',
            'health': f'{self.base_url}/api/v1/health',
            'limits': f'{self.base_url}/api/v1/limits',
            'validate': f'{self.base_url}/api/v1/validate',
            'status': f'{self.base_url}/api/v1/status',
            'connectors_status': f'{self.base_url}/api/v1/connectors/status',
            'connectors_connect': f'{self.base_url}/api/v1/connectors/connect',
            'manage_keys': f'{self.base_url}/api/manage/keys',
            'pricing': f'{self.base_url}/api/manage/pricing',
        }
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MeridianSDK/1.0.0'
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> APIResponse:
        """Internal method to make HTTP requests with retry logic"""
        
        try:
            if method.upper() == 'GET':
                response = await self.client.get(url, params=params)
            elif method.upper() == 'POST':
                response = await self.client.post(url, json=data, params=params)
            elif method.upper() == 'PUT':
                response = await self.client.put(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = await self.client.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            # Check if request was successful
            if response.status_code < 400:
                return APIResponse(
                    success=True,
                    data=response_data,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            else:
                # Handle API errors
                error_msg = "API request failed"
                if isinstance(response_data, dict):
                    error_msg = response_data.get('detail', 
                        response_data.get('error', {}).get('message', error_msg))
                
                return APIResponse(
                    success=False,
                    data=response_data,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    error=error_msg
                )
        
        except httpx.RequestError as e:
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self._make_request(method, url, data, params, retry_count + 1)
            
            return APIResponse(
                success=False,
                data=None,
                status_code=0,
                headers={},
                error=f"Network error: {str(e)}"
            )
    
    # === SEARCH API ===
    
    async def search(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        processing_mode: str = "auto",
        max_results: int = 10,
        sources: Optional[List[str]] = None,
        include_sources: bool = True,
        include_related: bool = False
    ) -> APIResponse:
        """
        Perform an AI-powered search across connected data sources
        
        Args:
            prompt: Search query (3-2000 characters)
            conversation_id: Optional conversation context
            session_id: Optional session context  
            processing_mode: 'auto', 'standard', or 'agentic'
            max_results: Number of results (1-100)
            sources: Filter by data sources ['sharepoint', 'google_drive']
            include_sources: Include source documents in response
            include_related: Include related queries
            
        Returns:
            APIResponse with search results, sources, and metadata
        """
        
        payload = {
            "prompt": prompt,
            "options": {
                "processing_mode": processing_mode,
                "max_results": max_results,
                "include_sources": include_sources,
                "include_related": include_related
            }
        }
        
        if conversation_id or session_id:
            payload["context"] = {}
            if conversation_id:
                payload["context"]["conversation_id"] = conversation_id
            if session_id:
                payload["context"]["session_id"] = session_id
        
        if sources:
            payload["filters"] = {"sources": sources}
        
        return await self._make_request('POST', self.endpoints['search'], payload)
    
    # === USAGE & BILLING API ===
    
    async def get_usage(self) -> APIResponse:
        """Get detailed usage statistics and billing information"""
        return await self._make_request('GET', self.endpoints['usage'])
    
    async def get_limits(self) -> APIResponse:
        """Get current rate limits and usage quotas"""
        return await self._make_request('GET', self.endpoints['limits'])
    
    # === HEALTH & STATUS API ===
    
    async def health_check(self) -> APIResponse:
        """Get comprehensive system health status"""
        return await self._make_request('GET', self.endpoints['health'])
    
    async def get_status(self) -> APIResponse:
        """Get API status and feature information"""
        return await self._make_request('GET', self.endpoints['status'])
    
    # === VALIDATION API ===
    
    async def validate_request(
        self,
        prompt: str,
        processing_mode: str = "auto"
    ) -> APIResponse:
        """Validate a search request without executing it"""
        
        payload = {
            "prompt": prompt,
            "options": {"processing_mode": processing_mode}
        }
        
        return await self._make_request('POST', self.endpoints['validate'], payload)
    
    # === CONNECTOR MANAGEMENT API ===
    
    async def get_connector_status(self) -> APIResponse:
        """Get status of connected data sources"""
        return await self._make_request('GET', self.endpoints['connectors_status'])
    
    async def connect_data_source(self, provider: str) -> APIResponse:
        """
        Initiate connection to a data source
        
        Args:
            provider: 'microsoft' (SharePoint) or 'google' (Google Drive)
        """
        payload = {"provider": provider}
        return await self._make_request('POST', self.endpoints['connectors_connect'], payload)
    
    # === API KEY MANAGEMENT ===
    
    async def get_api_keys(self) -> APIResponse:
        """Get list of API keys (requires user authentication)"""
        return await self._make_request('GET', self.endpoints['manage_keys'])
    
    async def get_pricing_info(self) -> APIResponse:
        """Get usage-based pricing information"""
        return await self._make_request('GET', self.endpoints['pricing'])
    
    # === UTILITY METHODS ===
    
    async def test_connection(self) -> bool:
        """Test if the API is accessible and authentication works"""
        try:
            response = await self.get_status()
            return response.success
        except:
            return False
    
    def get_rate_limit_info(self, response: APIResponse) -> Dict[str, Any]:
        """Extract rate limit information from API response headers"""
        headers = response.headers
        return {
            'limit': headers.get('X-RateLimit-Limit'),
            'remaining': headers.get('X-RateLimit-Remaining'), 
            'reset': headers.get('X-RateLimit-Reset'),
            'reset_time': datetime.fromtimestamp(int(headers.get('X-RateLimit-Reset', 0)))
                if headers.get('X-RateLimit-Reset') else None
        }


# === HELPER FUNCTIONS ===

def create_client(api_key: str, base_url: str = "https://dashboard.trymeridian.dev") -> MeridianAPI:
    """Convenience function to create a Meridian API client"""
    return MeridianAPI(api_key, base_url)


def print_response(response: APIResponse, title: str = "API Response"):
    """Pretty print API response for debugging"""
    print(f"\n=== {title} ===")
    print(f"Success: {'✅' if response.success else '❌'}")
    print(f"Status Code: {response.status_code}")
    
    if response.error:
        print(f"Error: {response.error}")
    
    if response.data:
        print("Response Data:")
        print(json.dumps(response.data, indent=2, default=str))
    
    print("=" * (len(title) + 8))


# === EXAMPLE USAGE ===

async def example_usage():
    """Example of how to use the Meridian API SDK"""
    
    # Initialize client
    api_key = "your_api_key_here"
    
    async with MeridianAPI(api_key) as client:
        
        # Test connection
        print("Testing connection...")
        if await client.test_connection():
            print("✅ Connected to Meridian API")
        else:
            print("❌ Failed to connect to API")
            return
        
        # Get API status
        status = await client.get_status()
        print_response(status, "API Status")
        
        # Perform search
        search_result = await client.search(
            prompt="What are our Q4 sales numbers?",
            processing_mode="agentic",
            include_sources=True
        )
        print_response(search_result, "Search Results")
        
        # Get usage statistics
        usage = await client.get_usage()
        print_response(usage, "Usage Statistics")
        
        # Check connector status
        connectors = await client.get_connector_status()
        print_response(connectors, "Connector Status")


if __name__ == "__main__":
    asyncio.run(example_usage())