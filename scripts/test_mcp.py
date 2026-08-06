#!/usr/bin/env python3
"""Test connection to KeeperHub MCP server via streamable HTTP transport."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings

MCP_URL = "https://app.keeperhub.com/mcp"


async def main():
    settings = get_settings()

    print(f"Connecting to {MCP_URL}...")
    print(f"API Key: {settings.keeperhub_api_key[:12]}...")
    print()

    # Use KeeperHub MCP client
    from src.keeperhub.client import KeeperHubClient

    client = KeeperHubClient(settings)

    initialized = await client.initialize()
    if not initialized:
        print("❌ Failed to initialize MCP session")
        return

    print("✅ Connected to KeeperHub MCP")
    print()

    # List available workflows
    print("📋 Listing available workflows...")
    try:
        workflows = await client.list_workflows()
        print(f"Found {len(workflows)} workflow(s)")
        for wf in workflows[:5]:
            print(f"  - {wf.name}: {wf.description[:100]}")
    except Exception as e:
        print(f"Error listing workflows: {e}")
    print()

    # List integrations
    print("📋 Listing integrations...")
    try:
        integrations = await client.list_integrations()
        print(f"Found {len(integrations)} integration(s)")
        for integration in integrations:
            print(f"  - {integration}")
    except Exception as e:
        print(f"Error listing integrations: {e}")
    print()

    # List action schemas
    print("📋 Listing action schemas...")
    try:
        await client.list_action_schemas()
        print("Action schemas loaded successfully")
    except Exception as e:
        print(f"Error listing action schemas: {e}")
    print()

    print("=" * 70)
    print("\n✅ MCP connection successful!")
    print("\nNext step: Use the KeeperHub client to execute transactions.")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
