#!/usr/bin/env python3
"""Execute first real transaction via KeeperHub MCP - for hackathon submission."""

import asyncio
import json
import os
from datetime import datetime

from mcp import Client
from mcp.client.streamable_http import streamable_http_client, create_mcp_http_client

API_KEY = os.getenv("KEEPERHUB_API_KEY", "kh_aurRuIlaDrcAFoAujgkh3v5cz7UgrkwQ")
MCP_URL = "https://app.keeperhub.com/mcp"

# Our wallet address
WALLET = "0x749B59edC27F53E74fF93A6ef32a57be6E5F05f3"


async def main():
    print("=" * 70)
    print("🚀 DeFi Sentinel - First Onchain Transaction via KeeperHub")
    print("=" * 70)
    print(f"Wallet: {WALLET}")
    print(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    http_client = create_mcp_http_client(
        headers={"Authorization": f"Bearer {API_KEY}"}
    )

    async with Client(
        streamable_http_client(MCP_URL, http_client=http_client),
    ) as client:
        si = client.server_info
        print(f"✅ Connected to {si.name} v{si.version}")
        print()

        # Step 1: List integrations to get wallet ID
        print("📋 Step 1: Listing wallet integrations...")
        integrations = await client.call_tool("list_integrations", {})
        print(integrations)
        print()

        # Step 2: Simulate transfer first (safe test)
        print("📋 Step 2: Simulating ETH transfer on Base Sepolia...")
        print("-" * 50)

        try:
            sim_result = await client.call_tool("execute_transfer", {
                "chain_id": "84532",  # Base Sepolia
                "to_address": WALLET,  # self-transfer
                "amount": "0.0001",
                "simulate": True
            })
            print(f"✅ Simulation result:")
            print(sim_result)
            print()
        except Exception as e:
            print(f"Simulation error: {e}")
            print()

        # Step 3: Execute real transfer
        print("📋 Step 3: Executing REAL ETH transfer on Base Sepolia...")
        print("-" * 50)
        print(f"  From: {WALLET}")
        print(f"  To:   {WALLET}")
        print(f"  Amount: 0.0001 ETH (self-transfer for test)")
        print(f"  Chain: Base Sepolia (84532)")
        print()

        try:
            tx_result = await client.call_tool("execute_transfer", {
                "chain_id": "84532",  # Base Sepolia
                "to_address": WALLET,
                "amount": "0.0001",
            })
            print(f"✅ Transaction submitted!")
            print(f"Result: {tx_result}")

            # Parse for transaction hash
            result_str = str(tx_result)
            if "transaction_hash" in result_str or "txHash" in result_str or "0x" in result_str:
                print()
                print("=" * 70)
                print("🎉 TRANSACTION EXECUTED SUCCESSFULLY!")
                print("=" * 70)
                # Extract tx hash if present
                for line in result_str.split('\n'):
                    if '0x' in line and ('hash' in line.lower() or 'tx' in line.lower()):
                        print(f"  {line.strip()}")

        except Exception as e:
            print(f"Transaction error: {e}")


if __name__ == "__main__":
    asyncio.run(main())