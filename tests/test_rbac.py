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


@pytest.mark.asyncio
async def test_all_memory_routes_auth_enforcement(monkeypatch):
    """Verify that graph, procedural, consolidation, and proactive endpoints require authentication."""
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    admin_key = "test-all-routes-admin-key"
    api_key_manager.register_key(admin_key, tenant_id="acme", roles=[ROLE_ADMIN])
    headers = {"Authorization": f"Bearer {admin_key}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        routes_to_test = [
            ("post", "/graph/query", {"entity": "Python"}),
            ("post", "/procedural/track", {
                "session_id": "sess-1",
                "tool_name": "calc",
                "arguments": {},
                "result": "42",
                "success": True,
                "execution_time_ms": 1.0
            }),
            ("get", "/procedural/session/sess-1", None),
            ("post", "/procedural/workflow", {
                "pattern_name": "wf-test",
                "description": "test workflow",
                "step_sequence": [{"tool": "calc", "action": "add"}]
            }),
            ("get", "/procedural/workflow/wf-test", None),
            ("post", "/memories/consolidate", {"entity_key": "dummy-key"}),
            ("post", "/memories/prune", None),
            ("post", "/proactive/triggers", {
                "trigger_type": "event",
                "condition_value": "test_event",
                "target_agent": "test-bot",
                "content": "Alert message"
            }),
            ("get", "/proactive/pending", None),
            ("post", "/proactive/acknowledge/non-existent-trigger", None),
        ]

        for method, path, payload in routes_to_test:
            # 1. Without credentials -> 401 Unauthorized
            if method == "post":
                res_unauth = await client.post(path, json=payload if payload is not None else {})
            else:
                res_unauth = await client.get(path)
            assert res_unauth.status_code == 401, f"Expected 401 for unauthenticated {method.upper()} {path}, got {res_unauth.status_code}"

            # 2. With valid credentials -> must NOT be 401 (e.g. 200, or 404 for non-existent item, but never 401)
            if method == "post":
                res_auth = await client.post(path, json=payload if payload is not None else {}, headers=headers)
            else:
                res_auth = await client.get(path, headers=headers)
            assert res_auth.status_code != 401, f"Expected authenticated {method.upper()} {path} to pass auth, got 401"

