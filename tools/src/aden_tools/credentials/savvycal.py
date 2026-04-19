"""
SavvyCal tool credentials.

Contains credentials for SavvyCal scheduling API integration.
"""

from .base import CredentialSpec

SAVVYCAL_CREDENTIALS = {
    "savvycal": CredentialSpec(
        env_var="SAVVYCAL_API_KEY",
        tools=[
            "savvycal_list_links",
            "savvycal_get_link",
            "savvycal_create_link",
            "savvycal_update_link",
            "savvycal_delete_link",
            "savvycal_list_events",
            "savvycal_get_event",
            "savvycal_cancel_event",
        ],
        required=True,
        startup_required=False,
        help_url="https://developer.savvycal.com/",
        description="SavvyCal API key for scheduling link and event management",
        # Auth method support
        aden_supported=False,
        direct_api_key_supported=True,
        api_key_instructions="""To get a SavvyCal API key:
1. Log in to SavvyCal (https://savvycal.com)
2. Go to Settings > Integrations > API
3. Click "Create new API token"
4. Give it a descriptive name
5. Copy the token (shown only once)""",
        # Health check configuration
        health_check_endpoint="https://api.savvycal.com/v1/me",
        health_check_method="GET",
        # Credential store mapping
        credential_id="savvycal",
        credential_key="api_key",
    ),
}
