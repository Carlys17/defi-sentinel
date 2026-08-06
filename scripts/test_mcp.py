#!/usr/bin/env python3
"""Test connection to KeeperHub MCP server via streamable HTTP transport."""

import asyncio
import json
import os

from mcp import Client
from mcp.client.streamable_http import streamable_http_client, create_mcp_http_client

API_KEY = os.getenv("KEEPERHUB_API_KEY", "kh_aurRuIlaDrcAFoAujgkh3v5cz7UgrkwQ")
MCP_URL = "https://app.keeperhub.com/mcp"


async def main():
    print(f"Connecting to {MCP_URL}...")
    print(f"API Key: {API_KEY[:12]}...")
    print()

    http_client = create_mcp_http_client(
        headers={"Authorization": f"Bearer {API_KEY}"}
    )

    async with Client(
        streamable_http_client(MCP_URL, http_client=http_client),
    ) as client:
        # List available tools
        result = await client.list_tools()
        tools = result.tools

        # Get server info from client
        si = client.server_info
        print(f"✅ Connected! Server: {si.name} v{si.version}")
        print(f"🔧 Available tools: {len(tools)}")
        print("=" * 70)

        for i, tool in enumerate(tools, 1):
            print(f"\n{i}. {tool.name}")
            print(f"   Description: {tool.description[:150]}")
            # Show first few input schema properties
            if hasattr(tool, "inputSchema") and tool.inputSchema:
                props = tool.inputSchema.get("properties", {})
                required = tool.inputSchema.get("required", [])
                if props:
                    print(f"   Parameters ({len(props)}):")
                    for pname, pdesc in list(props.items())[:5]:
                        req = " *" if pname in required else ""
                        pinfo = pdesc if isinstance(pdesc, dict) else {}
                        ptype = pinfo.get("type", "any")
                        print(f"     - {pname}{req}: {ptype}")
                    if len(props) > 5:
                        print(f"     ... and {len(props) - 5} more")

        print("\n" + "=" * 70)
        print("\n✅ MCP connection successful!")
        print(f"\nNext step: Pick a tool to call. Try 'execute_transaction' or similar.")


if __name__ == "__main__":
    asyncio.run(main())