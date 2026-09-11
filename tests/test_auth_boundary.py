import pytest
from memagent.core.auth_interface import TenantContext, CommunityLocalAuthEngine, CommunityLocalTenantResolver
from memagent.enterprise import EnterpriseRbacEngine, EnterpriseTenantResolver

@pytest.mark.asyncio
async def test_community_auth_zero_overhead():
    engine = CommunityLocalAuthEngine()
    resolver = CommunityLocalTenantResolver()
    ctx = TenantContext()
    
    assert await engine.authorize_read(ctx, "general") is True
    assert await engine.authorize_write(ctx, "general") is True
    assert resolver.get_namespace(ctx) == "default"

@pytest.mark.asyncio
async def test_enterprise_rbac_isolation():
    rbac = EnterpriseRbacEngine()
    resolver = EnterpriseTenantResolver()
    
    # Read-only agent
    reader_ctx = TenantContext(tenant_id="corp_acme", agent_id="scout", roles=["agent_reader"])
    assert await rbac.authorize_read(reader_ctx, "general") is True
    assert await rbac.authorize_write(reader_ctx, "general") is False
    assert resolver.get_namespace(reader_ctx) == "tenant_corp_acme"

    # Writer agent
    writer_ctx = TenantContext(tenant_id="corp_acme", agent_id="analyst", roles=["agent_writer"])
    assert await rbac.authorize_write(writer_ctx, "general") is True
