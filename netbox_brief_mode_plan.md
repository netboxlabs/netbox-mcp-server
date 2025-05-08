# Plan: Enhance NetBox MCP Server Brief Device Queries

**Goal:** Modify the NetBox MCP server to include `manufacturer`, `model`, `serial number`, and `site` in the "brief" output for device queries, and update in-code documentation to reflect this change for clarity, especially for LLM consumers.

**Affected File:** `server.py`

## Revised Plan Details:

1.  **Target Function & Comments:**
    *   Code modifications will be made within the `netbox_get_objects` function in `server.py`.
    *   Documentation (comment) modifications will be at the top of `server.py` (around lines 8-35, specifically updating the description of `brief=True` behavior).

2.  **Locate Brief Mode Logic (Code):**
    *   Inside the `netbox_get_objects` function, the focus will be on the section that processes results when `brief=True`. This is typically within a loop iterating through fetched items, after an initial `brief_item` dictionary is created.

3.  **Device-Specific Enhancement (Code Change):**
    *   A conditional check will be added: `if object_type == "devices" and isinstance(item, dict):`.
    *   Inside this condition, the following fields will be extracted from the full `item` and added to the `brief_item` dictionary:
        *   **Manufacturer Name:** `brief_item['manufacturer_name'] = item.get('manufacturer', {}).get('name')`
        *   **Model Name:** `brief_item['model_name'] = item.get('device_type', {}).get('model')`
        *   **Serial Number:** `brief_item['serial_number'] = item.get('serial')` (only if it has a value).
        *   **Site Name:** `brief_item['site_name'] = item.get('site', {}).get('name')`

4.  **Graceful Handling (Code):**
    *   The use of `.get('key', {}).get('nested_key')` for nested objects and checking `item.get('serial')` will ensure that if any of these fields or their parent objects are missing for a particular device, the process will not error out. Instead, the field will be omitted from the brief output for that specific device.

5.  **Update Documentation (Comment Change):**
    *   The comment block at the beginning of `server.py` (describing `netbox_get_objects` and the `brief` parameter, typically around lines 8-35) will be updated.
    *   The description of what `brief=True` returns (currently detailed around lines 20-27) will be amended.
    *   It will be clearly stated that **for `object_type="devices"`**, the brief output will now *also* include `manufacturer_name`, `model_name`, `serial_number`, and `site_name` when these fields are available on the device object. This provides explicit guidance for users and LLMs.

6.  **No Impact on Existing Filters:**
    *   These changes are focused on the *display* of information in brief mode and its documentation. They will not affect the existing filter resolution logic (e.g., `RESOLVABLE_FIELD_MAP`) or how `context_filters` are added to the `brief_item`. The new keys (`manufacturer_name`, `model_name`, `serial_number`, `site_name`) are chosen to be descriptive and avoid clashes with existing filter keys.

## Visual Plan (Mermaid Diagram):

```mermaid
graph TD
    A[Start: User requests enhanced brief device output & LLM guidance] --> B{Analyze `server.py`};
    B --> C[Identify `netbox_get_objects` function & its documentation comments];
    C --> D[Locate 'brief' mode processing loop in function];
    D --> E{Is `object_type == "devices"`?};
    E -- Yes --> F[Extract Manufacturer Name];
    F --> G[Add `manufacturer_name` to `brief_item`];
    G --> H[Extract Model Name from `device_type`];
    H --> I[Add `model_name` to `brief_item`];
    I --> J[Extract Serial Number];
    J --> K[Add `serial_number` to `brief_item` (if exists)];
    K --> L[Extract Site Name];
    L --> M[Add `site_name` to `brief_item`];
    M --> N[Continue with existing filter context logic];
    E -- No --> N;
    N --> O[Modify `server.py` comments (lines 8-35)];
    O -- Add details about new device fields in brief mode --> P;
    P[Return `brief_results`];
    P --> Q[End: Brief device queries include new fields & docs updated];