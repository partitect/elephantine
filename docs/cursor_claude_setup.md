# 1-Minute Setup: MemAgent with Cursor & Claude Desktop

MemAgent provides your AI agents in Cursor and Claude Desktop with **persistent local memory**, ensuring decisions, coding preferences, and workflow snippets are remembered across sessions with **zero cloud leakage** and **zero GPU requirements**.

---

## 1. Claude Desktop Setup

1. Open your Claude Desktop configuration file:
   - **macOS**: ~/Library/Application Support/Claude/claude_desktop_config.json
   - **Windows**: %APPDATA%\Claude\claude_desktop_config.json
   - **Linux**: ~/.config/Claude/claude_desktop_config.json

2. Add elephantine under mcpServers:
   `json
   {
     "mcpServers": {
       "elephantine": {
         "command": "python",
         "args": ["-m", "elephantine.mcp.server"]
       }
     }
   }
   `
   *(Or run python -m elephantine.cli config-claude to get your exact virtual environment Python path).*

3. Restart Claude Desktop. The hammer icon will show:
   - 
emember_fact
   - 
ecall_context
   - get_procedural_workflow

---

## 2. Cursor Setup

1. Open **Cursor Settings** (Ctrl+, or Cmd+,).
2. Navigate to **Features** -> **MCP Servers**.
3. Click **+ Add New MCP Server**:
   - **Name**: elephantine
   - **Type**: command
   - **Command**: python -m elephantine.mcp.server
4. Click Save. Cursor Composer and Chat now automatically invoke MemAgent to remember and recall architecture choices.

---

## 3. CLI Helper Commands

`ash
# Start REST API server
python -m elephantine.cli start --port 8765

# Start MCP Server directly
python -m elephantine.cli mcp

# Print Claude Desktop config snippet
python -m elephantine.cli config-claude

# Print Cursor setup instructions
python -m elephantine.cli config-cursor
`
