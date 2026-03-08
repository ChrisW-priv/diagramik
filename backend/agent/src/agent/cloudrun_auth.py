"""CloudRun service-to-service authentication for FastAgent MCP connections.

This module patches FastAgent's OAuth flow to use OIDC identity tokens when
running in CloudRun environments, enabling proper service-to-service authentication.

CloudRun authentication requires:
1. OIDC identity tokens (not OAuth access tokens)
2. Audience claim set to the target service URL
3. Tokens generated from service account credentials via metadata server
"""

import logging
import os
from typing import Generator
from urllib.parse import urlparse

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import id_token

logger = logging.getLogger(__name__)


class CloudRunAuth(httpx.Auth):
    """HTTPX auth for CloudRun service-to-service calls using OIDC identity tokens.

    Generates OIDC identity tokens with the target service URL as the audience
    claim, fetched from the GCP metadata server using the attached service account.
    """

    def __init__(self, target_audience: str):
        self.target_audience = target_audience
        logger.info(f"CloudRunAuth initialized with audience: {target_audience}")

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        try:
            token = id_token.fetch_id_token(Request(), self.target_audience)
            request.headers["Authorization"] = f"Bearer {token}"
            logger.debug(f"Added OIDC identity token for {request.url}")
        except Exception as e:
            logger.error(f"Failed to fetch OIDC identity token: {e}")
            raise

        yield request


def is_running_in_cloudrun() -> bool:
    """Detect if running in CloudRun (K_SERVICE env var is set)."""
    return os.getenv("K_SERVICE") is not None


def patch_fastagent_oauth():
    """Patch FastAgent's OAuth provider to use CloudRun OIDC auth when deployed.

    Replaces `build_oauth_provider` in `fast_agent.mcp.oauth_client` so that
    HTTP/SSE connections to MCP servers use OIDC identity tokens instead of
    the interactive OAuth 2.0 authorization code flow.

    No-op when not running in CloudRun (detected via K_SERVICE env var).
    """
    if not is_running_in_cloudrun():
        logger.info("Not running in CloudRun - skipping OAuth patch")
        return

    logger.info(
        "Running in CloudRun - patching FastAgent OAuth for OIDC identity tokens"
    )

    try:
        from fast_agent.mcp import oauth_client as fastagent_oauth
        from fast_agent.mcp import mcp_connection_manager
    except ImportError:
        logger.warning(
            "Could not import fast_agent.mcp.oauth_client - OAuth patch skipped"
        )
        return

    # Store original for reference
    _original_build_oauth_provider = fastagent_oauth.build_oauth_provider

    def patched_build_oauth_provider(server_config):
        """Return CloudRunAuth for OIDC-based service-to-service auth."""
        if server_config.transport not in ("sse", "http"):
            return None

        url = server_config.url or ""
        parsed = urlparse(url)
        audience = f"{parsed.scheme}://{parsed.netloc}"

        logger.info(
            f"Using CloudRunAuth for MCP service at {url} (audience: {audience})"
        )
        return CloudRunAuth(target_audience=audience)

    # Patch in both modules (mcp_connection_manager imports it at module level)
    fastagent_oauth.build_oauth_provider = patched_build_oauth_provider
    mcp_connection_manager.build_oauth_provider = patched_build_oauth_provider

    logger.info("FastAgent OAuth successfully patched for CloudRun OIDC authentication")
