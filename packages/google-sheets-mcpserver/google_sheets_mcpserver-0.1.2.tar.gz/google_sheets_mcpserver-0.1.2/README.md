# Google Sheets MCP

A Model Context Protocol (MCP) server that provides Google Sheets integration for AI assistants like Claude.
[Doc](https://developers.google.cn/workspace/sheets/api/reference/rest?hl=lv)

```json

{
  "mcpServers": {
    "google-sheets": {
      "env": {
        "GOOGLE_ACCESS_TOKEN": "GOOGLE_ACCESS_TOKEN",
        "GOOGLE_REFRESH_TOKEN": "GOOGLE_REFRESH_TOKEN",
        "GOOGLE_CLIENT_ID": "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET": "GOOGLE_CLIENT_SECRET"
      },
      "command": "uvx",
      "args": [
        "google-sheets-mcpserver"
      ]
    }
  }
}
```