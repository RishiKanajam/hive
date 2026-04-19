# SavvyCal Tool

MCP tool integration for [SavvyCal](https://savvycal.com) - modern, flexible scheduling software.

## Overview

This tool provides 8 MCP-registered functions for interacting with the SavvyCal API:

| Tool | Description |
|------|-------------|
| `savvycal_list_links` | List all scheduling links for the authenticated user |
| `savvycal_get_link` | Get detailed information about a specific scheduling link |
| `savvycal_create_link` | Create a new scheduling link with custom durations |
| `savvycal_update_link` | Update an existing scheduling link |
| `savvycal_delete_link` | Delete a scheduling link permanently |
| `savvycal_list_events` | List booked events with optional filters |
| `savvycal_get_event` | Get details of a specific booked event |
| `savvycal_cancel_event` | Cancel a booked event with an optional reason |

## Quick Start

```bash
export SAVVYCAL_API_KEY="your-api-token-here"
```

Then use any tool directly:

```python
# List your scheduling links
savvycal_list_links()

# Create a 30-minute scheduling link
savvycal_create_link(name="Quick Chat", durations=[30])
```

## Configuration

### Environment Variable

```bash
export SAVVYCAL_API_KEY="your-savvycal-api-token"
```

### Getting an API Key

1. Log in to [SavvyCal](https://savvycal.com)
2. Go to **Settings → Integrations → API**
3. Click **"Create new API token"**
4. Give it a descriptive name (e.g., "Hive Agent")
5. Copy the token — it is shown **only once**

## Usage Examples

### List All Scheduling Links

```python
savvycal_list_links(limit=20)
```

### Get a Specific Link

```python
savvycal_get_link(link_id="abc123")
```

### Create a Scheduling Link

```python
savvycal_create_link(
    name="Product Demo",
    durations=[30, 60],
    slug="product-demo",
    description="Book a live demo of our product",
    timezone="America/New_York",
)
```

### Update a Scheduling Link

```python
savvycal_update_link(
    link_id="abc123",
    name="Updated Demo",
    durations=[45],
)
```

### Delete a Scheduling Link

```python
savvycal_delete_link(link_id="abc123")
```

### List Upcoming Events

```python
savvycal_list_events(
    status="active",
    start_date="2024-01-01",
    end_date="2024-01-31",
    limit=50,
)
```

### Get Event Details

```python
savvycal_get_event(event_id="evt-456")
```

### Cancel an Event

```python
savvycal_cancel_event(
    event_id="evt-456",
    reason="Schedule conflict — will reach out to reschedule",
)
```

## API Reference

- **Base URL:** `https://api.savvycal.com/v1`
- **Authentication:** Bearer token (`Authorization: Bearer <token>`)
- **Documentation:** [SavvyCal API Reference](https://developer.savvycal.com/)

## Error Handling

All tools return a dict with either:
- **Success:** API response data
- **Error:** `{"error": "description"}` or `{"error": "description", "help": "guidance"}`

Common error scenarios:

| HTTP Code | Error Message |
|-----------|---------------|
| `401` | Invalid or expired SavvyCal API key |
| `403` | Access forbidden — check API key permissions |
| `404` | Resource not found |
| `429` | Rate limit exceeded — try again later |
| `5xx` | SavvyCal API error with HTTP status code |
| Timeout | Request timed out |
| Network | Network error with details |

## Troubleshooting

**"SavvyCal API key not configured"**
→ Ensure `SAVVYCAL_API_KEY` is set in your environment or passed via credential store.

**"Invalid or expired SavvyCal API key" (401)**
→ The token may have been revoked. Regenerate it in SavvyCal Settings → Integrations → API.

**"Access forbidden" (403)**
→ Your token may lack permissions for this resource. Check your token's scope.

**"Resource not found" (404)**
→ The link ID or event ID does not exist or was already deleted.

**"Rate limit exceeded" (429)**
→ You have hit SavvyCal's API rate limit. Wait briefly and retry.
