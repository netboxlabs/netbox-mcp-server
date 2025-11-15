package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sort"
	"strings"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

var (
	netboxClient *NetBoxRestClient
	settings     *Settings
)

// Default search types for global search
var defaultSearchTypes = []string{
	"dcim.device",
	"dcim.site",
	"ipam.ipaddress",
	"dcim.interface",
	"dcim.rack",
	"ipam.vlan",
	"circuits.circuit",
	"virtualization.virtualmachine",
}

func main() {
	// Load .env file if it exists
	LoadEnvFile()

	// Initialize settings
	settings = NewSettings()
	settings.LoadFromEnv()
	settings.LoadFromCLI()

	// Validate settings
	if err := settings.Validate(); err != nil {
		log.Fatalf("Configuration error: %v", err)
	}

	// Configure logging
	ConfigureLogging(settings.LogLevel)

	log.Println("Starting NetBox MCP Server")
	configSummary, _ := json.MarshalIndent(settings.GetEffectiveConfigSummary(), "", "  ")
	log.Printf("Effective configuration: %s", configSummary)

	if !settings.VerifySSL {
		log.Println("WARNING: SSL certificate verification is DISABLED. This is insecure and should only be used for testing.")
	}

	// Initialize NetBox client
	netboxClient = NewNetBoxRestClient(settings.NetBoxURL, settings.NetBoxToken, settings.VerifySSL)
	log.Println("NetBox client initialized successfully")

	// Create MCP server
	s := server.NewMCPServer(
		"NetBox",
		"1.0.0",
		server.WithToolCapabilities(true),
	)

	// Register tools
	registerTools(s)

	// Start server based on transport
	if settings.Transport == "stdio" {
		log.Println("Starting stdio transport")
		if err := server.ServeStdio(s); err != nil {
			log.Fatalf("Server error: %v", err)
		}
	} else if settings.Transport == "http" {
		log.Printf("Starting HTTP transport (SSE) on %s:%d", settings.Host, settings.Port)

		// Create SSE server
		sseServer := server.NewSSEServer(s)

		addr := fmt.Sprintf("%s:%d", settings.Host, settings.Port)
		log.Printf("SSE server listening on: http://%s", addr)
		log.Printf("SSE endpoint: http://%s/sse", addr)
		log.Printf("Message endpoint: http://%s/message", addr)

		if err := sseServer.Start(addr); err != nil {
			log.Fatalf("Server error: %v", err)
		}
	}
}

func registerTools(s *server.MCPServer) {
	// Register netbox_get_objects tool
	s.AddTool(mcp.Tool{
		Name:        "netbox_get_objects",
		Description: buildGetObjectsDescription(),
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"object_type": map[string]interface{}{
					"type":        "string",
					"description": "The NetBox object type (e.g., 'dcim.device', 'ipam.ipaddress')",
				},
				"filters": map[string]interface{}{
					"type":        "object",
					"description": "Dictionary of filters to apply",
				},
				"fields": map[string]interface{}{
					"type":        "array",
					"description": "Optional list of specific fields to return",
					"items": map[string]interface{}{
						"type": "string",
					},
				},
				"brief": map[string]interface{}{
					"type":        "boolean",
					"description": "Return minimal representation",
					"default":     false,
				},
				"limit": map[string]interface{}{
					"type":        "integer",
					"description": "Maximum results to return (default 5, max 100)",
					"default":     5,
					"minimum":     1,
					"maximum":     100,
				},
				"offset": map[string]interface{}{
					"type":        "integer",
					"description": "Skip this many results for pagination",
					"default":     0,
					"minimum":     0,
				},
				"ordering": map[string]interface{}{
					"description": "Fields for sort order (string or array of strings)",
				},
			},
			Required: []string{"object_type", "filters"},
		},
	}, handleGetObjects)

	// Register netbox_get_object_by_id tool
	s.AddTool(mcp.Tool{
		Name:        "netbox_get_object_by_id",
		Description: "Get detailed information about a specific NetBox object by its ID",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"object_type": map[string]interface{}{
					"type":        "string",
					"description": "The NetBox object type",
				},
				"object_id": map[string]interface{}{
					"type":        "integer",
					"description": "The numeric ID of the object",
				},
				"fields": map[string]interface{}{
					"type":        "array",
					"description": "Optional list of specific fields to return",
					"items": map[string]interface{}{
						"type": "string",
					},
				},
				"brief": map[string]interface{}{
					"type":        "boolean",
					"description": "Return minimal representation",
					"default":     false,
				},
			},
			Required: []string{"object_type", "object_id"},
		},
	}, handleGetObjectByID)

	// Register netbox_search_objects tool
	s.AddTool(mcp.Tool{
		Name:        "netbox_search_objects",
		Description: "Perform global search across NetBox infrastructure",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"query": map[string]interface{}{
					"type":        "string",
					"description": "Search term (device names, IPs, serial numbers, etc.)",
				},
				"object_types": map[string]interface{}{
					"type":        "array",
					"description": "Limit search to specific types (optional)",
					"items": map[string]interface{}{
						"type": "string",
					},
				},
				"fields": map[string]interface{}{
					"type":        "array",
					"description": "Optional list of specific fields to return",
					"items": map[string]interface{}{
						"type": "string",
					},
				},
				"limit": map[string]interface{}{
					"type":        "integer",
					"description": "Max results per object type (default 5, max 100)",
					"default":     5,
					"minimum":     1,
					"maximum":     100,
				},
			},
			Required: []string{"query"},
		},
	}, handleSearchObjects)

	// Register netbox_get_changelogs tool
	s.AddTool(mcp.Tool{
		Name:        "netbox_get_changelogs",
		Description: "Get object change records (changelogs) from NetBox",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"filters": map[string]interface{}{
					"type":        "object",
					"description": "Dictionary of filters to apply",
				},
			},
			Required: []string{"filters"},
		},
	}, handleGetChangelogs)
}

func buildGetObjectsDescription() string {
	objectTypes := make([]string, 0, len(NetBoxObjectTypes))
	for k := range NetBoxObjectTypes {
		objectTypes = append(objectTypes, k)
	}
	sort.Strings(objectTypes)

	desc := `Get objects from NetBox based on their type and filters.

FILTER RULES:
- Valid: Direct fields like {'site_id': 1, 'name': 'router', 'status': 'active'}
- Valid: Lookups like {'name__ic': 'switch', 'id__in': [1,2,3], 'vid__gte': 100}
- Invalid: Multi-hop like {'device__site_id': 1} - NOT supported

Valid object_type values:
`
	for _, t := range objectTypes {
		desc += fmt.Sprintf("- %s\n", t)
	}

	return desc
}

func handleGetObjects(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		ObjectType string                 `json:"object_type"`
		Filters    map[string]interface{} `json:"filters"`
		Fields     []string               `json:"fields"`
		Brief      bool                   `json:"brief"`
		Limit      int                    `json:"limit"`
		Offset     int                    `json:"offset"`
		Ordering   interface{}            `json:"ordering"`
	}

	if err := json.Unmarshal([]byte(request.Params.Arguments.(string)), &args); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	// Set defaults
	if args.Limit == 0 {
		args.Limit = 5
	}

	// Validate object type
	objType, exists := NetBoxObjectTypes[args.ObjectType]
	if !exists {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid object_type: %s", args.ObjectType)), nil
	}

	// Validate filters
	if err := validateFilters(args.Filters); err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}

	// Build parameters
	params := make(map[string]interface{})
	for k, v := range args.Filters {
		params[k] = v
	}
	params["limit"] = args.Limit
	params["offset"] = args.Offset

	if len(args.Fields) > 0 {
		params["fields"] = strings.Join(args.Fields, ",")
	}

	if args.Brief {
		params["brief"] = "1"
	}

	if args.Ordering != nil {
		switch v := args.Ordering.(type) {
		case string:
			if strings.TrimSpace(v) != "" {
				params["ordering"] = v
			}
		case []interface{}:
			orderFields := make([]string, len(v))
			for i, field := range v {
				orderFields[i] = fmt.Sprintf("%v", field)
			}
			params["ordering"] = strings.Join(orderFields, ",")
		}
	}

	// Make API call
	result, err := netboxClient.Get(objType.Endpoint, params)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("API error: %v", err)), nil
	}

	resultJSON, _ := json.Marshal(result)
	return mcp.NewToolResultText(string(resultJSON)), nil
}

func handleGetObjectByID(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		ObjectType string   `json:"object_type"`
		ObjectID   int      `json:"object_id"`
		Fields     []string `json:"fields"`
		Brief      bool     `json:"brief"`
	}

	if err := json.Unmarshal([]byte(request.Params.Arguments.(string)), &args); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	// Validate object type
	objType, exists := NetBoxObjectTypes[args.ObjectType]
	if !exists {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid object_type: %s", args.ObjectType)), nil
	}

	// Build parameters
	params := make(map[string]interface{})
	if len(args.Fields) > 0 {
		params["fields"] = strings.Join(args.Fields, ",")
	}
	if args.Brief {
		params["brief"] = "1"
	}

	// Make API call
	result, err := netboxClient.GetByID(objType.Endpoint, args.ObjectID, params)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("API error: %v", err)), nil
	}

	resultJSON, _ := json.Marshal(result)
	return mcp.NewToolResultText(string(resultJSON)), nil
}

func handleSearchObjects(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		Query       string   `json:"query"`
		ObjectTypes []string `json:"object_types"`
		Fields      []string `json:"fields"`
		Limit       int      `json:"limit"`
	}

	if err := json.Unmarshal([]byte(request.Params.Arguments.(string)), &args); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	// Set defaults
	if args.Limit == 0 {
		args.Limit = 5
	}
	searchTypes := args.ObjectTypes
	if len(searchTypes) == 0 {
		searchTypes = defaultSearchTypes
	}

	// Validate object types
	for _, objType := range searchTypes {
		if _, exists := NetBoxObjectTypes[objType]; !exists {
			return mcp.NewToolResultError(fmt.Sprintf("Invalid object_type: %s", objType)), nil
		}
	}

	// Build results
	results := make(map[string]interface{})
	for _, objType := range searchTypes {
		params := map[string]interface{}{
			"q":     args.Query,
			"limit": args.Limit,
		}
		if len(args.Fields) > 0 {
			params["fields"] = strings.Join(args.Fields, ",")
		}

		result, err := netboxClient.Get(NetBoxObjectTypes[objType].Endpoint, params)
		if err != nil {
			results[objType] = []interface{}{}
			continue
		}

		// Extract results array from paginated response
		if resultMap, ok := result.(map[string]interface{}); ok {
			if resultArray, ok := resultMap["results"].([]interface{}); ok {
				results[objType] = resultArray
			} else {
				results[objType] = []interface{}{}
			}
		} else {
			results[objType] = []interface{}{}
		}
	}

	resultJSON, _ := json.Marshal(results)
	return mcp.NewToolResultText(string(resultJSON)), nil
}

func handleGetChangelogs(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		Filters map[string]interface{} `json:"filters"`
	}

	if err := json.Unmarshal([]byte(request.Params.Arguments.(string)), &args); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	// Make API call
	result, err := netboxClient.Get("core/object-changes", args.Filters)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("API error: %v", err)), nil
	}

	resultJSON, _ := json.Marshal(result)
	return mcp.NewToolResultText(string(resultJSON)), nil
}

func validateFilters(filters map[string]interface{}) error {
	validSuffixes := map[string]bool{
		"n": true, "ic": true, "nic": true, "isw": true, "nisw": true,
		"iew": true, "niew": true, "ie": true, "nie": true, "empty": true,
		"regex": true, "iregex": true, "lt": true, "lte": true, "gt": true,
		"gte": true, "in": true,
	}

	for filterName := range filters {
		// Skip special parameters
		if filterName == "limit" || filterName == "offset" || filterName == "fields" || filterName == "q" {
			continue
		}

		if !strings.Contains(filterName, "__") {
			continue
		}

		parts := strings.Split(filterName, "__")

		// Allow field__suffix pattern
		if len(parts) == 2 && validSuffixes[parts[1]] {
			continue
		}

		// Block multi-hop patterns and invalid suffixes
		if len(parts) >= 2 {
			return fmt.Errorf("invalid filter '%s': Multi-hop relationship traversal or invalid lookup suffix not supported", filterName)
		}
	}

	return nil
}
