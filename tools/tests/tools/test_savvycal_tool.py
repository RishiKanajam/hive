"""Tests for SavvyCal tool with FastMCP."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastmcp import FastMCP

from aden_tools.tools.savvycal_tool import register_tools


@pytest.fixture
def mcp():
    """Create a FastMCP instance for testing."""
    return FastMCP("test-savvycal")


@pytest.fixture
def savvycal_tools(mcp: FastMCP, monkeypatch):
    """Register SavvyCal tools and return tool functions."""
    monkeypatch.setenv("SAVVYCAL_API_KEY", "test-api-key")
    register_tools(mcp)
    return {
        "list_links": mcp._tool_manager._tools["savvycal_list_links"].fn,
        "get_link": mcp._tool_manager._tools["savvycal_get_link"].fn,
        "create_link": mcp._tool_manager._tools["savvycal_create_link"].fn,
        "update_link": mcp._tool_manager._tools["savvycal_update_link"].fn,
        "delete_link": mcp._tool_manager._tools["savvycal_delete_link"].fn,
        "list_events": mcp._tool_manager._tools["savvycal_list_events"].fn,
        "get_event": mcp._tool_manager._tools["savvycal_get_event"].fn,
        "cancel_event": mcp._tool_manager._tools["savvycal_cancel_event"].fn,
    }


class TestToolRegistration:
    """Tests for tool registration."""

    def test_all_tools_registered(self, mcp: FastMCP, monkeypatch):
        """All 8 SavvyCal tools are registered."""
        monkeypatch.setenv("SAVVYCAL_API_KEY", "test-key")
        register_tools(mcp)

        expected_tools = [
            "savvycal_list_links",
            "savvycal_get_link",
            "savvycal_create_link",
            "savvycal_update_link",
            "savvycal_delete_link",
            "savvycal_list_events",
            "savvycal_get_event",
            "savvycal_cancel_event",
        ]

        for tool_name in expected_tools:
            assert tool_name in mcp._tool_manager._tools


class TestCredentialHandling:
    """Tests for credential handling."""

    def test_no_credentials_returns_error(self, mcp: FastMCP, monkeypatch):
        """Tools without credentials return helpful error."""
        monkeypatch.delenv("SAVVYCAL_API_KEY", raising=False)
        register_tools(mcp)

        fn = mcp._tool_manager._tools["savvycal_list_links"].fn
        result = fn()

        assert "error" in result
        assert "not configured" in result["error"]
        assert "help" in result

    def test_non_string_credential_returns_error(self, mcp: FastMCP, monkeypatch):
        """Non-string credential returns error dict instead of raising."""
        monkeypatch.delenv("SAVVYCAL_API_KEY", raising=False)
        creds = MagicMock()
        creds.get.return_value = 12345  # non-string
        register_tools(mcp, credentials=creds)

        fn = mcp._tool_manager._tools["savvycal_list_links"].fn
        result = fn()

        assert "error" in result
        assert "not configured" in result["error"]

    def test_credentials_from_env(self, mcp: FastMCP, monkeypatch):
        """Tools use credentials from environment variable."""
        monkeypatch.setenv("SAVVYCAL_API_KEY", "test-key")
        register_tools(mcp)

        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_get.return_value = mock_response

            fn = mcp._tool_manager._tools["savvycal_list_links"].fn
            result = fn()

            assert "error" not in result or "not configured" not in result.get("error", "")

            call_kwargs = mock_get.call_args
            headers = call_kwargs.kwargs.get("headers", {})
            assert headers.get("Authorization") == "Bearer test-key"

    def test_credentials_from_credential_store(self, mcp: FastMCP, monkeypatch):
        """Tools use credentials from credential store when provided."""
        monkeypatch.delenv("SAVVYCAL_API_KEY", raising=False)
        creds = MagicMock()
        creds.get.return_value = "store-api-key"
        register_tools(mcp, credentials=creds)

        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_get.return_value = mock_response

            fn = mcp._tool_manager._tools["savvycal_list_links"].fn
            result = fn()

            assert "error" not in result or "not configured" not in result.get("error", "")

            call_kwargs = mock_get.call_args
            headers = call_kwargs.kwargs.get("headers", {})
            assert headers.get("Authorization") == "Bearer store-api-key"


class TestListLinks:
    """Tests for savvycal_list_links tool."""

    def test_list_links_success(self, savvycal_tools):
        """List links returns links on success."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [
                    {"id": "link-1", "name": "30 Min Call"},
                    {"id": "link-2", "name": "60 Min Consultation"},
                ]
            }
            mock_get.return_value = mock_response

            result = savvycal_tools["list_links"]()

            assert "data" in result
            assert len(result["data"]) == 2

    def test_list_links_with_limit(self, savvycal_tools):
        """List links sends limit parameter to API."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_get.return_value = mock_response

            savvycal_tools["list_links"](limit=10)

            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args
            params = call_kwargs.kwargs.get("params", {})
            assert params.get("limit") == 10

    def test_list_links_clamps_limit_high(self, savvycal_tools):
        """Limit above 100 is clamped to 100."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_get.return_value = mock_response

            savvycal_tools["list_links"](limit=9999)

            call_kwargs = mock_get.call_args
            params = call_kwargs.kwargs.get("params", {})
            assert params.get("limit") == 100

    def test_list_links_clamps_limit_low(self, savvycal_tools):
        """Limit below 1 is clamped to 1."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_get.return_value = mock_response

            savvycal_tools["list_links"](limit=-5)

            call_kwargs = mock_get.call_args
            params = call_kwargs.kwargs.get("params", {})
            assert params.get("limit") == 1


class TestGetLink:
    """Tests for savvycal_get_link tool."""

    def test_get_link_success(self, savvycal_tools):
        """Get link returns link details."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": "link-123", "name": "Quick Chat", "durations": [30]}}
            mock_get.return_value = mock_response

            result = savvycal_tools["get_link"](link_id="link-123")

            assert "data" in result

    def test_get_link_not_found(self, savvycal_tools):
        """Get link returns error for non-existent link."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            result = savvycal_tools["get_link"](link_id="nonexistent")

            assert "error" in result
            assert "not found" in result["error"].lower()

    def test_get_link_missing_id(self, savvycal_tools):
        """Get link returns error for empty link_id."""
        result = savvycal_tools["get_link"](link_id="")

        assert "error" in result
        assert "link_id" in result["error"]

    def test_get_link_strips_whitespace(self, savvycal_tools):
        """Get link strips whitespace from link_id."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": "link-123"}}
            mock_get.return_value = mock_response

            savvycal_tools["get_link"](link_id="  link-123  ")

            call_args = mock_get.call_args
            assert "link-123" in call_args[0][0]
            assert "  link-123  " not in call_args[0][0]


class TestCreateLink:
    """Tests for savvycal_create_link tool."""

    def test_create_link_success(self, savvycal_tools):
        """Create link succeeds with valid data."""
        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": "new-link", "name": "Team Sync", "durations": [30]}}
            mock_post.return_value = mock_response

            result = savvycal_tools["create_link"](
                name="Team Sync",
                durations=[30],
            )

            assert "data" in result

            call_kwargs = mock_post.call_args
            json_data = call_kwargs.kwargs.get("json", {})
            assert json_data.get("name") == "Team Sync"
            assert json_data.get("durations") == [30]

    def test_create_link_with_all_options(self, savvycal_tools):
        """Create link sends all optional fields."""
        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": "full-link"}}
            mock_post.return_value = mock_response

            savvycal_tools["create_link"](
                name="Deep Dive",
                durations=[30, 60],
                slug="deep-dive",
                description="A thorough review session",
                timezone="America/Chicago",
            )

            call_kwargs = mock_post.call_args
            json_data = call_kwargs.kwargs.get("json", {})
            assert json_data.get("slug") == "deep-dive"
            assert json_data.get("description") == "A thorough review session"
            assert json_data.get("timezone") == "America/Chicago"
            assert json_data.get("durations") == [30, 60]

    def test_create_link_missing_name(self, savvycal_tools):
        """Create link returns error for missing name."""
        result = savvycal_tools["create_link"](name="", durations=[30])

        assert "error" in result
        assert "name" in result["error"]

    def test_create_link_missing_durations(self, savvycal_tools):
        """Create link returns error for missing durations."""
        result = savvycal_tools["create_link"](name="My Link", durations=[])

        assert "error" in result
        assert "durations" in result["error"]

    def test_create_link_strips_whitespace(self, savvycal_tools):
        """Create link strips whitespace from string fields."""
        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": "link-1"}}
            mock_post.return_value = mock_response

            savvycal_tools["create_link"](
                name="  My Link  ",
                durations=[30],
                slug="  my-link  ",
            )

            call_kwargs = mock_post.call_args
            json_data = call_kwargs.kwargs.get("json", {})
            assert json_data.get("name") == "My Link"
            assert json_data.get("slug") == "my-link"


class TestUpdateLink:
    """Tests for savvycal_update_link tool."""

    def test_update_link_success(self, savvycal_tools):
        """Update link succeeds with valid data."""
        with patch("httpx.patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": "link-123", "name": "Updated Name"}}
            mock_patch.return_value = mock_response

            result = savvycal_tools["update_link"](link_id="link-123", name="Updated Name")

            assert "data" in result

            call_kwargs = mock_patch.call_args
            json_data = call_kwargs.kwargs.get("json", {})
            assert json_data.get("name") == "Updated Name"

    def test_update_link_missing_id(self, savvycal_tools):
        """Update link returns error for missing link_id."""
        result = savvycal_tools["update_link"](link_id="")

        assert "error" in result
        assert "link_id" in result["error"]

    def test_update_link_durations(self, savvycal_tools):
        """Update link sends durations to API."""
        with patch("httpx.patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": "link-123"}}
            mock_patch.return_value = mock_response

            savvycal_tools["update_link"](link_id="link-123", durations=[15, 30, 45])

            call_kwargs = mock_patch.call_args
            json_data = call_kwargs.kwargs.get("json", {})
            assert json_data.get("durations") == [15, 30, 45]


class TestDeleteLink:
    """Tests for savvycal_delete_link tool."""

    def test_delete_link_success(self, savvycal_tools):
        """Delete link succeeds."""
        with patch("httpx.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_request.return_value = mock_response

            result = savvycal_tools["delete_link"](link_id="link-123")

            assert "error" not in result

            mock_request.assert_called_once()
            args = mock_request.call_args[0]
            assert args[0] == "DELETE"
            assert "link-123" in args[1]

    def test_delete_link_missing_id(self, savvycal_tools):
        """Delete link returns error for empty link_id."""
        result = savvycal_tools["delete_link"](link_id="")

        assert "error" in result
        assert "link_id" in result["error"]


class TestListEvents:
    """Tests for savvycal_list_events tool."""

    def test_list_events_success(self, savvycal_tools):
        """List events returns events on success."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [
                    {"id": "evt-1", "name": "Meeting with Alice"},
                    {"id": "evt-2", "name": "Meeting with Bob"},
                ]
            }
            mock_get.return_value = mock_response

            result = savvycal_tools["list_events"]()

            assert "data" in result
            assert len(result["data"]) == 2

    def test_list_events_with_filters(self, savvycal_tools):
        """List events sends filter parameters to API."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_get.return_value = mock_response

            savvycal_tools["list_events"](
                status="active",
                start_date="2024-01-01",
                end_date="2024-01-31",
                limit=25,
            )

            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args
            params = call_kwargs.kwargs.get("params", {})
            assert params.get("status") == "active"
            assert params.get("start_date") == "2024-01-01"
            assert params.get("end_date") == "2024-01-31"
            assert params.get("limit") == 25

    def test_list_events_clamps_limit(self, savvycal_tools):
        """Limit above 100 is clamped to 100."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_get.return_value = mock_response

            savvycal_tools["list_events"](limit=500)

            call_kwargs = mock_get.call_args
            params = call_kwargs.kwargs.get("params", {})
            assert params.get("limit") == 100


class TestGetEvent:
    """Tests for savvycal_get_event tool."""

    def test_get_event_success(self, savvycal_tools):
        """Get event returns event details."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "id": "evt-123",
                    "name": "Team Sync",
                    "start_time": "2024-01-20T14:00:00Z",
                }
            }
            mock_get.return_value = mock_response

            result = savvycal_tools["get_event"](event_id="evt-123")

            assert "data" in result

    def test_get_event_not_found(self, savvycal_tools):
        """Get event returns error for non-existent event."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            result = savvycal_tools["get_event"](event_id="nonexistent")

            assert "error" in result
            assert "not found" in result["error"].lower()

    def test_get_event_missing_id(self, savvycal_tools):
        """Get event returns error for empty event_id."""
        result = savvycal_tools["get_event"](event_id="")

        assert "error" in result
        assert "event_id" in result["error"]


class TestCancelEvent:
    """Tests for savvycal_cancel_event tool."""

    def test_cancel_event_success(self, savvycal_tools):
        """Cancel event succeeds."""
        with patch("httpx.patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": "evt-123", "status": "cancelled"}}
            mock_patch.return_value = mock_response

            result = savvycal_tools["cancel_event"](event_id="evt-123")

            assert "error" not in result

    def test_cancel_event_with_reason(self, savvycal_tools):
        """Cancel event includes cancellation reason."""
        with patch("httpx.patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": "evt-123"}}
            mock_patch.return_value = mock_response

            savvycal_tools["cancel_event"](event_id="evt-123", reason="Schedule conflict")

            call_kwargs = mock_patch.call_args
            json_data = call_kwargs.kwargs.get("json", {})
            assert json_data.get("reason") == "Schedule conflict"

    def test_cancel_event_missing_id(self, savvycal_tools):
        """Cancel event returns error for empty event_id."""
        result = savvycal_tools["cancel_event"](event_id="")

        assert "error" in result
        assert "event_id" in result["error"]

    def test_cancel_event_strips_whitespace(self, savvycal_tools):
        """Cancel event strips whitespace from reason."""
        with patch("httpx.patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": "evt-123"}}
            mock_patch.return_value = mock_response

            savvycal_tools["cancel_event"](event_id="evt-123", reason="  conflict  ")

            call_kwargs = mock_patch.call_args
            json_data = call_kwargs.kwargs.get("json", {})
            assert json_data.get("reason") == "conflict"


class TestErrorHandling:
    """Tests for error handling across tools."""

    def test_401_unauthorized(self, savvycal_tools):
        """401 response returns authentication error."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response

            result = savvycal_tools["list_links"]()

            assert "error" in result
            assert "Invalid" in result["error"] or "expired" in result["error"]

    def test_403_forbidden(self, savvycal_tools):
        """403 response returns forbidden error."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_get.return_value = mock_response

            result = savvycal_tools["list_links"]()

            assert "error" in result
            assert "forbidden" in result["error"].lower() or "Access" in result["error"]

    def test_429_rate_limit(self, savvycal_tools):
        """429 response returns rate limit error."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_get.return_value = mock_response

            result = savvycal_tools["list_links"]()

            assert "error" in result
            assert "rate limit" in result["error"].lower()

    def test_500_server_error(self, savvycal_tools):
        """500 response returns server error."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.return_value = {"message": "Internal Server Error"}
            mock_get.return_value = mock_response

            result = savvycal_tools["list_links"]()

            assert "error" in result
            assert "500" in result["error"]

    def test_timeout_error(self, savvycal_tools):
        """Timeout returns appropriate error."""
        with patch("httpx.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timed out")

            result = savvycal_tools["list_links"]()

            assert "error" in result
            assert "timed out" in result["error"].lower()

    def test_network_error(self, savvycal_tools):
        """Network error returns appropriate error."""
        with patch("httpx.get") as mock_get:
            mock_get.side_effect = httpx.RequestError("Connection failed")

            result = savvycal_tools["list_links"]()

            assert "error" in result
            assert "error" in result["error"].lower()

    def test_timeout_on_post(self, savvycal_tools):
        """Timeout on POST returns appropriate error."""
        with patch("httpx.post") as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timed out")

            result = savvycal_tools["create_link"](name="My Link", durations=[30])

            assert "error" in result
            assert "timed out" in result["error"].lower()

    def test_timeout_on_patch(self, savvycal_tools):
        """Timeout on PATCH returns appropriate error."""
        with patch("httpx.patch") as mock_patch:
            mock_patch.side_effect = httpx.TimeoutException("Timed out")

            result = savvycal_tools["cancel_event"](event_id="evt-123")

            assert "error" in result
            assert "timed out" in result["error"].lower()

    def test_timeout_on_delete(self, savvycal_tools):
        """Timeout on DELETE returns appropriate error."""
        with patch("httpx.request") as mock_request:
            mock_request.side_effect = httpx.TimeoutException("Timed out")

            result = savvycal_tools["delete_link"](link_id="link-123")

            assert "error" in result
            assert "timed out" in result["error"].lower()


class TestCredentialSpec:
    """Tests for SavvyCal credential spec."""

    def test_savvycal_credential_spec_exists(self):
        """SAVVYCAL_CREDENTIALS dict is defined."""
        from aden_tools.credentials.savvycal import SAVVYCAL_CREDENTIALS

        assert "savvycal" in SAVVYCAL_CREDENTIALS

    def test_savvycal_spec_env_var(self):
        """Credential spec has correct env var."""
        from aden_tools.credentials.savvycal import SAVVYCAL_CREDENTIALS

        spec = SAVVYCAL_CREDENTIALS["savvycal"]
        assert spec.env_var == "SAVVYCAL_API_KEY"

    def test_savvycal_spec_tools(self):
        """Credential spec lists all 8 tools."""
        from aden_tools.credentials.savvycal import SAVVYCAL_CREDENTIALS

        spec = SAVVYCAL_CREDENTIALS["savvycal"]
        expected_tools = [
            "savvycal_list_links",
            "savvycal_get_link",
            "savvycal_create_link",
            "savvycal_update_link",
            "savvycal_delete_link",
            "savvycal_list_events",
            "savvycal_get_event",
            "savvycal_cancel_event",
        ]
        for tool in expected_tools:
            assert tool in spec.tools

    def test_savvycal_spec_health_check(self):
        """Credential spec has health check endpoint configured."""
        from aden_tools.credentials.savvycal import SAVVYCAL_CREDENTIALS

        spec = SAVVYCAL_CREDENTIALS["savvycal"]
        assert spec.health_check_endpoint == "https://api.savvycal.com/v1/me"
        assert spec.health_check_method == "GET"

    def test_savvycal_spec_direct_api_key_supported(self):
        """Credential spec supports direct API key."""
        from aden_tools.credentials.savvycal import SAVVYCAL_CREDENTIALS

        spec = SAVVYCAL_CREDENTIALS["savvycal"]
        assert spec.direct_api_key_supported is True

    def test_savvycal_spec_api_key_instructions(self):
        """Credential spec includes setup instructions."""
        from aden_tools.credentials.savvycal import SAVVYCAL_CREDENTIALS

        spec = SAVVYCAL_CREDENTIALS["savvycal"]
        assert spec.api_key_instructions is not None
        assert "savvycal.com" in spec.api_key_instructions.lower()
