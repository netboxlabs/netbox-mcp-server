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
	LoadEnvFile()

	settings = NewSettings()
	settings.LoadFromEnv()
	settings.LoadFromCLI()

	if err := settings.Validate(); err != nil {
		log.Fatalf("Configuration error: %v", err)
	}

	ConfigureLogging(settings.LogLevel)

	log.Println("Starting NetBox MCP Server")
	configSummary, _ := json.MarshalIndent(settings.GetEffectiveConfigSummary(), "", "  ")
	log.Printf("Effective configuration: %s", configSummary)

	if !settings.VerifySSL {
		log.Println("WARNING: SSL certificate verification is DISABLED. This is insecure and should only be used for testing.")
	}

	netboxClient = NewNetBoxRestClient(settings.NetBoxURL, settings.NetBoxToken, settings.VerifySSL)
	log.Println("NetBox client initialized successfully")

	s := server.NewMCPServer(
		"NetBox",
		"1.0.0",
		server.WithToolCapabilities(true),
	)

	registerTools(s)

	if settings.Transport == "stdio" {
		log.Println("Starting stdio transport")
		if err := server.ServeStdio(s); err != nil {
			log.Fatalf("Server error: %v", err)
		}
	} else if settings.Transport == "http" {
		log.Printf("Starting HTTP transport (Streamable HTTP) on %s:%d", settings.Host, settings.Port)

		httpServer := server.NewStreamableHTTPServer(s)

		addr := fmt.Sprintf("%s:%d", settings.Host, settings.Port)
		log.Printf("Streamable HTTP server listening on: http://%s", addr)
		log.Printf("MCP endpoint: http://%s/mcp", addr)
		log.Printf("Use this URL in your MCP client: http://%s/mcp", addr)

		if err := httpServer.Start(addr); err != nil {
			log.Fatalf("Server error: %v", err)
		}
	}
}

func registerTools(s *server.MCPServer) {
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

	s.AddTool(mcp.Tool{
		Name:        "netbox_create_object",
		Description: "Create a new object in NetBox",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"object_type": map[string]interface{}{
					"type":        "string",
					"description": "The NetBox object type (e.g., 'dcim.device', 'ipam.ipaddress')",
				},
				"data": map[string]interface{}{
					"type":        "object",
					"description": "Object data to create (must include all required fields for the object type)",
				},
			},
			Required: []string{"object_type", "data"},
		},
	}, handleCreateObject)

	s.AddTool(mcp.Tool{
		Name:        "netbox_update_object",
		Description: "Update an existing object in NetBox",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"object_type": map[string]interface{}{
					"type":        "string",
					"description": "The NetBox object type (e.g., 'dcim.device', 'ipam.ipaddress')",
				},
				"object_id": map[string]interface{}{
					"type":        "integer",
					"description": "The numeric ID of the object to update",
				},
				"data": map[string]interface{}{
					"type":        "object",
					"description": "Object data to update (only include fields to be changed)",
				},
			},
			Required: []string{"object_type", "object_id", "data"},
		},
	}, handleUpdateObject)

	s.AddTool(mcp.Tool{
		Name:        "netbox_delete_object",
		Description: "Delete an object from NetBox",
		InputSchema: mcp.ToolInputSchema{
			Type: "object",
			Properties: map[string]interface{}{
				"object_type": map[string]interface{}{
					"type":        "string",
					"description": "The NetBox object type (e.g., 'dcim.device', 'ipam.ipaddress')",
				},
				"object_id": map[string]interface{}{
					"type":        "integer",
					"description": "The numeric ID of the object to delete",
				},
			},
			Required: []string{"object_type", "object_id"},
		},
	}, handleDeleteObject)
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

func decodeArguments(args interface{}, target interface{}) error {
	switch v := args.(type) {
	case string:
		return json.Unmarshal([]byte(v), target)
	case map[string]interface{}:
		data, err := json.Marshal(v)
		if err != nil {
			return err
		}
		return json.Unmarshal(data, target)
	default:
		data, err := json.Marshal(v)
		if err != nil {
			return fmt.Errorf("unsupported arguments type: %T", v)
		}
		return json.Unmarshal(data, target)
	}
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

	if err := decodeArguments(request.Params.Arguments, &args); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	if args.Limit == 0 {
		args.Limit = 5
	}

	log.Printf("MCP Tool Call: netbox_get_objects - object_type=%s, filters=%v, limit=%d", args.ObjectType, args.Filters, args.Limit)

	objType, exists := NetBoxObjectTypes[args.ObjectType]
	if !exists {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid object_type: %s", args.ObjectType)), nil
	}

	if err := validateFilters(args.Filters); err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}

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

	if err := decodeArguments(request.Params.Arguments, &args); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	log.Printf("MCP Tool Call: netbox_get_object_by_id - object_type=%s, object_id=%d", args.ObjectType, args.ObjectID)

	objType, exists := NetBoxObjectTypes[args.ObjectType]
	if !exists {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid object_type: %s", args.ObjectType)), nil
	}

	params := make(map[string]interface{})
	if len(args.Fields) > 0 {
		params["fields"] = strings.Join(args.Fields, ",")
	}
	if args.Brief {
		params["brief"] = "1"
	}

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

	if err := decodeArguments(request.Params.Arguments, &args); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	if args.Limit == 0 {
		args.Limit = 5
	}
	searchTypes := args.ObjectTypes
	if len(searchTypes) == 0 {
		searchTypes = defaultSearchTypes
	}

	log.Printf("MCP Tool Call: netbox_search_objects - query=%s, object_types=%v, limit=%d", args.Query, searchTypes, args.Limit)

	for _, objType := range searchTypes {
		if _, exists := NetBoxObjectTypes[objType]; !exists {
			return mcp.NewToolResultError(fmt.Sprintf("Invalid object_type: %s", objType)), nil
		}
	}

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

	if err := decodeArguments(request.Params.Arguments, &args); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	log.Printf("MCP Tool Call: netbox_get_changelogs - filters=%v", args.Filters)

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
		if filterName == "limit" || filterName == "offset" || filterName == "fields" || filterName == "q" {
			continue
		}

		if !strings.Contains(filterName, "__") {
			continue
		}

		parts := strings.Split(filterName, "__")

		if len(parts) == 2 && validSuffixes[parts[1]] {
			continue
		}

		if len(parts) >= 2 {
			return fmt.Errorf("invalid filter '%s': Multi-hop relationship traversal or invalid lookup suffix not supported", filterName)
		}
	}

	return nil
}

func handleCreateObject(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		ObjectType string                 `json:"object_type"`
		Data       map[string]interface{} `json:"data"`
	}

	if err := decodeArguments(request.Params.Arguments, &args); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	log.Printf("MCP Tool Call: netbox_create_object - object_type=%s, data=%v", args.ObjectType, args.Data)

	objType, exists := NetBoxObjectTypes[args.ObjectType]
	if !exists {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid object_type: %s", args.ObjectType)), nil
	}

	result, err := netboxClient.Create(objType.Endpoint, args.Data)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("API error: %v", err)), nil
	}

	resultJSON, _ := json.Marshal(result)
	return mcp.NewToolResultText(string(resultJSON)), nil
}

func handleUpdateObject(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		ObjectType string                 `json:"object_type"`
		ObjectID   int                    `json:"object_id"`
		Data       map[string]interface{} `json:"data"`
	}

	if err := decodeArguments(request.Params.Arguments, &args); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	log.Printf("MCP Tool Call: netbox_update_object - object_type=%s, object_id=%d, data=%v", args.ObjectType, args.ObjectID, args.Data)

	objType, exists := NetBoxObjectTypes[args.ObjectType]
	if !exists {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid object_type: %s", args.ObjectType)), nil
	}

	result, err := netboxClient.Update(objType.Endpoint, args.ObjectID, args.Data)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("API error: %v", err)), nil
	}

	resultJSON, _ := json.Marshal(result)
	return mcp.NewToolResultText(string(resultJSON)), nil
}

func handleDeleteObject(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var args struct {
		ObjectType string `json:"object_type"`
		ObjectID   int    `json:"object_id"`
	}

	if err := decodeArguments(request.Params.Arguments, &args); err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid arguments: %v", err)), nil
	}

	log.Printf("MCP Tool Call: netbox_delete_object - object_type=%s, object_id=%d", args.ObjectType, args.ObjectID)

	objType, exists := NetBoxObjectTypes[args.ObjectType]
	if !exists {
		return mcp.NewToolResultError(fmt.Sprintf("Invalid object_type: %s", args.ObjectType)), nil
	}

	success, err := netboxClient.Delete(objType.Endpoint, args.ObjectID)
	if err != nil {
		return mcp.NewToolResultError(fmt.Sprintf("API error: %v", err)), nil
	}

	if !success {
		return mcp.NewToolResultError("Delete operation failed"), nil
	}

	return mcp.NewToolResultText(fmt.Sprintf(`{"success": true, "message": "Object %s with ID %d deleted successfully"}`, args.ObjectType, args.ObjectID)), nil
}
