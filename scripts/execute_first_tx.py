#!/usr/bin/env python3
"""Execute first real transaction via KeeperHub MCP - for hackathon submission."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings

MCP_URL = "https://app.keeperhub.com/mcp"


async def main():
    settings = get_settings()

    print("=" * 70)
    print("🚀 DeFi Sentinel - First Onchain Transaction via KeeperHub")
    print("=" * 70)
    print(f"Wallet: {settings.wallet_address}")
    print(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    # Use KeeperHub MCP client
    from src.keeperhub.client import KeeperHubClient

    client = KeeperHubClient(settings)

    initialized = await client.initialize()
    if initialized:
        print("✅ Connected to KeeperHub MCP")
    else:
        print("❌ Failed to connect to KeeperHub MCP")
        return
    print()

    # Step 1: List integrations
    print("📋 Step 1: Listing wallet integrations...")
    try:
        integrations = await client.list_integrations()
        print(f"Found {len(integrations)} integration(s)")
    except Exception as e:
        print(f"Error listing integrations: {e}")
    print()

    # Step 2: Simulate transfer first (safe test)
    print("📋 Step 2: Simulating ETH transfer on Base Sepolia...")
    print("-" * 50)

    try:
        sim_result = await client.execute_transfer(
            to_address=settings.wallet_address,
            amount="0.0001",
            simulate=True,
        )
        print(f"✅ Simulation result: {sim_result.status.value}")
        if sim_result.error:
            print(f"   Error: {sim_result.error}")
    except Exception as e:
        print(f"Simulation error: {e}")
    print()

    # Step 3: Execute real transfer
    print("📋 Step 3: Executing REAL ETH transfer on Base Sepolia...")
    print("-" * 50)
    print(f"  From: {settings.wallet_address}")
    print(f"  To:   {settings.wallet_address}")
    print("  Amount: 0.0001 ETH (self-transfer for test)")
    print("  Chain: Base Sepolia (84532)")
    print()

    try:
        tx_result = await client.execute_transfer(
            to_address=settings.wallet_address,
            amount="0.0001",
            simulate=False,
        )
        print("✅ Transaction submitted!")
        print(f"Status: {tx_result.status.value}")

        if tx_result.transaction_hash:
            print()
            print("=" * 70)
            print("🎉 TRANSACTION EXECUTED SUCCESSFULLY!")
            print("=" * 70)
            print(f"  Transaction Hash: {tx_result.transaction_hash}")

    except Exception as e:
        print(f"Transaction error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
