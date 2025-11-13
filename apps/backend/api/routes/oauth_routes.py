"""
OAuth 2.1 API Routes
Phase 3 Implementation - OAuth 2.1 compliant endpoints
"""

import json
import logging
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field, HttpUrl

from apps.backend.api.auth.auth import get_current_user
from apps.backend.api.auth.oauth21 import (
    AuthorizationRequest,
    OAuth21Server,
    PKCEMethod,
    TokenRequest,
    get_oauth_server,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["OAuth 2.1"])

# ===== Request/Response Models =====


class AuthorizeParams(BaseModel):
    """OAuth 2.1 Authorization Request Parameters"""

    client_id: str = Field(..., description="Client application ID")
    redirect_uri: HttpUrl = Field(..., description="Redirect URI")
    response_type: str = Field(..., pattern="^code$", description="Must be 'code'")
    scope: str = Field(..., description="Space-delimited scopes")
    state: str = Field(..., min_length=8, description="CSRF protection state")
    code_challenge: str = Field(..., min_length=43, max_length=128, description="PKCE challenge")
    code_challenge_method: PKCEMethod = Field(PKCEMethod.S256, description="PKCE method")


class TokenRequestForm(BaseModel):
    """OAuth 2.1 Token Request"""

    grant_type: str = Field(..., description="Grant type")
    code: Optional[str] = Field(None, description="Authorization code")
    redirect_uri: Optional[HttpUrl] = Field(None, description="Redirect URI")
    client_id: str = Field(..., description="Client ID")
    client_secret: Optional[str] = Field(None, description="Client secret")
    code_verifier: Optional[str] = Field(None, description="PKCE verifier")
    refresh_token: Optional[str] = Field(None, description="Refresh token for renewal")
    scope: Optional[str] = Field(None, description="Requested scopes")


class IntrospectRequest(BaseModel):
    """Token Introspection Request"""

    token: str = Field(..., description="Token to introspect")
    token_type_hint: Optional[str] = Field(None, description="Token type hint")
    client_id: str = Field(..., description="Client ID")
    client_secret: Optional[str] = Field(None, description="Client secret")


class RevokeRequest(BaseModel):
    """Token Revocation Request"""

    token: str = Field(..., description="Token to revoke")
    token_type_hint: Optional[str] = Field(None, description="Token type hint")
    client_id: str = Field(..., description="Client ID")
    client_secret: Optional[str] = Field(None, description="Client secret")


class ClientRegistrationRequest(BaseModel):
    """Dynamic Client Registration"""

    client_name: str = Field(..., description="Human-readable client name")
    redirect_uris: List[HttpUrl] = Field(..., description="Redirect URIs")
    grant_types: List[str] = Field(["authorization_code"], description="Grant types")
    response_types: List[str] = Field(["code"], description="Response types")
    scope: str = Field("", description="Default requested scopes")
    token_endpoint_auth_method: str = Field("none", description="Auth method")
    application_type: str = Field("web", description="Application type")
    contacts: Optional[List[str]] = Field(None, description="Contact emails")
    logo_uri: Optional[HttpUrl] = Field(None, description="Logo URL")
    client_uri: Optional[HttpUrl] = Field(None, description="Client homepage")
    policy_uri: Optional[HttpUrl] = Field(None, description="Privacy policy")
    tos_uri: Optional[HttpUrl] = Field(None, description="Terms of service")


# ===== Authorization Endpoints =====


@router.get("/authorize", response_class=HTMLResponse)
async def authorization_endpoint(
    request: Request,
    client_id: str,
    redirect_uri: str,
    response_type: str,
    scope: str,
    state: str,
    code_challenge: str,
    code_challenge_method: str = "S256",
    oauth_server: OAuth21Server = Depends(get_oauth_server),
):
    """
    OAuth 2.1 Authorization Endpoint

    Initiates the authorization flow. Returns an HTML consent screen.
    """

    # Validate request parameters
    if response_type != "code":
        error_params = {
            "error": "unsupported_response_type",
            "error_description": "Only 'code' response type is supported",
            "state": state,
        }
        return RedirectResponse(f"{redirect_uri}?{urlencode(error_params)}")

    if code_challenge_method not in ["S256", "plain"]:
        error_params = {
            "error": "invalid_request",
            "error_description": "Invalid code_challenge_method",
            "state": state,
        }
        return RedirectResponse(f"{redirect_uri}?{urlencode(error_params)}")

    # Validate client
    client = await oauth_server.get_client(client_id)
    if not client:
        error_params = {
            "error": "invalid_client",
            "error_description": "Client not found",
            "state": state,
        }
        return RedirectResponse(f"{redirect_uri}?{urlencode(error_params)}")

    if redirect_uri not in client.get("redirect_uris", []):
        error_params = {
            "error": "invalid_request",
            "error_description": "Invalid redirect_uri",
            "state": state,
        }
        return RedirectResponse(f"{redirect_uri}?{urlencode(error_params)}")

    # Generate consent form HTML
    consent_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authorization Request - ToolBoxAI</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .consent-container {{
                background: white;
                border-radius: 12px;
                padding: 2rem;
                max-width: 450px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h2 {{
                color: #333;
                margin-bottom: 1rem;
            }}
            .client-info {{
                background: #f7f8fa;
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
            }}
            .scopes {{
                margin: 1.5rem 0;
            }}
            .scope-item {{
                padding: 0.5rem 0;
                border-bottom: 1px solid #eee;
            }}
            .buttons {{
                display: flex;
                gap: 1rem;
                margin-top: 2rem;
            }}
            button {{
                flex: 1;
                padding: 0.75rem;
                border: none;
                border-radius: 6px;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .approve {{
                background: #667eea;
                color: white;
            }}
            .approve:hover {{
                background: #5a67d8;
            }}
            .deny {{
                background: #f1f3f5;
                color: #333;
            }}
            .deny:hover {{
                background: #e9ecef;
            }}
        </style>
    </head>
    <body>
        <div class="consent-container">
            <h2>Authorization Request</h2>
            <div class="client-info">
                <strong>{client.get('client_name', client_id)}</strong> is requesting access to your account.
            </div>

            <div class="scopes">
                <h3>Requested Permissions:</h3>
                {"".join([f'<div class="scope-item">• {s}</div>' for s in scope.split()])}
            </div>

            <form method="post" action="/oauth/authorize/consent">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="scope" value="{scope}">
                <input type="hidden" name="state" value="{state}">
                <input type="hidden" name="code_challenge" value="{code_challenge}">
                <input type="hidden" name="code_challenge_method" value="{code_challenge_method}">

                <div class="buttons">
                    <button type="submit" name="consent" value="approve" class="approve">
                        Allow Access
                    </button>
                    <button type="submit" name="consent" value="deny" class="deny">
                        Deny
                    </button>
                </div>
            </form>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=consent_html)


@router.post("/authorize/consent")
async def process_consent(
    request: Request,
    consent: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form(...),
    state: str = Form(...),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form("S256"),
    current_user: dict = Depends(get_current_user),
    oauth_server: OAuth21Server = Depends(get_oauth_server),
):
    """Process user consent decision"""

    if consent != "approve":
        # User denied consent
        error_params = {
            "error": "access_denied",
            "error_description": "User denied consent",
            "state": state,
        }
        return RedirectResponse(f"{redirect_uri}?{urlencode(error_params)}")

    # Create authorization request
    auth_request = AuthorizationRequest(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        code_challenge=code_challenge,
        code_challenge_method=PKCEMethod(code_challenge_method),
    )

    # Generate authorization code
    auth_code = await oauth_server.create_authorization_request(auth_request, current_user["id"])

    # Redirect with authorization code
    success_params = {"code": auth_code, "state": state}

    return RedirectResponse(f"{redirect_uri}?{urlencode(success_params)}")


# ===== Token Endpoints =====


@router.post("/token", status_code=status.HTTP_200_OK)
async def token_endpoint(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: str = Form(...),
    client_secret: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    scope: Optional[str] = Form(None),
    oauth_server: OAuth21Server = Depends(get_oauth_server),
):
    """
    OAuth 2.1 Token Endpoint

    Exchanges authorization codes or refresh tokens for access tokens.
    """

    try:
        if grant_type == "authorization_code":
            if not code or not redirect_uri or not code_verifier:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required parameters for authorization_code grant",
                )

            # Create token request
            token_request = TokenRequest(
                grant_type=grant_type,
                code=code,
                redirect_uri=redirect_uri,
                client_id=client_id,
                client_secret=client_secret,
                code_verifier=code_verifier,
            )

            # Exchange code for tokens
            token_response = await oauth_server.exchange_authorization_code(token_request)

        elif grant_type == "refresh_token":
            if not refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Missing refresh_token"
                )

            # Refresh access token
            token_response = await oauth_server.refresh_access_token(
                refresh_token, client_id, client_secret, scope
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported grant_type: {grant_type}",
            )

        return token_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token endpoint error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")


@router.post("/introspect", status_code=status.HTTP_200_OK)
async def introspection_endpoint(
    request: IntrospectRequest, oauth_server: OAuth21Server = Depends(get_oauth_server)
):
    """
    Token Introspection Endpoint (RFC 7662)

    Returns information about a token.
    """

    # Validate client credentials
    client = await oauth_server.get_client(request.client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client")

    if client.get("client_secret") and client["client_secret"] != request.client_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials"
        )

    # Introspect token
    introspection = await oauth_server.introspect_token(request.token, request.token_type_hint)

    return introspection


@router.post("/revoke", status_code=status.HTTP_200_OK)
async def revocation_endpoint(
    request: RevokeRequest, oauth_server: OAuth21Server = Depends(get_oauth_server)
):
    """
    Token Revocation Endpoint (RFC 7009)

    Revokes an access or refresh token.
    """

    # Validate client credentials
    client = await oauth_server.get_client(request.client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client")

    if client.get("client_secret") and client["client_secret"] != request.client_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials"
        )

    # Revoke token
    success = await oauth_server.revoke_token(request.token, request.token_type_hint)

    # Always return 200 OK per RFC 7009
    return {"revoked": success}


# ===== Client Management =====


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def client_registration(
    request: ClientRegistrationRequest,
    current_user: dict = Depends(get_current_user),
    oauth_server: OAuth21Server = Depends(get_oauth_server),
):
    """
    Dynamic Client Registration Endpoint (RFC 7591)

    Registers a new OAuth client application.
    """

    # Check if user can register clients (e.g., developers only)
    if current_user.get("role") not in ["developer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges to register clients",
        )

    # Generate client credentials
    client_id = secrets.token_urlsafe(24)
    client_secret = None

    # Generate secret for confidential clients
    if request.token_endpoint_auth_method != "none":
        client_secret = secrets.token_urlsafe(32)

    # Store client registration
    client_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": request.client_name,
        "redirect_uris": [str(uri) for uri in request.redirect_uris],
        "grant_types": request.grant_types,
        "response_types": request.response_types,
        "scope": request.scope,
        "token_endpoint_auth_method": request.token_endpoint_auth_method,
        "application_type": request.application_type,
        "contacts": request.contacts,
        "logo_uri": str(request.logo_uri) if request.logo_uri else None,
        "client_uri": str(request.client_uri) if request.client_uri else None,
        "policy_uri": str(request.policy_uri) if request.policy_uri else None,
        "tos_uri": str(request.tos_uri) if request.tos_uri else None,
        "owner_id": current_user["id"],
        "created_at": datetime.utcnow().isoformat(),
        "client_id_issued_at": int(datetime.utcnow().timestamp()),
    }

    # Store client
    await oauth_server.store_client(client_data)

    # Return registration response
    response = {
        "client_id": client_id,
        "client_id_issued_at": client_data["client_id_issued_at"],
        "client_name": request.client_name,
        "redirect_uris": request.redirect_uris,
        "grant_types": request.grant_types,
        "response_types": request.response_types,
        "scope": request.scope,
        "token_endpoint_auth_method": request.token_endpoint_auth_method,
    }

    if client_secret:
        response["client_secret"] = client_secret
        response["client_secret_expires_at"] = 0  # Never expires

    return response


@router.get("/clients", status_code=status.HTTP_200_OK)
async def list_clients(
    current_user: dict = Depends(get_current_user),
    oauth_server: OAuth21Server = Depends(get_oauth_server),
):
    """List OAuth clients owned by the current user"""

    clients = await oauth_server.get_user_clients(current_user["id"])

    # Remove sensitive information
    safe_clients = []
    for client in clients:
        safe_client = {
            "client_id": client["client_id"],
            "client_name": client["client_name"],
            "redirect_uris": client["redirect_uris"],
            "created_at": client["created_at"],
        }
        safe_clients.append(safe_client)

    return {"clients": safe_clients}


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    current_user: dict = Depends(get_current_user),
    oauth_server: OAuth21Server = Depends(get_oauth_server),
):
    """Delete an OAuth client"""

    # Get client
    client = await oauth_server.get_client(client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    # Check ownership
    if client["owner_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this client"
        )

    # Delete client and all associated tokens
    await oauth_server.delete_client(client_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ===== JWKS Endpoint =====


@router.get("/.well-known/jwks.json", status_code=status.HTTP_200_OK)
async def jwks_endpoint(oauth_server: OAuth21Server = Depends(get_oauth_server)):
    """
    JSON Web Key Set Endpoint

    Returns public keys for token verification.
    """

    jwks = await oauth_server.get_jwks()

    return jwks


# ===== OAuth Metadata =====


@router.get("/.well-known/oauth-authorization-server", status_code=status.HTTP_200_OK)
async def oauth_metadata():
    """
    OAuth 2.0 Authorization Server Metadata (RFC 8414)

    Returns server capabilities and endpoints.
    """

    base_url = "https://api.toolboxai.com"  # Should be from config

    metadata = {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "jwks_uri": f"{base_url}/oauth/.well-known/jwks.json",
        "registration_endpoint": f"{base_url}/oauth/register",
        "introspection_endpoint": f"{base_url}/oauth/introspect",
        "revocation_endpoint": f"{base_url}/oauth/revoke",
        "response_types_supported": ["code"],
        "response_modes_supported": ["query", "fragment"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": [
            "openid",
            "profile",
            "email",
            "offline_access",
            "read",
            "write",
            "admin",
        ],
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic",
            "none",
        ],
        "claims_supported": ["sub", "name", "email", "email_verified", "picture", "locale"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "introspection_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic",
        ],
        "revocation_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "service_documentation": f"{base_url}/docs/oauth",
        "ui_locales_supported": ["en-US"],
    }

    return metadata
