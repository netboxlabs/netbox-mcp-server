import os
import json
import time
import logging
import asyncio
import sys
import threading
from typing import Dict, Any
from netbox_client import NetBoxRestClient
import inspect
from urllib.parse import urljoin, urlencode
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("netbox_mcp")

# Environment variables
NETBOX_URL = os.getenv("NETBOX_URL")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN")

if not NETBOX_URL or not NETBOX_TOKEN:
    raise ValueError("Missing NETBOX_URL or NETBOX_TOKEN")

# Mapping of simple object names to API endpoints
NETBOX_OBJECT_TYPES = {
    # DCIM (Device and Infrastructure)
    "cables": "dcim/cables",
    "console-ports": "dcim/console-ports",
    "console-server-ports": "dcim/console-server-ports",
    "devices": "dcim/devices",
    "device-bays": "dcim/device-bays",
    "device-roles": "dcim/device-roles",
    "device-types": "dcim/device-types",
    "front-ports": "dcim/front-ports",
    "interfaces": "dcim/interfaces",
    "inventory-items": "dcim/inventory-items",
    "locations": "dcim/locations",
    "manufacturers": "dcim/manufacturers",
    "modules": "dcim/modules",
    "module-bays": "dcim/module-bays",
    "module-types": "dcim/module-types",
    "platforms": "dcim/platforms",
    "power-feeds": "dcim/power-feeds",
    "power-outlets": "dcim/power-outlets",
    "power-panels": "dcim/power-panels",
    "power-ports": "dcim/power-ports",
    "racks": "dcim/racks",
    "rack-reservations": "dcim/rack-reservations",
    "rack-roles": "dcim/rack-roles",
    "regions": "dcim/regions",
    "sites": "dcim/sites",
    "site-groups": "dcim/site-groups",
    "virtual-chassis": "dcim/virtual-chassis",
    # IPAM (IP Address Management)
    "asns": "ipam/asns",
    "asn-ranges": "ipam/asn-ranges",
    "aggregates": "ipam/aggregates",
    "fhrp-groups": "ipam/fhrp-groups",
    "ip-addresses": "ipam/ip-addresses",
    "ip-ranges": "ipam/ip-ranges",
    "prefixes": "ipam/prefixes",
    "rirs": "ipam/rirs",
    "roles": "ipam/roles",
    "route-targets": "ipam/route-targets",
    "services": "ipam/services",
    "vlans": "ipam/vlans",
    "vlan-groups": "ipam/vlan-groups",
    "vrfs": "ipam/vrfs",
    # Circuits
    "circuits": "circuits/circuits",
    "circuit-types": "circuits/circuit-types",
    "circuit-terminations": "circuits/circuit-terminations",
    "providers": "circuits/providers",
    "provider-networks": "circuits/provider-networks",
    # Virtualization
    "clusters": "virtualization/clusters",
    "cluster-groups": "virtualization/cluster-groups",
    "cluster-types": "virtualization/cluster-types",
    "virtual-machines": "virtualization/virtual-machines",
    "vm-interfaces": "virtualization/interfaces",
    # Tenancy
    "tenants": "tenancy/tenants",
    "tenant-groups": "tenancy/tenant-groups",
    "contacts": "tenancy/contacts",
    "contact-groups": "tenancy/contact-groups",
    "contact-roles": "tenancy/contact-roles",
    # VPN
    "ike-policies": "vpn/ike-policies",
    "ike-proposals": "vpn/ike-proposals",
    "ipsec-policies": "vpn/ipsec-policies",
    "ipsec-profiles": "vpn/ipsec-profiles",
    "ipsec-proposals": "vpn/ipsec-proposals",
    "l2vpns": "vpn/l2vpns",
    "tunnels": "vpn/tunnels",
    "tunnel-groups": "vpn/tunnel-groups",
    # Wireless
    "wireless-lans": "wireless/wireless-lans",
    "wireless-lan-groups": "wireless/wireless-lan-groups",
    "wireless-links": "wireless/wireless-links"
}


class NetBoxRestClient:
    def __init__(self, url, token):
        self.url = url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Token {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def get(self, endpoint, params=None):
        url = urljoin(self.url, f'api/{endpoint}/')
        if params:
            url += '?' + urlencode(params)
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"NetBox API Error: {e}"}


class AsyncNetBoxAPIClient:
    def __init__(self, client: NetBoxRestClient):
        self.client = client
        logger.info("AsyncNetBoxAPIClient initialized")

    async def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self.client.get, endpoint, params)
            logger.info(f"AsyncNetBoxAPIClient: GET {endpoint} with params: {params} - Success")
            return result
        except Exception as e:
            logger.error(f"AsyncNetBoxAPIClient: GET {endpoint} with params: {params} - Error: {e}")
            return {"error": f"NetBox API Error: {e}"}


async def send_response(response_data: dict) -> None:
    response = json.dumps(response_data) + "\n"
    sys.stdout.write(response)
    sys.stdout.flush()
    logger.info(f"Sent response: {response.strip()}")


def normalize_object_type(input_type: str) -> str:
    """
    Normalize dot notation to the expected NetBox object_type keys.
    Examples:
    - 'dcim.sites' → 'sites'
    - 'ipam.vlans' → 'vlans'
    """
    # Try exact match first
    if input_type in NETBOX_OBJECT_TYPES:
        return input_type

    # Try to extract the last part (e.g., 'sites' from 'dcim.sites')
    suffix = input_type.split(".")[-1]
    for key in NETBOX_OBJECT_TYPES:
        if key.endswith(suffix):
            return key

    return None


async def get_objects(netbox_client: AsyncNetBoxAPIClient, object_type: str, filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get objects from NetBox based on their type and filters.
    Args:
        netbox_client: An instance of AsyncNetBoxAPIClient.
        object_type: String representing the NetBox object type (e.g., "providers", "sites", "vlans").
        filters: dict of filters to apply to the API call.
    """
    normalized_type = normalize_object_type(object_type)
    if not normalized_type:
        valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")

    endpoint = NETBOX_OBJECT_TYPES[normalized_type]
    return await netbox_client.get(endpoint, params=filters or {})


async def search_netbox(netbox_client: AsyncNetBoxAPIClient, query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Perform a global search across NetBox objects.
    Args:
        netbox_client: An instance of AsyncNetBoxAPIClient.
        query: Search string to look for.
        limit: Maximum number of results to return.
    """
    return await netbox_client.get("search", params={"q": query, "limit": limit})


async def get_object_by_id(netbox_client: AsyncNetBoxAPIClient, object_type: str, object_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific NetBox object by its ID.
    Args:
        netbox_client: An instance of AsyncNetBoxAPIClient.
        object_type: String representing the NetBox object type.
        object_id: The numeric ID of the object.
    """
    if object_type not in NETBOX_OBJECT_TYPES:
        valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")
    endpoint = f"{NETBOX_OBJECT_TYPES[object_type]}/{object_id}"
    return await netbox_client.get(endpoint)


async def handle_tools_call(netbox_client: AsyncNetBoxAPIClient, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handles the 'tools/call' method."""
    logger.debug(f"handle_tools_call called with tool_name: {tool_name}, arguments: {arguments}")
    try:
        if tool_name == "get_objects":
            result = await get_objects(netbox_client, object_type=arguments.get("object_type"),
                                      filters=arguments.get("filters", {}))
            logger.debug(f"Result from get_objects: {result}")
            return {"result": result}
        elif tool_name == "search_netbox":
            result = await search_netbox(netbox_client, query=arguments.get("query"),
                                         limit=arguments.get("limit", 10))
            logger.debug(f"Result from search_netbox: {result}")
            return {"result": result}
        elif tool_name == "get_object_by_id":
            result = await get_object_by_id(netbox_client, object_type=arguments.get("object_type"),
                                           object_id=arguments.get("object_id"))
            logger.debug(f"Result from get_object_by_id: {result}")
            return {"result": result}
        else:
            error_msg = "tool not found"
            logger.error(error_msg)
            return {"error": error_msg}
    except Exception as e:
        logger.exception(f"Error calling tool {tool_name}: {e}")
        return {"error": f"Error calling tool {tool_name}: {e}"}


def extract_parameters(func):
    sig = inspect.signature(func)
    params = {}
    for name, param in sig.parameters.items():
        param_type = param.annotation
        if param_type is inspect.Parameter.empty:
            param_type_name = "string"
        elif param_type == int:
            param_type_name = "integer"
        elif param_type == float:
            param_type_name = "number"
        elif param_type == bool:
            param_type_name = "boolean"
        elif param_type == dict:
            param_type_name = "object"
        else:
            param_type_name = "string"
        params[name] = {"type": param_type_name}
    return params


async def handle_tools_discover(netbox_client: AsyncNetBoxAPIClient) -> Dict[str, Any]:
    tools = [
        {
            "name": "get_objects",
            "description": get_objects.__doc__.strip() if get_objects.__doc__ else "",
            "parameters": {
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "The NetBox object type (e.g., 'providers', 'sites', 'vlans').",
                        "example": "providers"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Filters to apply to the API call.",
                        "example": {"name": "My Provider"}
                    }
                }
            }
        },
        {
            "name": "search_netbox",
            "description": search_netbox.__doc__.strip() if search_netbox.__doc__ else "",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search string to look for.",
                        "example": "My Site"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return.",
                        "example": 10
                    }
                }
            }
        },
        {
            "name": "get_object_by_id",
            "description": get_object_by_id.__doc__.strip() if get_object_by_id.__doc__ else "",
            "parameters": {
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "The NetBox object type (e.g., 'providers', 'sites', 'vlans').",
                        "example": "providers"
                    },
                    "object_id": {
                        "type": "integer",
                        "description": "The numeric ID of the object.",
                        "example": 123
                    }
                }
            }
        },
    ]
    return {"result": tools}


async def monitor_stdin(netbox_client: AsyncNetBoxAPIClient) -> None:
    """Monitors stdin for JSON-RPC requests."""
    logger.debug("monitor_stdin thread started")
    loop = asyncio.get_event_loop()
    try:
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            line = line.strip()
            if not line:
                await asyncio.sleep(0.1)
                continue

            logger.debug(f"Read from stdin: {line}")

            try:
                data = json.loads(line)
                logger.debug(f"Parsed JSON: {data}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                await send_response({"error": f"Invalid JSON input: {e}"})
                continue

            if not isinstance(data, dict):
                logger.error(f"Invalid input: {data}. Expected a JSON object.")
                await send_response({"error": "Invalid input: Expected a JSON object."})
                continue

            method = data.get("method")
            params = data.get("params", {})
            logger.debug(f"Method: {method}, Params: {params}")

            if method == "tools/call":
                logger.debug("Handling tools/call")
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                response = await handle_tools_call(netbox_client, tool_name, arguments)
                logger.debug(f"Response from handle_tools_call: {response}")
                await send_response(response)
            elif method == "tools/discover":
                logger.debug("Handling tools/discover")
                response = await handle_tools_discover(netbox_client)
                logger.debug(f"Response from handle_tools_discover: {response}")
                await send_response(response)
            else:
                error_msg = f"Unknown method: {method}"
                logger.warning(error_msg)
                await send_response({"error": error_msg})

        logger.debug("monitor_stdin loop finished")

    except Exception as e:
        logger.exception(f"Exception in monitor_stdin: {e}")
    finally:
        logger.debug("monitor_stdin thread finished")


if __name__ == "__main__":
    logger.info("Starting NetBox MCP server (async)")

    client = NetBoxRestClient(url=NETBOX_URL, token=NETBOX_TOKEN)
    netbox_client = AsyncNetBoxAPIClient(client)

    if "--oneshot" in sys.argv:
        line = sys.stdin.readline().strip()
        try:
            data = json.loads(line)
            method = data.get("method")
            params = data.get("params", {})

            if method == "tools/discover":
                result = asyncio.run(handle_tools_discover(netbox_client))
                asyncio.run(send_response(result))
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = asyncio.run(handle_tools_call(netbox_client, tool_name, arguments))
                asyncio.run(send_response(result))
            else:
                asyncio.run(send_response({"error": f"Unknown method: {method}"}))
        except Exception as e:
            logger.error(f"Error in oneshot mode: {e}")
            asyncio.run(send_response({"error": str(e)}))
        sys.exit(0)
    else:
        asyncio.run(monitor_stdin(netbox_client))