import sys
import os
import json
import argparse
import uvicorn
from pathlib import Path
from typing import List, Optional
from elephantine.config import settings
from elephantine.core.project import detect_project_workspace

def get_claude_config_path() -> Path:
    """Returns the platform-specific path for Claude Desktop config."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        return base / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

def get_cursor_config_path() -> Path:
    """Returns the primary path for Cursor MCP configuration."""
    cursor_dir = Path.home() / ".cursor"
    return cursor_dir / "mcp.json"

def get_vscode_config_path() -> Path:
    """Returns the local project .vscode/settings.json path."""
    return Path.cwd() / ".vscode" / "settings.json"

def get_antigravity_config_paths() -> List[Path]:
    """Returns candidate paths for Google Antigravity MCP configuration."""
    return [
        Path.home() / ".gemini" / "antigravity" / "mcp_config.json",
        Path.home() / ".gemini" / "config" / "mcp_config.json"
    ]

def get_codex_config_paths() -> List[Path]:
    """Returns candidate paths for OpenAI Codex MCP configuration."""
    return [
        Path.cwd() / ".vscode" / "settings.json",
        Path.home() / ".codex" / "mcp.json",
        Path.home() / ".codex" / "config.json"
    ]

def _inject_mcp_config(target_path: Path, tool_name: str) -> bool:
    """Helper to safely inject elephantine into an MCP JSON file."""
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if target_path.exists():
            content = target_path.read_text(encoding="utf-8").strip()
            if content:
                try:
                    data = json.loads(content)
                except Exception:
                    data = {}

        if "mcpServers" not in data:
            data["mcpServers"] = {}

        data["mcpServers"]["elephantine"] = {
            "command": sys.executable,
            "args": ["-m", "elephantine.mcp.server"]
        }

        target_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[✓] Successfully configured Elephantine in {tool_name}: {target_path}")
        return True
    except Exception as e:
        print(f"[✗] Failed to configure {tool_name} at {target_path}: {e}")
        return False

def install_claude_mcp(target_path: Optional[Path] = None) -> bool:
    """Installs Elephantine MCP server into Claude Desktop config."""
    path = target_path or get_claude_config_path()
    return _inject_mcp_config(path, "Claude Desktop")

def install_cursor_mcp(target_path: Optional[Path] = None) -> bool:
    """Installs Elephantine MCP server into Cursor config."""
    path = target_path or get_cursor_config_path()
    return _inject_mcp_config(path, "Cursor")

def install_vscode_mcp(target_path: Optional[Path] = None) -> bool:
    """Installs Elephantine MCP server into project .vscode/settings.json."""
    path = target_path or get_vscode_config_path()
    return _inject_mcp_config(path, "VS Code / Codex")

def install_antigravity_mcp(target_path: Optional[Path] = None) -> bool:
    """Installs Elephantine MCP server into Google Antigravity config."""
    paths = [target_path] if target_path else get_antigravity_config_paths()
    success = False
    for p in paths:
        if _inject_mcp_config(p, "Google Antigravity"):
            success = True
    return success

def install_codex_mcp(target_path: Optional[Path] = None) -> bool:
    """Installs Elephantine MCP server into OpenAI Codex config."""
    paths = [target_path] if target_path else get_codex_config_paths()
    success = False
    for p in paths:
        if _inject_mcp_config(p, "OpenAI Codex"):
            success = True
    return success

def print_claude_config():
    """Outputs ready-to-paste JSON config for Claude Desktop."""
    python_exec = sys.executable
    config = {
        "mcpServers": {
            "elephantine": {
                "command": python_exec,
                "args": ["-m", "elephantine.mcp.server"]
            }
        }
    }
    print("\n--- Copy and paste into your claude_desktop_config.json ---")
    print(json.dumps(config, indent=2))
    print("-----------------------------------------------------------\n")

def print_cursor_config():
    """Outputs instructions for Cursor settings."""
    python_exec = sys.executable
    print("\n--- Cursor MCP Server Configuration ---")
    print("In Cursor Settings -> Features -> MCP Servers -> Add New:")
    print("  Name: elephantine")
    print("  Type: command")
    print(f"  Command: {python_exec} -m elephantine.mcp.server")
    print("----------------------------------------\n")

def print_codex_config():
    """Outputs instructions for OpenAI Codex, GitHub Copilot, and VS Code / Windsurf agent integration."""
    python_exec = sys.executable
    config = {
        "mcpServers": {
            "elephantine": {
                "command": python_exec,
                "args": ["-m", "elephantine.mcp.server"]
            }
        }
    }
    print("\n--- OpenAI Codex / GitHub Copilot / VS Code Agent Configuration ---")
    print("Add this to your workspace or user settings (`.vscode/settings.json` or MCP manager):")
    print(json.dumps(config, indent=2))
    print("REST Memory Endpoint for Codex / Copilot Extensions: http://127.0.0.1:8765/recall")
    print("--------------------------------------------------------------------\n")

def print_antigravity_config():
    """Outputs ready-to-paste JSON config for Google Antigravity."""
    python_exec = sys.executable
    config = {
        "mcpServers": {
            "elephantine": {
                "command": python_exec,
                "args": ["-m", "elephantine.mcp.server"]
            }
        }
    }
    print("\n--- Google Antigravity (AGY) MCP Configuration ---")
    print("Add this to your `~/.gemini/antigravity/mcp_config.json` or `.gemini/mcp_config.json`:")
    print(json.dumps(config, indent=2))
    print("--------------------------------------------------\n")

def run_remember_cli(args):
    """Stores a memory fact directly from the command line."""
    from elephantine.client import ElephantineClient
    workspace = args.workspace or detect_project_workspace()
    client = ElephantineClient(args.base_url)
    try:
        res = client.remember(
            content=args.content,
            category=args.category,
            entity_key=args.entity_key,
            workspace_id=workspace,
            role_authority=args.authority,
            source_agent=args.source_agent
        )
        print("\n[✓] Memory stored successfully:")
        print(f"  ID:          {res.get('id')}")
        print(f"  Workspace:   {workspace}")
        print(f"  Category:    {args.category}")
        print(f"  Authority:   {args.authority}")
        print(f"  Content:     {args.content}")
        conflicts = res.get('conflicts_resolved', [])
        if conflicts:
            print(f"  Superseded:  {len(conflicts)} conflict(s)")
        print()
    except Exception as e:
        print(f"\n[✗] Failed to store memory: {e}")
        print("    Make sure the Elephantine server is running: `elephantine start`\n")
        sys.exit(1)

def run_recall_cli(args):
    """Recalls memories directly from the command line."""
    from elephantine.client import ElephantineClient
    workspace = args.workspace or detect_project_workspace()
    client = ElephantineClient(args.base_url)
    try:
        res = client.recall(
            query=args.query,
            workspace_id=workspace,
            top_k=args.top_k,
            category=args.category
        )
        memories = res.get("memories", [])
        print(f"\n[🐘 Elephantine Recall] Found {len(memories)} memory item(s) for query: \"{args.query}\"")
        print(f"Workspace: {workspace} | Latency: {res.get('latency_ms', 0):.1f}ms\n")
        
        if not memories:
            print("  No matching memories found.")
        else:
            for idx, m in enumerate(memories, start=1):
                auth = m.get("role_authority", 0.5)
                cat = m.get("category", "general")
                score = m.get("decayed_score") or m.get("similarity_score", 0.0)
                content = m.get("content", "")
                print(f"  {idx}. [{cat}] (Authority: {auth}, Score: {score:.3f})")
                print(f"     \"{content}\"\n")
        
        graph = res.get("graph_triplets", [])
        if graph:
            print("  [Knowledge Graph Relations]:")
            for t in graph:
                print(f"    - ({t.get('subject')}) --[{t.get('predicate')}]--> ({t.get('object')})")
            print()
    except Exception as e:
        print(f"\n[✗] Failed to recall memory: {e}")
        print("    Make sure the Elephantine server is running: `elephantine start`\n")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Elephantine: Zero-GPU, Local-First, CPU-Native AI Memory Layer")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # start (REST server)
    start_parser = subparsers.add_parser("start", help="Start the FastAPI REST server")
    start_parser.add_argument("--host", default=settings.HOST, help="Host address")
    start_parser.add_argument("--port", type=int, default=settings.PORT, help="Port number")

    # mcp (FastMCP stdio server)
    subparsers.add_parser("mcp", help="Run the Model Context Protocol (MCP) server over stdio")

    # Auto-Installers
    subparsers.add_parser("install-antigravity", help="Automatically configure Google Antigravity MCP")
    subparsers.add_parser("install-codex", help="Automatically configure OpenAI Codex / Copilot MCP")
    subparsers.add_parser("install-claude", help="Automatically configure Claude Desktop MCP")
    subparsers.add_parser("install-cursor", help="Automatically configure Cursor MCP")
    subparsers.add_parser("install-vscode", help="Automatically configure VS Code / Codex MCP in .vscode/settings.json")

    # Manual Config Visualizers
    subparsers.add_parser("config-antigravity", help="Generate ready-to-paste Google Antigravity MCP config")
    subparsers.add_parser("config-claude", help="Generate ready-to-paste Claude Desktop MCP config")
    subparsers.add_parser("config-cursor", help="Generate Cursor MCP setup instructions")
    subparsers.add_parser("config-codex", help="Generate OpenAI Codex & GitHub Copilot / VS Code MCP config")

    # remember CLI
    rem_parser = subparsers.add_parser("remember", help="Store a memory fact from the terminal")
    rem_parser.add_argument("content", help="Fact or memory content to remember")
    rem_parser.add_argument("--category", default="general", help="Category (e.g. architecture, preference, fact)")
    rem_parser.add_argument("--workspace", default=None, help="Workspace/Project ID (auto-detected if omitted)")
    rem_parser.add_argument("--authority", type=float, default=0.5, help="Role authority score (0.0 to 1.0)")
    rem_parser.add_argument("--entity-key", default=None, help="Entity key for LWW conflict resolution")
    rem_parser.add_argument("--source-agent", default="cli", help="Identifier of calling agent/user")
    rem_parser.add_argument("--base-url", default=f"http://{settings.HOST}:{settings.PORT}", help="Elephantine server URL")

    # recall CLI
    rec_parser = subparsers.add_parser("recall", help="Retrieve relevant memories from the terminal")
    rec_parser.add_argument("query", help="Search query or question")
    rec_parser.add_argument("--workspace", default=None, help="Workspace/Project ID (auto-detected if omitted)")
    rec_parser.add_argument("--category", default=None, help="Optional category filter")
    rec_parser.add_argument("--top-k", type=int, default=5, help="Maximum number of memories to return")
    rec_parser.add_argument("--base-url", default=f"http://{settings.HOST}:{settings.PORT}", help="Elephantine server URL")

    # trigger-create CLI
    tc_parser = subparsers.add_parser("trigger-create", help="Create a proactive memory trigger")
    tc_parser.add_argument("content", help="Memory content to trigger")
    tc_parser.add_argument("--trigger", required=True, help="Condition e.g. 'every:30m', 'weekly:FRI:17:00', or ISO datetime")
    tc_parser.add_argument("--type", default="datetime", help="Trigger type (datetime, interval, weekly, daily)")
    tc_parser.add_argument("--workspace", default=None, help="Workspace ID (auto-detected if omitted)")
    tc_parser.add_argument("--agent", default="default", help="Target agent ID to notify")
    tc_parser.add_argument("--webhook", default=None, help="Optional webhook URL")
    tc_parser.add_argument("--base-url", default=f"http://{settings.HOST}:{settings.PORT}", help="Elephantine server URL")

    # trigger-pending CLI
    tp_parser = subparsers.add_parser("trigger-pending", help="List unacknowledged proactive memory alerts")
    tp_parser.add_argument("--agent", default="default", help="Target agent ID")
    tp_parser.add_argument("--workspace", default=None, help="Workspace ID (auto-detected if omitted)")
    tp_parser.add_argument("--base-url", default=f"http://{settings.HOST}:{settings.PORT}", help="Elephantine server URL")

    args = parser.parse_args()

    if args.command == "start":
        print(f"Starting Elephantine REST Server on http://{args.host}:{args.port}")
        uvicorn.run("elephantine.api.app:app", host=args.host, port=args.port, reload=False)
    elif args.command == "mcp":
        from elephantine.mcp.server import main as mcp_main
        mcp_main()
    elif args.command == "install-antigravity":
        install_antigravity_mcp()
    elif args.command == "install-codex":
        install_codex_mcp()
    elif args.command == "install-claude":
        install_claude_mcp()
    elif args.command == "install-cursor":
        install_cursor_mcp()
    elif args.command == "install-vscode":
        install_vscode_mcp()
    elif args.command == "remember":
        run_remember_cli(args)
    elif args.command == "recall":
        run_recall_cli(args)
    elif args.command == "trigger-create":
        from elephantine.client import ElephantineClient
        ws = args.workspace or detect_project_workspace()
        c = ElephantineClient(args.base_url)
        res = c.create_trigger(
            condition=args.trigger,
            content=args.content,
            trigger_type=args.type,
            target_agent=args.agent,
            workspace_id=ws,
            webhook_url=args.webhook
        )
        print(f"\n[🔔 Proactive Trigger Created]")
        print(f"  Trigger ID: {res.get('trigger_id')}")
        print(f"  Condition:  {args.trigger}")
        print(f"  Next Fire:  {res.get('next_trigger_at')}\n")
    elif args.command == "trigger-pending":
        from elephantine.client import ElephantineClient
        ws = args.workspace or detect_project_workspace()
        c = ElephantineClient(args.base_url)
        alerts = c.get_pending_alerts(target_agent=args.agent, workspace_id=ws)
        print(f"\n[🔔 Pending Proactive Alerts for Agent: '{args.agent}'] ({len(alerts)} items)")
        for a in alerts:
            print(f"  - [{a.get('trigger_id')}] \"{a.get('content')}\" (Condition: {a.get('condition')})")
        print()
    elif args.command == "config-antigravity":
        print_antigravity_config()
    elif args.command == "config-claude":
        print_claude_config()
    elif args.command == "config-cursor":
        print_cursor_config()
    elif args.command == "config-codex":
        print_codex_config()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
