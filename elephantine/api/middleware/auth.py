from typing import Optional
from fastapi import Header, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from elephantine.config import settings
from elephantine.core.auth_interface import TenantContext
from elephantine.enterprise.rbac import api_key_manager, rbac_auth_engine

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_tenant_context(
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> TenantContext:
    """
    Resolves the calling agent's tenant and security context.
    If settings.AUTH_ENABLED is False (Community mode), grants full local access with zero configuration.
    If True, verifies the API key or Bearer token.
    """
    if not settings.AUTH_ENABLED:
        return TenantContext(
            tenant_id="default_tenant",
            agent_id="local",
            roles=["admin"],
            is_enterprise=False
        )

    token = api_key or (bearer.credentials if bearer else None)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Missing API Key. Provide via 'X-API-Key' header or 'Authorization: Bearer <key>'."
        )

    context = api_key_manager.authenticate(token)
    if not context:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid Elephantine API Key."
        )

    return context

async def require_write_permission(
    context: TenantContext = Depends(get_current_tenant_context)
) -> TenantContext:
    """Ensures the caller has write authorization."""
    can_write = await rbac_auth_engine.authorize_write(context)
    if not can_write:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Caller role has insufficient permissions to write memories."
        )
    return context

async def require_read_permission(
    context: TenantContext = Depends(get_current_tenant_context)
) -> TenantContext:
    """Ensures the caller has read authorization."""
    can_read = await rbac_auth_engine.authorize_read(context)
    if not can_read:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Caller role has insufficient permissions to read memories."
        )
    return context
