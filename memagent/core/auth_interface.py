from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class TenantContext(BaseModel):
    """Context holding active tenant, agent identity, and security roles."""
    tenant_id: str = Field(default="default_tenant", description="Unique tenant ID for data isolation")
    agent_id: str = Field(default="default_agent", description="Calling agent identifier")
    roles: List[str] = Field(default_factory=lambda: ["admin"], description="Security roles, e.g. ['read', 'write', 'admin']")
    is_enterprise: bool = Field(default=False, description="Flag indicating enterprise tier license active")

class IAuthorizationEngine(ABC):
    """Abstract interface defining memory access authorization."""
    @abstractmethod
    async def authorize_read(self, context: TenantContext, resource_category: str) -> bool:
        """Determines if the calling agent can read memories in given category/tenant."""
        pass

    @abstractmethod
    async def authorize_write(self, context: TenantContext, resource_category: str) -> bool:
        """Determines if the calling agent can write/modify memories."""
        pass

class CommunityLocalAuthEngine(IAuthorizationEngine):
    """
    Default Community Core implementation.
    Permits local single-user access with zero overhead and zero configuration.
    """
    async def authorize_read(self, context: TenantContext, resource_category: str) -> bool:
        return True

    async def authorize_write(self, context: TenantContext, resource_category: str) -> bool:
        return True

class ITenantStorageResolver(ABC):
    """Resolves data storage paths or table namespaces per tenant."""
    @abstractmethod
    def get_namespace(self, context: TenantContext) -> str:
        pass

class CommunityLocalTenantResolver(ITenantStorageResolver):
    """Community Core: Single local namespace."""
    def get_namespace(self, context: TenantContext) -> str:
        return "default"
