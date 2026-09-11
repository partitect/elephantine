import sys
import json
import argparse
import uvicorn
from memagent.config import settings

def print_claude_config():
    """Outputs ready-to-paste JSON config for Claude Desktop."""
    python_exec = sys.executable
    config = {
        "mcpServers": {
            "elephantine": {
                "command": python_exec,
                "args": ["-m", "memagent.mcp.server"]
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
    print(f"  Command: {python_exec} -m memagent.mcp.server")
    print("----------------------------------------\n")

def main():
    parser = argparse.ArgumentParser(description="Elephantine: Zero-GPU, Local-First, CPU-Native AI Memory Layer")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # start (REST server)
    start_parser = subparsers.add_parser("start", help="Start the FastAPI REST server")
    start_parser.add_argument("--host", default=settings.HOST, help="Host address")
    start_parser.add_argument("--port", type=int, default=settings.PORT, help="Port number")

    # mcp (FastMCP stdio server)
    subparsers.add_parser("mcp", help="Run the Model Context Protocol (MCP) server over stdio")

    # config-claude
    subparsers.add_parser("config-claude", help="Generate ready-to-paste Claude Desktop MCP config")

    # config-cursor
    subparsers.add_parser("config-cursor", help="Generate Cursor MCP setup instructions")

    args = parser.parse_args()

    if args.command == "start":
        print(f"Starting MemAgent REST Server on http://{args.host}:{args.port}")
        uvicorn.run("memagent.api.app:app", host=args.host, port=args.port, reload=False)
    elif args.command == "mcp":
        from memagent.mcp.server import main as mcp_main
        mcp_main()
    elif args.command == "config-claude":
        print_claude_config()
    elif args.command == "config-cursor":
        print_cursor_config()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
