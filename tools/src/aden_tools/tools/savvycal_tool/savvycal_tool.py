"""
SavvyCal Tool - Scheduling links and meeting automation.

Supports:
- Scheduling link management (list, get, create, update, delete)
- Event/booking management (list, get, cancel)

API Reference: https://developer.savvycal.com/
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import httpx
from fastmcp import FastMCP

if TYPE_CHECKING:
    from aden_tools.credentials import CredentialStoreAdapter

SAVVYCAL_API_BASE = "https://api.savvycal.com/v1"
DEFAULT_TIMEOUT = 30.0


class _SavvycalClient:
    """Internal client wrapping SavvyCal API calls."""

    def __init__(self, api_key: str):
        self._api_key = api_key

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle common HTTP error codes."""
        if response.status_code == 401:
            return {"error": "Invalid or expired SavvyCal API key"}
        if response.status_code == 403:
            return {"error": "Access forbidden. Check API key permissions."}
        if response.status_code == 404:
            return {"error": "Resource not found"}
        if response.status_code == 429:
            return {"error": "Rate limit exceeded. Try again later."}
        if response.status_code >= 400:
            try:
                detail = response.json().get("message", response.text)
            except Exception:
                detail = response.text
            return {"error": f"SavvyCal API error (HTTP {response.status_code}): {detail}"}
        return response.json()

    def list_links(self, limit: int = 50) -> dict[str, Any]:
        """List all scheduling links for the authenticated user."""
        response = httpx.get(
            f"{SAVVYCAL_API_BASE}/links",
            headers=self._headers,
            params={"limit": limit},
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def get_link(self, link_id: str) -> dict[str, Any]:
        """Get a specific scheduling link by ID."""
        response = httpx.get(
            f"{SAVVYCAL_API_BASE}/links/{link_id}",
            headers=self._headers,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def create_link(
        self,
        name: str,
        durations: list[int],
        slug: str | None = None,
        description: str | None = None,
        timezone: str | None = None,
    ) -> dict[str, Any]:
        """Create a new scheduling link."""
        data: dict[str, Any] = {
            "name": name,
            "durations": durations,
        }
        if slug:
            data["slug"] = slug
        if description:
            data["description"] = description
        if timezone:
            data["timezone"] = timezone

        response = httpx.post(
            f"{SAVVYCAL_API_BASE}/links",
            headers=self._headers,
            json=data,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def update_link(
        self,
        link_id: str,
        name: str | None = None,
        slug: str | None = None,
        durations: list[int] | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing scheduling link."""
        data: dict[str, Any] = {}
        if name:
            data["name"] = name
        if slug:
            data["slug"] = slug
        if durations:
            data["durations"] = durations
        if description:
            data["description"] = description

        response = httpx.patch(
            f"{SAVVYCAL_API_BASE}/links/{link_id}",
            headers=self._headers,
            json=data,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def delete_link(self, link_id: str) -> dict[str, Any]:
        """Delete a scheduling link."""
        response = httpx.request(
            "DELETE",
            f"{SAVVYCAL_API_BASE}/links/{link_id}",
            headers=self._headers,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def list_events(
        self,
        status: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List booked events."""
        params: dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = httpx.get(
            f"{SAVVYCAL_API_BASE}/events",
            headers=self._headers,
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def get_event(self, event_id: str) -> dict[str, Any]:
        """Get details of a specific booked event."""
        response = httpx.get(
            f"{SAVVYCAL_API_BASE}/events/{event_id}",
            headers=self._headers,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def cancel_event(self, event_id: str, reason: str | None = None) -> dict[str, Any]:
        """Cancel a booked event."""
        data: dict[str, Any] = {}
        if reason:
            data["reason"] = reason

        response = httpx.patch(
            f"{SAVVYCAL_API_BASE}/events/{event_id}/cancel",
            headers=self._headers,
            json=data if data else None,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)


def register_tools(
    mcp: FastMCP,
    credentials: CredentialStoreAdapter | None = None,
) -> None:
    """Register SavvyCal tools with the MCP server."""

    def _get_api_key() -> str | None:
        """Get SavvyCal API key from credential manager or environment."""
        if credentials is not None:
            api_key = credentials.get("savvycal")
            if api_key is not None and not isinstance(api_key, str):
                return None
            return api_key
        return os.getenv("SAVVYCAL_API_KEY")

    def _get_client() -> _SavvycalClient | dict[str, str]:
        """Get a SavvyCal client, or return an error dict if no credentials."""
        api_key = _get_api_key()
        if not api_key:
            return {
                "error": "SavvyCal API key not configured",
                "help": "Set SAVVYCAL_API_KEY environment variable or configure via credential store",
            }
        return _SavvycalClient(api_key)

    # --- Scheduling Links ---

    @mcp.tool()
    def savvycal_list_links(limit: int = 50) -> dict:
        """
        List all scheduling links for the authenticated SavvyCal user.

        Use this when you need to:
        - Browse all scheduling pages you've created
        - Find a link's ID before updating or deleting it
        - Audit which scheduling links are active
        - Retrieve link slugs to share with invitees

        Args:
            limit: Maximum number of links to return (1-100, default: 50)

        Returns:
            Dict with list of scheduling links or error
        """
        client = _get_client()
        if isinstance(client, dict):
            return client

        limit = max(1, min(100, limit))

        try:
            return client.list_links(limit=limit)
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    @mcp.tool()
    def savvycal_get_link(link_id: str) -> dict:
        """
        Get detailed information about a specific scheduling link.

        Use this when you need to:
        - Inspect the configuration of a particular scheduling page
        - Verify durations, slug, and description for a link
        - Retrieve link settings before making updates
        - Share or display a specific scheduling link to a user

        Args:
            link_id: The unique ID of the scheduling link

        Returns:
            Dict with link details or error
        """
        client = _get_client()
        if isinstance(client, dict):
            return client

        link_id = link_id.strip() if link_id else link_id
        if not link_id:
            return {"error": "link_id is required"}

        try:
            return client.get_link(link_id)
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    @mcp.tool()
    def savvycal_create_link(
        name: str,
        durations: list[int],
        slug: str | None = None,
        description: str | None = None,
        timezone: str | None = None,
    ) -> dict:
        """
        Create a new SavvyCal scheduling link.

        Use this when you need to:
        - Set up a new scheduling page for a specific meeting type
        - Create a link with custom durations (e.g., 15, 30, 60 minutes)
        - Programmatically provision scheduling pages for users or teams
        - Build scheduling workflows that auto-create meeting links

        Args:
            name: Display name for the scheduling link
            durations: List of meeting durations in minutes (e.g., [30, 60])
            slug: URL-friendly identifier (e.g., "quick-chat"); auto-generated if omitted
            description: Optional description shown to invitees
            timezone: Default timezone (e.g., "America/New_York"); defaults to account timezone

        Returns:
            Dict with created link details or error
        """
        client = _get_client()
        if isinstance(client, dict):
            return client

        name = name.strip() if name else name
        if not name:
            return {"error": "name is required"}
        if not durations:
            return {"error": "durations is required"}

        if slug:
            slug = slug.strip()
        if description:
            description = description.strip()
        if timezone:
            timezone = timezone.strip()

        try:
            return client.create_link(
                name=name,
                durations=durations,
                slug=slug or None,
                description=description or None,
                timezone=timezone or None,
            )
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    @mcp.tool()
    def savvycal_update_link(
        link_id: str,
        name: str | None = None,
        slug: str | None = None,
        durations: list[int] | None = None,
        description: str | None = None,
    ) -> dict:
        """
        Update an existing SavvyCal scheduling link.

        Use this when you need to:
        - Rename a scheduling page or change its URL slug
        - Add or remove available meeting durations
        - Update the description shown to invitees
        - Modify scheduling link settings without recreating it

        Args:
            link_id: The unique ID of the link to update
            name: New display name for the link
            slug: New URL-friendly identifier
            durations: New list of meeting durations in minutes
            description: New description for the link

        Returns:
            Dict with updated link details or error
        """
        client = _get_client()
        if isinstance(client, dict):
            return client

        link_id = link_id.strip() if link_id else link_id
        if not link_id:
            return {"error": "link_id is required"}

        if name:
            name = name.strip()
        if slug:
            slug = slug.strip()
        if description:
            description = description.strip()

        try:
            return client.update_link(
                link_id=link_id,
                name=name or None,
                slug=slug or None,
                durations=durations,
                description=description or None,
            )
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    @mcp.tool()
    def savvycal_delete_link(link_id: str) -> dict:
        """
        Delete a SavvyCal scheduling link permanently.

        Use this when you need to:
        - Remove a scheduling page that is no longer needed
        - Clean up outdated or unused scheduling links
        - Revoke a link so invitees can no longer book through it

        Args:
            link_id: The unique ID of the link to delete

        Returns:
            Dict confirming deletion or error
        """
        client = _get_client()
        if isinstance(client, dict):
            return client

        link_id = link_id.strip() if link_id else link_id
        if not link_id:
            return {"error": "link_id is required"}

        try:
            return client.delete_link(link_id)
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    # --- Events ---

    @mcp.tool()
    def savvycal_list_events(
        status: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 50,
    ) -> dict:
        """
        List booked events (meetings scheduled through SavvyCal links).

        Use this when you need to:
        - View upcoming or past scheduled meetings
        - Filter events by status (e.g., active, cancelled)
        - Get meetings within a specific date range
        - Build a calendar view of all scheduled appointments

        Args:
            status: Filter by status (e.g., "active", "cancelled")
            start_date: Filter events on or after this date (ISO 8601, e.g., "2024-01-01")
            end_date: Filter events on or before this date (ISO 8601, e.g., "2024-01-31")
            limit: Maximum number of events to return (1-100, default: 50)

        Returns:
            Dict with list of events or error
        """
        client = _get_client()
        if isinstance(client, dict):
            return client

        limit = max(1, min(100, limit))

        if status:
            status = status.strip()
        if start_date:
            start_date = start_date.strip()
        if end_date:
            end_date = end_date.strip()

        try:
            return client.list_events(
                status=status or None,
                start_date=start_date or None,
                end_date=end_date or None,
                limit=limit,
            )
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    @mcp.tool()
    def savvycal_get_event(event_id: str) -> dict:
        """
        Get details of a specific booked event.

        Use this when you need to:
        - Retrieve attendee information for a booked meeting
        - Check the time, duration, and location of a specific event
        - Review event metadata before taking action (e.g., cancel)
        - Fetch event details to display in a notification or summary

        Args:
            event_id: The unique ID of the booked event

        Returns:
            Dict with event details or error
        """
        client = _get_client()
        if isinstance(client, dict):
            return client

        event_id = event_id.strip() if event_id else event_id
        if not event_id:
            return {"error": "event_id is required"}

        try:
            return client.get_event(event_id)
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    @mcp.tool()
    def savvycal_cancel_event(event_id: str, reason: str | None = None) -> dict:
        """
        Cancel a booked SavvyCal event.

        Use this when you need to:
        - Cancel a scheduled meeting on behalf of the organizer
        - Free up a time slot that was previously booked
        - Programmatically cancel events with a provided reason
        - Handle cancellation workflows in automated scheduling pipelines

        Args:
            event_id: The unique ID of the event to cancel
            reason: Optional cancellation reason communicated to the attendee

        Returns:
            Dict confirming cancellation or error
        """
        client = _get_client()
        if isinstance(client, dict):
            return client

        event_id = event_id.strip() if event_id else event_id
        if not event_id:
            return {"error": "event_id is required"}

        if reason:
            reason = reason.strip()

        try:
            return client.cancel_event(event_id, reason=reason or None)
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}
