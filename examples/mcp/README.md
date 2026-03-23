# MCP Examples

This folder contains copy-paste examples for agents that connect to the
`technobulgarian-scraper` MCP server.

## Claude Desktop

Use the JSON snippet from
[`mcp_servers.example.json`](./mcp_servers.example.json) in your Claude Desktop
MCP configuration. Point `cwd` at the local clone of this repository.

## OpenClaw

Use the same `mcpServers` block from
[`mcp_servers.example.json`](./mcp_servers.example.json) in the OpenClaw MCP
configuration. Point `cwd` at the local clone of this repository.

## Notes

- Install the project first with `pip install -e .`
- Launch the server with `technobulgarian-scraper-mcp`
- The server exposes tools for listing exports, searching products, building
  the comparison report, and running a fresh scrape
