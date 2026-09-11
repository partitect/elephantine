import pytest
from httpx import AsyncClient, ASGITransport
from elephantine.api.app import app
from elephantine.config import settings
from elephantine.enterprise.rbac import api_key_manager, ROLE_ADMIN, ROLE_VIEWER, ROLE_EDITOR

@pytest.mark.asyncio
async def test_community_mode_auth_bypass():
    """In default Community mode (AUTH_ENABLED=False), requests succeed without API keys."""
    settings.AUTH_ENABLED = False
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/remember", json={
            "content": "Public community fact",
            "category": "fact",
            "workspace_id": "community-ws"
        })
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_enterprise_rbac_enforcement():
    """When AUTH_ENABLED=True, token validation and role permissions are enforced."""
    settings.AUTH_ENABLED = True
    
    # Register test keys
    admin_key = "test-key-admin-999"
    viewer_key = "test-key-viewer-111"
    editor_key = "test-key-editor-555"

    api_key_manager.register_key(admin_key, tenant_id="acme", roles=[ROLE_ADMIN])
    api_key_manager.register_key(viewer_key, tenant_id="acme", roles=[ROLE_VIEWER])
    api_key_manager.register_key(editor_key, tenant_id="acme", roles=[ROLE_EDITOR])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. No token -> 401 Unauthorized
        unauth_res = await client.post("/remember", json={"content": "Secret fact"})
        assert unauth_res.status_code == 401

        # 2. Invalid token -> 401 Unauthorized
        bad_token_res = await client.post(
            "/remember",
            json={"content": "Secret fact"},
            headers={"X-API-Key": "invalid-token-xyz"}
        )
        assert bad_token_res.status_code == 401

        # 3. Viewer role -> Read allowed (200), but Write forbidden (403)
        viewer_write = await client.post(
            "/remember",
            json={"content": "Viewer attempt"},
            headers={"X-API-Key": viewer_key}
        )
        assert viewer_write.status_code == 403

        viewer_read = await client.post(
            "/recall",
            json={"query": "test query"},
            headers={"X-API-Key": viewer_key}
        )
        assert viewer_read.status_code == 200

        # 4. Editor role -> Write allowed (200)
        editor_write = await client.post(
            "/remember",
            json={"content": "Editor authorized fact"},
            headers={"X-API-Key": editor_key}
        )
        assert editor_write.status_code == 200

        # 5. Admin role via Bearer header -> Full access (200)
        admin_write = await client.post(
            "/remember",
            json={"content": "Admin authorized fact"},
            headers={"Authorization": f"Bearer {admin_key}"}
        )
        assert admin_write.status_code == 200

    # Reset back to community default
    settings.AUTH_ENABLED = False
