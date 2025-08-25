#!/usr/bin/env python3
"""
NetBox Client Library

This module provides a base class for NetBox client implementations and a REST API implementation.
"""

import abc
from typing import Any, Dict, List, Optional, Union
import requests
import logging


class NetBoxClientBase(abc.ABC):
    """
    Abstract base class for NetBox client implementations.
    
    This class defines the interface for CRUD operations that can be implemented
    either via the REST API or directly via the ORM in a NetBox plugin.
    """
    
    @abc.abstractmethod
    def get(self, endpoint: str, id: Optional[int] = None, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Retrieve one or more objects from NetBox.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            id: Optional ID to retrieve a specific object
            params: Optional query parameters for filtering
            
        Returns:
            Either a single object dict or a list of object dicts
        """
        pass
    
    @abc.abstractmethod
    def create(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new object in NetBox.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            data: Object data to create
            
        Returns:
            The created object as a dict
        """
        pass
    
    @abc.abstractmethod
    def update(self, endpoint: str, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing object in NetBox.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            id: ID of the object to update
            data: Object data to update
            
        Returns:
            The updated object as a dict
        """
        pass
    
    @abc.abstractmethod
    def delete(self, endpoint: str, id: int) -> bool:
        """
        Delete an object from NetBox.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            id: ID of the object to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def bulk_create(self, endpoint: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple objects in NetBox.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            data: List of object data to create
            
        Returns:
            List of created objects as dicts
        """
        pass
    
    @abc.abstractmethod
    def bulk_update(self, endpoint: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update multiple objects in NetBox.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            data: List of object data to update (must include ID)
            
        Returns:
            List of updated objects as dicts
        """
        pass
    
    @abc.abstractmethod
    def bulk_delete(self, endpoint: str, ids: List[int]) -> bool:
        """
        Delete multiple objects from NetBox.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            ids: List of IDs to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass


class NetBoxRestClient(NetBoxClientBase):
    """
    NetBox client implementation using the REST API.
    """

# # Example of how to use the client
# client = NetBoxRestClient(
#     url="https://netbox.example.com",
#     token="your_api_token_here",
#     verify_ssl=True
# )
    
# # Get all sites
# sites = client.get("dcim/sites")
# print(f"Found {len(sites)} sites")
    
# # Get a specific site
# site = client.get("dcim/sites", id=1)
# print(f"Site name: {site.get('name')}")
    
# # Create a new site
# new_site = client.create("dcim/sites", {
#     "name": "New Site",
#     "slug": "new-site",
#     "status": "active"
# })
# print(f"Created site: {new_site.get('name')} (ID: {new_site.get('id')})")

    def __init__(self, url: str, token: str, verify_ssl: bool = True):
        """
        Initialize the REST API client.
        
        Args:
            url: The base URL of the NetBox instance (e.g., 'https://netbox.example.com')
            token: API token for authentication
            verify_ssl: Whether to verify SSL certificates
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.base_url = url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.token = token
        self.verify_ssl = verify_ssl
        
        self.logger.debug(f"Initializing NetBox REST client for {self.base_url}")
        self.logger.debug(f"SSL verification: {verify_ssl}")
        
        self.session = requests.Session()
        
        # Extract hostname from URL for Host header
        from urllib.parse import urlparse
        parsed_url = urlparse(self.base_url)
        host_header = parsed_url.netloc
        
        self.session.headers.update({
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Host': host_header,
            'User-Agent': 'NetBox-MCP-Server/1.0',
        })
        
        self.logger.debug(f"Session headers configured: {dict(self.session.headers)}")
        self.logger.debug("NetBox REST client initialized successfully")
    
    def _build_url(self, endpoint: str, id: Optional[int] = None) -> str:
        """Build the full URL for an API request."""
        endpoint = endpoint.strip('/')
        if id is not None:
            return f"{self.api_url}/{endpoint}/{id}/"
        return f"{self.api_url}/{endpoint}/"
    
    def get(self, endpoint: str, id: Optional[int] = None, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Retrieve one or more objects from NetBox via the REST API.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            id: Optional ID to retrieve a specific object
            params: Optional query parameters for filtering
            
        Returns:
            Either a single object dict or a list of object dicts
        
        Raises:
            requests.HTTPError: If the request fails
        """
        url = self._build_url(endpoint, id)
        self.logger.debug(f"Built URL: {url}")
        self.logger.debug(f"Request params: {params}")
        self.logger.debug(f"Request headers: {dict(self.session.headers)}")
        
        try:
            response = self.session.get(url, params=params, verify=self.verify_ssl)
            
            # Log detailed request information
            self.logger.debug(f"Final request URL: {response.url}")
            self.logger.debug(f"Request method: {response.request.method}")
            self.logger.debug(f"Request headers sent: {dict(response.request.headers)}")
            self.logger.debug(f"Response status: {response.status_code}")
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            
            # Log response content for debugging
            if response.status_code >= 400:
                self.logger.error(f"Error response body: {response.text}")
            else:
                # Only log first 500 chars of successful response to avoid spam
                response_preview = response.text[:500] + "..." if len(response.text) > 500 else response.text
                self.logger.debug(f"Response body preview: {response_preview}")
            
            response.raise_for_status()
            
            data = response.json()
            if id is None and 'results' in data:
                # Handle paginated results
                result_count = len(data['results'])
                total_count = data.get('count', result_count)
                self.logger.debug(f"Retrieved {result_count} objects from paginated response (total: {total_count})")
                return data['results']
            else:
                self.logger.debug("Retrieved single object")
                return data
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request failed for {url}: {str(e)}")
            self.logger.error(f"Request details - Method: GET, URL: {url}, Params: {params}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response body: {e.response.text}")
            raise
    
    def create(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new object in NetBox via the REST API.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            data: Object data to create
            
        Returns:
            The created object as a dict
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = self._build_url(endpoint)
        response = self.session.post(url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()
    
    def update(self, endpoint: str, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing object in NetBox via the REST API.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            id: ID of the object to update
            data: Object data to update
            
        Returns:
            The updated object as a dict
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = self._build_url(endpoint, id)
        response = self.session.patch(url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str, id: int) -> bool:
        """
        Delete an object from NetBox via the REST API.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            id: ID of the object to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = self._build_url(endpoint, id)
        response = self.session.delete(url, verify=self.verify_ssl)
        response.raise_for_status()
        return response.status_code == 204
    
    def bulk_create(self, endpoint: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple objects in NetBox via the REST API.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            data: List of object data to create
            
        Returns:
            List of created objects as dicts
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self._build_url(endpoint)}bulk/"
        response = self.session.post(url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()
    
    def bulk_update(self, endpoint: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update multiple objects in NetBox via the REST API.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            data: List of object data to update (must include ID)
            
        Returns:
            List of updated objects as dicts
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self._build_url(endpoint)}bulk/"
        response = self.session.patch(url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()
    
    def bulk_delete(self, endpoint: str, ids: List[int]) -> bool:
        """
        Delete multiple objects from NetBox via the REST API.
        
        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            ids: List of IDs to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self._build_url(endpoint)}bulk/"
        data = [{"id": id} for id in ids]
        response = self.session.delete(url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.status_code == 204
