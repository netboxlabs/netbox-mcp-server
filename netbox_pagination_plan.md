# Plan to Implement Pagination Handling in NetBox Client

This document outlines the plan to update the `get` method in the `NetBoxRestClient` to fully support API pagination.

## Current State

The current `get` method in [`netbox_client.py`](netbox_client.py) has a basic check for paginated results:

```python
# In NetBoxRestClient.get()
# ...
        data = response.json()
        if id is None and 'results' in data:
            # Handle paginated results
            return data['results']
# ...
```

This extracts results from the *first page* only.

## Proposed Changes

1.  **Modify the `get` method in `NetBoxRestClient` (currently at line [`netbox_client.py:181`](netbox_client.py:181)):**
    *   After the initial API request, check if `id` is `None` (indicating a list endpoint was called) and if the response JSON (`data`) contains a `next` key with a non-null value. This `next` key holds the URL for the subsequent page of results.
    *   If a `next` URL exists:
        *   Initialize an empty list, `all_results`, and add the `results` from the current page (`data['results']`) to this list.
        *   Store the `next` URL (e.g., `current_url = data['next']`).
        *   Enter a `while` loop that continues as long as `current_url` is not `None`.
        *   Inside the loop:
            *   Make a GET request to `current_url`.
            *   Update `data` with the JSON response from this new request.
            *   Append the `results` from this new page (`data['results']`) to the `all_results` list.
            *   Update `current_url` with the new `data['next']` value (which could be another URL or `None`).
    *   Once the loop finishes (i.e., `current_url` is `None`), all pages have been fetched. Return the `all_results` list.
    *   If the initial response is not paginated (e.g., `id` is provided, or the `next` key is not present or is `None` in the initial response), the existing logic to return `data` (for a single object) or `data['results']` (for a single page of a non-paginated list) should be maintained.

## Mermaid Diagram of the `get` method logic:

```mermaid
graph TD
    A[Start get(endpoint, id, params)] --> B{id is None?};
    B -- Yes --> C{Initial API Call};
    B -- No --> D[API Call for single object];
    D --> E[Parse response.json() as data];
    E --> F[Return data];
    C --> G{Parse response.json() as data};
    G --> H{data has 'next' URL and 'results'?};
    H -- No --> I[Return data['results'] (if 'results' exists, else data)];
    H -- Yes --> J[Initialize all_results = data['results']];
    J --> K[current_url = data['next']];
    K --> L{current_url is not None?};
    L -- Yes --> M[Fetch data from current_url];
    M --> N{Parse new_response.json() as data_page};
    N --> O[Append data_page['results'] to all_results];
    O --> P[current_url = data_page['next']];
    P --> L;
    L -- No --> Q[Return all_results];
```

## Decisions Made

*   **Rate Limiting:** No explicit delay will be added between fetching pages for now. This can be revisited if rate-limiting issues arise.
*   **Scope:** The focus will be solely on the `get` method. Pagination for responses of bulk operations (`bulk_create`, `bulk_update`, `bulk_delete`) will not be investigated at this time.