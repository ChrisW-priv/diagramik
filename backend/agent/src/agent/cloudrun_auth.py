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

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import id_token

logger = logging.getLogger(__name__)


class CloudRunAuth(httpx.Auth):
    """HTTPX auth for CloudRun service-to-service calls using OIDC identity tokens.

    This auth class generates OIDC identity tokens with the target service URL
    as the audience claim. Tokens are fetched from the GCP metadata server
    using the service account attached to the CloudRun service.

    Args:
        target_audience: The target service URL (e.g., https://service.run.app)
    """

    def __init__(self, target_audience: str):
        self.target_audience = target_audience
        logger.info(f"CloudRunAuth initialized with audience: {target_audience}")

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """Inject OIDC identity token into request Authorization header.

        Args:
            request: The outgoing HTTP request

        Yields:
            The request with Authorization header added
        """
        try:
            # Fetch identity token from GCP metadata server
            # This uses Application Default Credentials (service account in CloudRun)
            token = id_token.fetch_id_token(Request(), self.target_audience)
            request.headers["Authorization"] = f"Bearer {token}"
            logger.debug(f"Added OIDC identity token to request for {request.url}")
        except Exception as e:
            logger.error(f"Failed to fetch OIDC identity token: {e}")
            raise

        yield request


def is_running_in_cloudrun() -> bool:
    """Detect if running in CloudRun environment.

    CloudRun sets the K_SERVICE environment variable with the service name.

    Returns:
        True if running in CloudRun, False otherwise
    """
    return os.getenv("K_SERVICE") is not None


def patch_fastagent_oauth():
    """Patch FastAgent's OAuth provider to use CloudRun OIDC auth when deployed.

    This function intercepts FastAgent's `build_oauth_provider()` to return
    CloudRunAuth instead of the OAuth 2.0 authorization code flow when running
    in CloudRun environments.

    The patch only applies in CloudRun (detected via K_SERVICE env var).
    In local development, the original OAuth flow is preserved.
    """
    if not is_running_in_cloudrun():
        logger.info("Not running in CloudRun - skipping OAuth patch")
        return

    logger.info(
        "Running in CloudRun - patching FastAgent OAuth for OIDC identity tokens"
    )

    # Import FastAgent's auth module
    try:
        from fast_agent_mcp import auth as fastagent_auth
    except ImportError:
        logger.warning("Could not import fast_agent_mcp.auth - OAuth patch skipped")
        return

    # Store original OAuth builder
    _ = fastagent_auth.build_oauth_provider

    def patched_build_oauth(
        mcp_url: str, client_id: str | None = None, client_secret: str | None = None
    ):
        """Patched OAuth builder that returns CloudRunAuth in CloudRun environments.

        Args:
            mcp_url: The MCP service URL
            client_id: OAuth client ID (ignored in CloudRun)
            client_secret: OAuth client secret (ignored in CloudRun)

        Returns:
            CloudRunAuth instance configured with mcp_url as audience
        """
        logger.info(f"Using CloudRunAuth for MCP service at {mcp_url}")

        # Extract base URL for audience (remove path components)
        # MCP URL format: https://service.run.app/mcp
        # Audience should be: https://service.run.app
        from urllib.parse import urlparse

        parsed = urlparse(mcp_url)
        audience = f"{parsed.scheme}://{parsed.netloc}"

        return CloudRunAuth(target_audience=audience)

    # Apply patch
    fastagent_auth.build_oauth_provider = patched_build_oauth
    logger.info("FastAgent OAuth successfully patched for CloudRun OIDC authentication")
