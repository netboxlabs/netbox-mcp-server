---
name: netbox-mcp-testing
description: This skill should be used when systematically testing the NetBox MCP server after code changes or to validate tool functionality. Provides structured protocol for discovering and testing MCP tools with a live NetBox instance, with emphasis on performance monitoring and comprehensive reporting.
---

# NetBox MCP Testing

## When to Use

Use this skill when:

- After code/configuration changes or new tool additions
- Validating MCP server functionality with NetBox instance

## Prerequisites Check

Before testing, verify:

1. NetBox MCP server is connected (run `/mcp` command)
2. Access to a live NetBox instance with test data exists
3. NETBOX_URL and NETBOX_TOKEN environment variables are configured

If prerequisites aren't met, testing cannot proceed reliably.

## Testing Approach

Execute comprehensive test scenarios autonomously, prioritizing high-value tests first.

### Core Testing Mindset

- **Provide clear, actionable feedback** - Include specific metrics whenever possible (response times, data sizes, error counts)
- **Investigate immediately** - When encountering issues, don't just report symptoms, immediately investigate root causes and propose solutions
- **Be metrics-driven** - Quantify results wherever possible rather than relying on qualitative assessments

## Core Testing Protocol

### 1. Pre-Test Analysis

Before beginning testing, assess the current state:

- Identify what has changed (if this is post-code-change validation)
- Determine testing scope (all tools vs. specific tools)
- Establish baseline expectations (what should work?)
- Note any known issues or limitations in the environment

### 2. Tool Discovery & Documentation

Discover available NetBox MCP tools by listing them. For each tool, document:

- Tool name and purpose
- Expected parameters (required and optional)
- Return data structure
- Error conditions

### 3. Systematic Testing with Performance Monitoring

Apply systematic testing to each discovered tool. Capture response times and metrics throughout.

**For each tool, test**:

1. **Valid inputs** - Execute with typical, valid parameters
   - Verify returns expected data structure
   - Confirm data is from NetBox instance
   - **Record response time for baseline**

2. **Invalid inputs** - Execute with incorrect parameters
   - Verify proper error messages
   - Ensure errors are informative (not generic)
   - Confirm server doesn't crash
   - Note error handling performance

3. **Edge cases** - Execute boundary conditions
   - Empty result sets (filters that match nothing)
   - Non-existent IDs or invalid identifiers
   - Missing required parameters
   - Permission boundaries (if applicable)
   - Large result sets (test pagination handling)

4. **Data integrity** - Validate returned data
   - Structure matches NetBox API format
   - Required fields are present
   - Data types are correct
   - Nested relationships are properly resolved

5. **Performance benchmarks** - Monitor efficiency metrics
   - Response times for typical queries
   - Behavior with large data sets
   - Resource usage patterns
   - Identify optimization opportunities

### 4. Issue Documentation & Investigation

When encountering failures or unexpected behavior:

1. **Document clearly** - Capture error messages, inputs, expected vs. actual behavior, performance metrics, affected features, and severity

2. **Investigate root causes** - Don't just report symptoms
   - Examine error messages and stack traces
   - Check NetBox API logs if accessible
   - Test variations to isolate the issue
   - Identify patterns across similar failures

3. **Propose solutions** - Provide actionable recommendations
   - Suggest code fixes when obvious
   - Recommend configuration changes if needed
   - Identify workarounds for temporary mitigation

### 5. Code Change Response

When the NetBox MCP server code has been modified, immediately:

1. **Reload the MCP server** - Disconnect and reconnect the mcp

2. **Re-run full test protocol** to validate changes
   - Execute all tests from Tool Discovery through Performance Monitoring
   - Document any new behaviors or changes from previous baseline

3. **Compare before/after results**
   - Check for functional regressions (previously working features now broken)
   - Check for performance regressions (response time increases)
   - Note any improvements or fixes

4. **Document impact of changes**
   - What was fixed or improved?
   - Were there any unintended side effects?
   - Are there remaining issues to address?

## Comprehensive Test Report

Produce a detailed test report as the primary deliverable.

### Naming Convention

Test reports should follow this naming pattern:

```
TEST_REPORT_YYYYMMDD_HHMM_[scope].md
```

**Examples**:
- `TEST_REPORT_20251017_1430_full.md` - Full test suite
- `TEST_REPORT_20251017_1530_post_code_change.md` - After modifications
- `TEST_REPORT_20251017_1600_[tool_name].md` - Specific tool

### Reporting

Use `assets/TEST_REPORT_TEMPLATE.md` as the structure - it includes all required sections (Executive Summary, Tool Inventory, Detailed Test Results with pass/fail/warnings, Performance Metrics, Recommendations, and Test Coverage Summary). Ensure proposed solutions from your investigations are included in the report.

**IMPORTANT**: Write test reports to the **project root directory** (not the assets folder). The template is in assets for reference, but the actual reports should be created at the root of the project.

## Efficiency Guidelines

Balance comprehensive testing with time constraints:

1. **Prioritize high-value tests** - Test core functionality first
2. **Start with happy paths** - Ensure basic operations work before edge cases
3. **Group similar tests** - Test multiple scenarios for the same tool together

## Troubleshooting Common Issues

**"Tool not found"**: MCP server isn't connected - verify with `/mcp` command
**"Authentication failed"**: Token invalid or expired - check NETBOX_TOKEN value
**"Connection refused"**: NetBox instance not accessible - verify NETBOX_URL
**Invalid parameters**: Review tool's expected parameters in its docstring or description

## Quick Example

Testing a hypothetical `netbox_get_objects` tool:

```text
✅ Valid: {"object_type": "devices", "filters": {}} → 150ms response
❌ Invalid: {"object_type": "invalid-type", "filters": {}} → ValueError (expected)
⚠️ Edge: {"object_type": "devices", "filters": {"name": "nonexistent"}} → Empty list, 200ms
```

Adapt this pattern to whatever tools are actually available.
