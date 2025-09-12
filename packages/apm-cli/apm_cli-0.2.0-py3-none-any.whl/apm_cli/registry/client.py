"""Simple MCP Registry client for server discovery."""

import os
import requests
from typing import Dict, List, Optional, Any, Tuple


class SimpleRegistryClient:
    """Simple client for querying MCP registries for server discovery."""

    def __init__(self, registry_url: Optional[str] = None):
        """Initialize the registry client.

        Args:
            registry_url (str, optional): URL of the MCP registry.
                If not provided, uses the MCP_REGISTRY_URL environment variable
                or falls back to the default demo registry.
        """
        self.registry_url = registry_url or os.environ.get(
            "MCP_REGISTRY_URL", "https://api.mcp.github.com"
        )
        self.session = requests.Session()

    def list_servers(self, limit: int = 100, cursor: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """List all available servers in the registry.

        Args:
            limit (int, optional): Maximum number of entries to return. Defaults to 100.
            cursor (str, optional): Pagination cursor for retrieving next set of results.

        Returns:
            Tuple[List[Dict[str, Any]], Optional[str]]: List of server metadata dictionaries and the next cursor if available.
        
        Raises:
            requests.RequestException: If the request fails.
        """
        url = f"{self.registry_url}/v0/servers"
        params = {}
        
        if limit is not None:
            params['limit'] = limit
        if cursor is not None:
            params['cursor'] = cursor
            
        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract servers - they're nested under "server" key in each item
        raw_servers = data.get("servers", [])
        servers = []
        for item in raw_servers:
            if "server" in item:
                servers.append(item["server"])
            else:
                servers.append(item)  # Fallback for different structure
                
        metadata = data.get("metadata", {})
        next_cursor = metadata.get("next_cursor")
        
        return servers, next_cursor

    def search_servers(self, query: str) -> List[Dict[str, Any]]:
        """Search for servers in the registry using the API search endpoint.

        Args:
            query (str): Search query string.

        Returns:
            List[Dict[str, Any]]: List of matching server metadata dictionaries.
        
        Raises:
            requests.RequestException: If the request fails.
        """
        url = f"{self.registry_url}/v0/servers/search"
        params = {'q': query}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract servers - they're nested under "server" key in each item
        raw_servers = data.get("servers", [])
        servers = []
        for item in raw_servers:
            if "server" in item:
                servers.append(item["server"])
            else:
                servers.append(item)  # Fallback for different structure
                
        return servers

    def get_server_info(self, server_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific server.

        Args:
            server_id (str): ID of the server.

        Returns:
            Dict[str, Any]: Server metadata dictionary.
        
        Raises:
            requests.RequestException: If the request fails.
            ValueError: If the server is not found.
        """
        url = f"{self.registry_url}/v0/servers/{server_id}"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Return the complete response including x-github and other metadata
        # but ensure the main server info is accessible at the top level
        if "server" in data:
            # Merge server info to top level while preserving x-github and other sections
            result = data["server"].copy()
            for key, value in data.items():
                if key != "server":
                    result[key] = value
            
            if not result:
                raise ValueError(f"Server '{server_id}' not found in registry")
                
            return result
        else:
            if not data:
                raise ValueError(f"Server '{server_id}' not found in registry")
            return data
        
    def get_server_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a server by its name using the search API.

        Args:
            name (str): Name of the server to find.

        Returns:
            Optional[Dict[str, Any]]: Server metadata dictionary or None if not found.
        
        Raises:
            requests.RequestException: If the request fails.
        """
        # Use search API to find by name - more efficient than listing all servers
        try:
            search_results = self.search_servers(name)
            
            # Look for an exact match in search results
            for server in search_results:
                if server.get("name") == name:
                    return self.get_server_info(server["id"])
                    
        except Exception:
            pass
                    
        return None
    

    
    def find_server_by_reference(self, reference: str) -> Optional[Dict[str, Any]]:
        """Find a server by exact name match or server ID.

        This is an efficient lookup that uses the search API:
        1. Server ID (UUID format) - direct API call
        2. Server name - search API for exact match

        Args:
            reference (str): Server reference (ID or exact name).

        Returns:
            Optional[Dict[str, Any]]: Server metadata dictionary or None if not found.
        
        Raises:
            requests.RequestException: If the request fails.
        """
        # Strategy 1: Try as server ID first (direct lookup)
        try:
            # Check if it looks like a UUID (contains hyphens and is 36 chars)
            if len(reference) == 36 and reference.count('-') == 4:
                return self.get_server_info(reference)
        except (ValueError, Exception):
            pass
        
        # Strategy 2: Use search API to find by name
        try:
            search_results = self.search_servers(reference)
            
            # Look for an exact match in search results
            for server in search_results:
                if server.get("name") == reference:
                    return self.get_server_info(server["id"])
                    
        except Exception:
            pass
                    
        # If not found by ID or exact name, server is not in registry
        return None