#!/usr/bin/env python3
"""
NetBox Client Library

This module provides a base class for NetBox client implementations and a REST API implementation.
"""

import abc
from typing import Any, Optional

import requests


class NetBoxClientBase(abc.ABC):
    """
    Abstract base class for NetBox client implementations.

    This class defines the interface for CRUD operations that can be implemented
    either via the REST API or directly via the ORM in a NetBox plugin.
    """

    @abc.abstractmethod
    def get(
        self,
        endpoint: str,
        id: Optional[int] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Retrieve one or more objects from NetBox.

        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            id: Optional ID to retrieve a specific object
            params: Optional query parameters for filtering

        Returns:
            For single object queries (with id): Returns the object dict
            For list queries (without id): Returns the full paginated response dict with:
                - count: Total number of objects matching the query
                         ALWAYS REFER TO THIS FIELD FOR THE TOTAL NUMBER OF OBJECTS MATCHING THE QUERY
                - next: URL to next page (or null if no more pages)
                        ALWAYS REFER TO THIS FIELD FOR THE NEXT PAGE OF RESULTS
                - previous: URL to previous page (or null if on first page)
                            ALWAYS REFER TO THIS FIELD FOR THE PREVIOUS PAGE OF RESULTS
                - results: Array of objects for this page
                           ALWAYS REFER TO THIS FIELD FOR THE OBJECTS ON THIS PAGE
        """
        pass

    @abc.abstractmethod
    def create(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
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
    def update(self, endpoint: str, id: int, data: dict[str, Any]) -> dict[str, Any]:
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
    def bulk_create(
        self, endpoint: str, data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
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
    def bulk_update(
        self, endpoint: str, data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
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
    def bulk_delete(self, endpoint: str, ids: list[int]) -> bool:
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
        self.base_url = url.rstrip("/")
        self.api_url = f"{self.base_url}/api"
        self.token = token
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Token {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _build_url(self, endpoint: str, id: Optional[int] = None) -> str:
        """Build the full URL for an API request."""
        endpoint = endpoint.strip("/")
        if id is not None:
            return f"{self.api_url}/{endpoint}/{id}/"
        return f"{self.api_url}/{endpoint}/"

    def get(
        self,
        endpoint: str,
        id: Optional[int] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Retrieve one or more objects from NetBox via the REST API.

        Args:
            endpoint: The API endpoint (e.g., 'dcim/sites', 'ipam/prefixes')
            id: Optional ID to retrieve a specific object
            params: Optional query parameters for filtering

        Returns:
            For single object queries (with id): Returns the object dict
            For list queries (without id): Returns the full paginated response dict with:
                - count: Total number of objects matching the query
                - next: URL to next page (or null)
                - previous: URL to previous page (or null)
                - results: Array of objects for this page

        Raises:
            requests.HTTPError: If the request fails
        """
        url = self._build_url(endpoint, id)
        response = self.session.get(url, params=params, verify=self.verify_ssl)
        response.raise_for_status()

        return response.json()

    def create(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
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

    def update(self, endpoint: str, id: int, data: dict[str, Any]) -> dict[str, Any]:
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

    def bulk_create(
        self, endpoint: str, data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
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

    def bulk_update(
        self, endpoint: str, data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
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

    def bulk_delete(self, endpoint: str, ids: list[int]) -> bool:
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
