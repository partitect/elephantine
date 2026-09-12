import json
from typing import Dict, List, Optional, Set
from elephantine.core.auth_interface import IAuthorizationEngine, TenantContext
from elephantine.config import settings

# Predefined standard RBAC roles
ROLE_ADMIN = "admin"
ROLE_ARCHITECT = "architect"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"

# Predefined role permissions
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    ROLE_ADMIN: {"read", "write", "delete", "admin"},
    ROLE_ARCHITECT: {"read", "write", "delete"},
    ROLE_EDITOR: {"read", "write"},
    ROLE_VIEWER: {"read"}
}

class RoleBasedAuthEngine(IAuthorizationEngine):
    """
    Enterprise Role-Based Access Control (RBAC) engine.
    Evaluates role permissions against requested memory actions.
    """
    def __init__(self, role_permissions: Optional[Dict[str, Set[str]]] = None):
        self.role_permissions = role_permissions or ROLE_PERMISSIONS

    def _has_permission(self, context: TenantContext, permission: str) -> bool:
        for role in context.roles:
            perms = self.role_permissions.get(role, set())
            if permission in perms or "admin" in perms:
                return True
        return False

    async def authorize_read(self, context: TenantContext, resource_category: str = "general") -> bool:
        """Verifies if the tenant context has read access."""
        return self._has_permission(context, "read")

    async def authorize_write(self, context: TenantContext, resource_category: str = "general") -> bool:
        """Verifies if the tenant context has write access."""
        return self._has_permission(context, "write")

    async def authorize_delete(self, context: TenantContext) -> bool:
        """Verifies if the tenant context has delete/deprecate access."""
        return self._has_permission(context, "delete")

class ApiKeyManager:
    """
    Manages API keys and maps tokens to TenantContext records.
    """
    def __init__(self, keys_json: Optional[str] = None):
        self._keys: Dict[str, TenantContext] = {}
        raw = keys_json or settings.API_KEYS_JSON
        if raw and raw.strip():
            try:
                parsed = json.loads(raw)
                for k, v in parsed.items():
                    ws_list = v.get("allowed_workspaces", ["*"])
                    auth_val = float(v.get("max_role_authority", 1.0))
                    self._keys[k] = TenantContext(
                        tenant_id=v.get("tenant_id", "default_tenant"),
                        agent_id=v.get("agent_id", "default_agent"),
                        roles=v.get("roles", [ROLE_VIEWER]),
                        allowed_workspaces=set(ws_list) if isinstance(ws_list, (list, set)) else {str(ws_list)},
                        max_role_authority=auth_val,
                        is_enterprise=True
                    )
            except Exception:
                pass

    def register_key(
        self,
        api_key: str,
        tenant_id: str,
        roles: List[str],
        agent_id: str = "agent",
        allowed_workspaces: Optional[List[str]] = None,
        max_role_authority: float = 1.0
    ):
        """Dynamically registers an API key with workspace boundaries and authority limits."""
        ws_set = set(allowed_workspaces) if allowed_workspaces else {"*"}
        self._keys[api_key] = TenantContext(
            tenant_id=tenant_id,
            agent_id=agent_id,
            roles=roles,
            allowed_workspaces=ws_set,
            max_role_authority=float(max_role_authority),
            is_enterprise=True
        )

    def authenticate(self, api_key: Optional[str]) -> Optional[TenantContext]:
        """Authenticates an incoming API key."""
        if not api_key:
            return None
        return self._keys.get(api_key.strip())

# Global singleton instance for enterprise middleware
api_key_manager = ApiKeyManager()
rbac_auth_engine = RoleBasedAuthEngine()
