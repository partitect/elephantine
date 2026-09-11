import json
import pytest
from pathlib import Path
from elephantine.cli import (
    install_claude_mcp,
    install_cursor_mcp,
    install_vscode_mcp,
    install_antigravity_mcp,
    install_codex_mcp
)

def test_install_claude_mcp(tmp_path):
    target = tmp_path / "Claude" / "claude_desktop_config.json"
    assert not target.exists()
    
    success = install_claude_mcp(target_path=target)
    assert success
    assert target.exists()
    
    data = json.loads(target.read_text(encoding="utf-8"))
    assert "mcpServers" in data
    assert "elephantine" in data["mcpServers"]
    assert "elephantine.mcp.server" in data["mcpServers"]["elephantine"]["args"]

def test_install_cursor_mcp(tmp_path):
    target = tmp_path / ".cursor" / "mcp.json"
    success = install_cursor_mcp(target_path=target)
    assert success
    assert target.exists()
    
    data = json.loads(target.read_text(encoding="utf-8"))
    assert "mcpServers" in data
    assert "elephantine" in data["mcpServers"]

def test_install_vscode_mcp_merge(tmp_path):
    target = tmp_path / ".vscode" / "settings.json"
    target.parent.mkdir(parents=True)
    # Pre-existing settings
    target.write_text(json.dumps({"editor.fontSize": 14}), encoding="utf-8")
    
    success = install_vscode_mcp(target_path=target)
    assert success
    
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["editor.fontSize"] == 14
    assert "mcpServers" in data
    assert "elephantine" in data["mcpServers"]

def test_install_antigravity_mcp(tmp_path):
    target = tmp_path / ".gemini" / "antigravity" / "mcp_config.json"
    success = install_antigravity_mcp(target_path=target)
    assert success
    assert target.exists()
    
    data = json.loads(target.read_text(encoding="utf-8"))
    assert "mcpServers" in data
    assert "elephantine" in data["mcpServers"]
    assert "elephantine.mcp.server" in data["mcpServers"]["elephantine"]["args"]

def test_install_codex_mcp(tmp_path):
    target = tmp_path / ".codex" / "mcp.json"
    success = install_codex_mcp(target_path=target)
    assert success
    assert target.exists()
    
    data = json.loads(target.read_text(encoding="utf-8"))
    assert "mcpServers" in data
    assert "elephantine" in data["mcpServers"]
