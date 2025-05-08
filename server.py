from mcp.server.fastmcp import FastMCP
from netbox_client import NetBoxRestClient
import os
import requests # Added
from typing import List, Dict, Any, Tuple, Optional # Added
import logging # Added

# --- NetBox MCP Server Tool Notes ---
#
# Understanding the 'brief' parameter for `netbox_get_objects`:
#
# The `netbox_get_objects` tool supports an optional `brief: bool` parameter,
# defaulting to `True`. This enables an intelligent, context-aware brief mode.
#
# - `brief=True` (Default - Intelligent Brief Mode):
#   When `brief` is True, the tool attempts to resolve common user-friendly
#   filter names (e.g., `site_ref="HQ"`, `tenant_ref="CustomerA"`) into the
#   actual IDs required by the NetBox API. It then queries NetBox using these
#   resolved IDs.
#   The returned "brief" data for each object will include:
#     1. Essential identifiers: `id`, `display`, and `name` (if available).
#     2. Context from resolved filters: The original user-friendly filter and
#        its value (e.g., `site_ref: "HQ"`) will be part of each brief object.
#     3. Values for pass-through filters: If the original query included direct
#        API filters (e.g., `status: "active"`), and the fetched object contains
#        this field, its value (or label for choice fields) will be included.
#     4. For `object_type="devices"`, it will also include `manufacturer_name`,
#        `model_name`, `serial_number` (if available), and `site_name` if these
#        fields are present on the device object.
#   This mode aims to return the least amount of data necessary to answer the
#   query contextually. Refer to `RESOLVABLE_FIELD_MAP` for configurable
#   filter resolution details.
#
# - `brief=False` (Detailed Mode):
#   Pass `brief=False` explicitly if you require the complete, detailed
#   representation of objects, including all fields returned by the NetBox API.
#   In this mode, filter resolution via `RESOLVABLE_FIELD_MAP` still occurs
#   to ensure the correct objects are fetched, but the full objects are returned.
#
# Filter Resolution Errors:
#   If a user-friendly filter cannot be resolved (e.g., name not found and
#   `on_no_result: "error"` is set), or if a lookup causes a critical API error,
#   the tool will raise a ValueError.
#
# `netbox_get_changelogs`:
#   This tool also has a `brief: bool = True` parameter, but it uses a simpler
#   field-stripping mechanism for its brief mode (see its docstring).
#
# `netbox_get_object_by_id`:
#   This tool does NOT use the `brief` parameter and always returns full details.
# ---

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
    "roles": "ipam/roles", # IPAM roles
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
    "vm-interfaces": "virtualization/interfaces", # Note: NetBox API endpoint is virtualization/interfaces
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
    "wireless-links": "wireless/wireless-links",
    # Extras
    "config-contexts": "extras/config-contexts",
    "custom-fields": "extras/custom-fields",
    "export-templates": "extras/export-templates",
    "image-attachments": "extras/image-attachments",
    "jobs": "extras/jobs",
    "saved-filters": "extras/saved-filters",
    "scripts": "extras/scripts",
    "tags": "extras/tags",
    "webhooks": "extras/webhooks",
}

mcp = FastMCP("NetBox", log_level="DEBUG")
netbox: Optional[NetBoxRestClient] = None # Added type hint

# --- Intelligent Filter Resolution Infrastructure ---

class FilterResolutionError(Exception):
    """Custom exception for errors during filter resolution."""
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

RESOLVABLE_FIELD_MAP: Dict[str, Dict[str, Dict[str, Any]]] = {
    "devices": {
        "site_ref": {
            "target_nb_type": "sites",
            "lookup_fields": ["name", "slug"],
            "api_filter_key": "site_id",
            "on_no_result": "error",
            "on_multiple_results": "error"
        },
        "tenant_ref": {
            "target_nb_type": "tenants",
            "lookup_fields": ["name", "slug"],
            "api_filter_key": "tenant_id",
            "on_no_result": "allow_empty",
            "on_multiple_results": "error"
        },
        "manufacturer_name": { # Assumes direct lookup on 'name'
            "target_nb_type": "manufacturers",
            "lookup_fields": ["name"],
            "api_filter_key": "manufacturer_id",
            "on_no_result": "error",
            "on_multiple_results": "error"
        },
        "device_role_name": {
             "target_nb_type": "device-roles",
             "lookup_fields": ["name", "slug"],
             "api_filter_key": "role_id", # Note: API filter key for device role is 'role_id' or 'role'
             "on_no_result": "error",
             "on_multiple_results": "error"
        },
        "platform_name": {
            "target_nb_type": "platforms",
            "lookup_fields": ["name", "slug"],
            "api_filter_key": "platform_id",
            "on_no_result": "error",
            "on_multiple_results": "error"
        }
    },
    "ip-addresses": {
        "vrf_ref": {
            "target_nb_type": "vrfs",
            "lookup_fields": ["name", "rd"],
            "api_filter_key": "vrf_id",
            "on_no_result": "error",
            "on_multiple_results": "error"
        },
        "tenant_ref": {
            "target_nb_type": "tenants",
            "lookup_fields": ["name", "slug"],
            "api_filter_key": "tenant_id",
            "on_no_result": "allow_empty",
            "on_multiple_results": "error"
        },
    },
    "vlans": {
        "site_ref": {
            "target_nb_type": "sites",
            "lookup_fields": ["name", "slug"],
            "api_filter_key": "site_id",
            "on_no_result": "error",
            "on_multiple_results": "error"
        },
        "tenant_ref": {
            "target_nb_type": "tenants",
            "lookup_fields": ["name", "slug"],
            "api_filter_key": "tenant_id",
            "on_no_result": "allow_empty",
            "on_multiple_results": "error"
        },
        "vlan_group_ref": {
            "target_nb_type": "vlan-groups",
            "lookup_fields": ["name", "slug"],
            "api_filter_key": "group_id",
            "on_no_result": "error",
            "on_multiple_results": "error"
        }
    }
    # Add more object_types and their resolvable fields as needed
}

def _fetch_ids_for_lookup(target_nb_type: str, lookup_field: str, lookup_value: Any) -> List[int]:
    """
    Fetches IDs from NetBox for a given type, field, and value.
    Returns a list of unique IDs.
    Raises FilterResolutionError for critical (non-404) API errors.
    Returns empty list on 404 (not found for this specific lookup).
    """
    if netbox is None:
        raise RuntimeError("NetBox client is not initialized.")

    ids = set()
    endpoint = NETBOX_OBJECT_TYPES.get(target_nb_type)
    if not endpoint:
        # This is an internal configuration error if target_nb_type is invalid
        logging.getLogger("NetBox").error(f"Invalid target_nb_type '{target_nb_type}' in RESOLVABLE_FIELD_MAP.")
        return []

    params = {lookup_field: lookup_value}
    try:
        results = netbox.get(endpoint, params=params)
        
        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict) and 'id' in item:
                    ids.add(item['id'])
        # NetBox usually returns a list for filtered queries.
        # If it's a single dict (e.g. if lookup_value was an ID and lookup_field was 'id'), handle it.
        elif isinstance(results, dict) and 'id' in results:
             ids.add(results['id'])

    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return []  # 404 means "not found for this specific lookup"
        else:
            # Other HTTP errors (400, 401, 403, 5xx) are critical for this lookup
            raise FilterResolutionError(
                f"API HTTP error during lookup for '{target_nb_type}' with '{lookup_field}={lookup_value}': {str(e)}",
                original_exception=e
            )
    except requests.exceptions.RequestException as e:
        # Network errors, timeouts etc., are critical
        raise FilterResolutionError(
            f"Network error during lookup for '{target_nb_type}' with '{lookup_field}={lookup_value}': {str(e)}",
            original_exception=e
        )
    return list(ids)

def _resolve_and_prepare_filters(object_type: str, user_filters: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Resolves user-friendly filter keys to API-compatible filter keys and values.
    Returns a tuple: (api_filters, resolved_context_filters).
    Raises ValueError or FilterResolutionError on critical resolution failures.
    """
    api_filters: Dict[str, Any] = {}
    resolved_context_filters: Dict[str, Any] = {} # Stores original user KVs that were resolved
    
    # Get the resolution map for the current primary object_type
    resolution_config_for_type = RESOLVABLE_FIELD_MAP.get(object_type, {})

    for user_key, user_value in user_filters.items():
        if user_key in resolution_config_for_type:
            config = resolution_config_for_type[user_key]
            target_nb_type = config["target_nb_type"]
            lookup_fields: List[str] = config["lookup_fields"]
            api_filter_key = config["api_filter_key"]
            on_no_result = config.get("on_no_result", "error") # Default to error
            on_multiple_results = config.get("on_multiple_results", "error") # Default to error

            all_found_ids = set()
            try:
                for field_to_try in lookup_fields:
                    ids_from_lookup = _fetch_ids_for_lookup(target_nb_type, field_to_try, user_value)
                    all_found_ids.update(ids_from_lookup)
                    # Optimization: if we only need one and found it, and policy isn't 'use_all', could break.
                    # For now, collect all to correctly handle on_multiple_results across all lookup_fields.
            except FilterResolutionError as fre:
                # Critical error during one of the lookups, fail entire operation
                raise ValueError(f"Critical error resolving filter '{user_key}=\"{user_value}\"': {str(fre)}") from fre

            final_ids_list = list(all_found_ids)

            if not final_ids_list:
                if on_no_result == "error":
                    fields_tried_str = ", ".join(lookup_fields)
                    raise ValueError(
                        f"No matching '{target_nb_type}' found for filter '{user_key}=\"{user_value}\"' (tried fields: {fields_tried_str})."
                    )
                elif on_no_result == "allow_empty":
                    # Don't add to api_filters, or add a non-matching placeholder if API requires it
                    # For now, we simply don't add the filter if it's allowed to be empty and resolved to nothing.
                    resolved_context_filters[user_key] = user_value # Still note it in context
            else: # IDs were found
                if len(final_ids_list) > 1 and on_multiple_results == "error":
                    raise ValueError(
                        f"Multiple ({len(final_ids_list)}) matching '{target_nb_type}' found for filter '{user_key}=\"{user_value}\"'. Please be more specific or use an ID."
                    )
                
                # Successfully resolved
                if on_multiple_results == "use_all":
                    api_filters[api_filter_key] = final_ids_list
                else: # "use_first" or implicitly single result from "error" policy
                    api_filters[api_filter_key] = final_ids_list[0]
                resolved_context_filters[user_key] = user_value
        else:
            # Not a resolvable key, pass it through directly
            api_filters[user_key] = user_value
            # Also add to resolved_context so it can be part of brief output if field exists on object
            resolved_context_filters[user_key] = user_value 


    return api_filters, resolved_context_filters

# --- MCP Tools ---

@mcp.tool()
def netbox_get_objects(object_type: str, filters: Dict[str, Any], brief: bool = True):
    """
    Retrieves a list of objects (e.g., devices, IP addresses) from a NetBox instance.

    This tool features an intelligent filter resolution system. User-friendly filter
    references (like `site_ref="HQ"`) are automatically resolved to the
    appropriate NetBox API filter parameters (e.g., `site_id=123`). Refer to the
    `RESOLVABLE_FIELD_MAP` definition in the server code for details on which
    fields support this resolution for different object types.

    It also supports a dynamic "brief" mode to control the level of detail in the
    returned objects.

    Args:
        object_type: The type of NetBox object to query (e.g., "devices",
                     "ip-addresses", "sites"). A comprehensive list of supported
                     types can be found in the `NETBOX_OBJECT_TYPES` mapping
                     within the server code.
        filters: A dictionary of filters to apply to the query.
                 - For resolvable fields (see `RESOLVABLE_FIELD_MAP`), provide
                   user-friendly values (e.g., `{"site_ref": "Main Office"}`).
                 - For other fields, provide direct NetBox API filter keys and
                   values (e.g., `{"status": "active"}`).
        brief: A boolean flag to control the output verbosity (default: `True`).
               It is generally recommended to use `brief=True` as it is designed
               to provide the most commonly needed information efficiently.
               Only set `brief=False` if, after an initial query, specific
               information is confirmed to be missing from the brief output.
               - If `True` (default):
                 Returns a summarized version of each object.
                 - For `object_type="devices"`, this includes: `id`, `display`,
                   `name` (if available), `manufacturer_name`, `model_name`,
                   `serial_number` (if available), `site_name`, and any
                   context derived from the resolved or passthrough filters.
                 - For other object types, this generally includes: `id`,
                   `display`, `name` (if available), and context from filters.
               - If `False`:
                 Returns the full, detailed object representation as provided
                 by the NetBox API. Filter resolution still occurs to ensure
                 the correct objects are fetched.
    Returns:
        A list of NetBox objects matching the query, or a single object if
        the query uniquely identifies one. The structure of the returned
        objects depends on the `brief` parameter.
    Raises:
        RuntimeError: If the NetBox client is not initialized.
        ValueError: If an invalid `object_type` is provided, or if filter
                    resolution fails (e.g., name not found, multiple matches
                    when one is expected).
    """
    if netbox is None:
        raise RuntimeError("NetBox client is not initialized.")
    if object_type not in NETBOX_OBJECT_TYPES:
        valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")

    endpoint = NETBOX_OBJECT_TYPES[object_type]
    
    # Resolve filters first, regardless of brief mode, to ensure correct objects are fetched
    api_filters, context_filters = _resolve_and_prepare_filters(object_type, filters if filters else {})
    
    full_results = netbox.get(endpoint, params=api_filters)

    if not brief:
        return full_results # Return full data if not in brief mode

    # Process for brief mode
    if not isinstance(full_results, list):
        # Should typically be a list for /<objects>/ endpoint.
        # If it's a single dict (e.g. if api_filters led to a direct ID match implicitly)
        # we can still process it.
        if isinstance(full_results, dict):
            items_to_process = [full_results]
        else: # Not a list or dict, return as is.
            return full_results
    else:
        items_to_process = full_results

    brief_results = []
    for item in items_to_process:
        if not isinstance(item, dict): # Skip if an item in the list is not a dict
            brief_results.append(item) # Or handle as an error
            continue

        brief_item: Dict[str, Any] = {
            'id': item.get('id'),
            'display': item.get('display'),
        }
        if 'name' in item:
            brief_item['name'] = item.get('name')
        
        # Add device-specific fields if object_type is "devices"
        if object_type == "devices":
            device_type_data = item.get('device_type')
            if device_type_data and isinstance(device_type_data, dict):
                # Manufacturer is nested under device_type
                manufacturer_data = device_type_data.get('manufacturer')
                if manufacturer_data and isinstance(manufacturer_data, dict):
                    brief_item['manufacturer_name'] = manufacturer_data.get('name')
                
                model_name = device_type_data.get('model')
                brief_item['model_name'] = model_name
                if model_name: # Infer OS from model_name
                    model_upper = model_name.upper()
                    if "NEXUS" in model_upper or \
                       "N9K" in model_upper or \
                       "N7K" in model_upper or \
                       "N5K" in model_upper or \
                       "N3K" in model_upper or \
                       "N2K" in model_upper or \
                       "MDS" in model_upper: # MDS also runs NX-OS
                        brief_item['os_type'] = "NX-OS"
                    elif "CATALYST" in model_upper or \
                         "ISR" in model_name.upper() or \
                         "ASR" in model_name.upper():
                        brief_item['os_type'] = "IOS"
                    # Add more rules as needed, or a fallback

            if item.get('serial'): # Only add if serial has a value
                brief_item['serial_number'] = item.get('serial')
            if item.get('site') and isinstance(item.get('site'), dict):
                brief_item['site_name'] = item.get('site', {}).get('name')

        # Add context from resolved and passthrough filters
        for ctx_key, ctx_value in context_filters.items():
            # If the context key corresponds to a resolved filter (e.g. "site_ref"), add it directly
            if ctx_key in RESOLVABLE_FIELD_MAP.get(object_type, {}) or ctx_key not in item:
                 brief_item[ctx_key] = ctx_value
            else:
                # If it's a passthrough filter key that also exists as a field on the item,
                # prefer the item's actual value/label for that field.
                field_data = item.get(ctx_key)
                if isinstance(field_data, dict) and 'label' in field_data:
                    brief_item[ctx_key] = field_data['label'] # For choice fields
                elif field_data is not None:
                    brief_item[ctx_key] = field_data
                else: # Fallback to the context value if field_data is None
                    brief_item[ctx_key] = ctx_value


        brief_results.append(brief_item)
    
    # If the original full_results was a single dict, return a single brief_item
    if isinstance(full_results, dict) and len(brief_results) == 1:
        return brief_results[0]
        
    return brief_results

@mcp.tool()
def netbox_get_object_by_id(object_type: str, object_id: int):
    """
    Get detailed information about a specific NetBox object by its ID.
    This tool does NOT use the `brief` parameter.
    Args:
        object_type: String representing the NetBox object type (e.g. "devices", "ip-addresses")
        object_id: The numeric ID of the object
    Returns:
        Complete object details
    """
    if netbox is None:
        raise RuntimeError("NetBox client is not initialized.")
    if object_type not in NETBOX_OBJECT_TYPES:
        valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")
        
    endpoint = f"{NETBOX_OBJECT_TYPES[object_type]}/{object_id}/" # Ensure trailing slash for consistency
    
    return netbox.get(endpoint)

@mcp.tool()
def netbox_get_changelogs(filters: Dict[str, Any], brief: bool = True):
    """
    Get object change records (changelogs) from NetBox based on filters.
    Brief mode for changelogs uses simple field stripping.
    Args:
        filters: dict of filters to apply to the API call.
        brief: If False, returns full changelog details. (Default: True, for summarized version).
    Returns:
        List of changelog objects.
    """
    if netbox is None:
        raise RuntimeError("NetBox client is not initialized.")
    endpoint = "extras/object-changes/" # Corrected endpoint

    query_params = filters.copy() if filters else {}
    full_results = netbox.get(endpoint, params=query_params)

    if not brief:
        return full_results

    if not isinstance(full_results, list):
         return full_results # Should be a list

    brief_results = []
    changelog_brief_fields = [
        'id', 'time', 'user_name', 'action', 
        'changed_object_type', 'changed_object_id', 'object_repr', 'request_id'
    ]
    for item in full_results:
        if isinstance(item, dict):
            brief_item = {key: item.get(key) for key in changelog_brief_fields if item.get(key) is not None}
            brief_results.append(brief_item)
        else:
            brief_results.append(item) # Append non-dict items as is
            
    return brief_results

if __name__ == "__main__":
    netbox_url = os.getenv("NETBOX_URL")
    netbox_token = os.getenv("NETBOX_TOKEN")
    
    if not netbox_url or not netbox_token:
        raise ValueError("NETBOX_URL and NETBOX_TOKEN environment variables must be set")
    
    # Initialize NetBox client
    # Consider making verify_ssl configurable, e.g., via an env var
    verify_ssl_env = os.getenv("NETBOX_VERIFY_SSL", "false").lower()
    verify_ssl_val = verify_ssl_env == "true"
    netbox = NetBoxRestClient(url=netbox_url, token=netbox_token, verify_ssl=verify_ssl_val)
    
    logging.getLogger("NetBox").info(f"NetBox MCP Server initialized. URL: {netbox_url}, SSL Verification: {verify_ssl_val}")
    mcp.run(transport="stdio")
