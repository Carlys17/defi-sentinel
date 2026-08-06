#!/usr/bin/env python3
"""
DeFi Sentinel — Quick Start: Execute First Onchain Transaction
===============================================================

This script helps you execute your FIRST real onchain transaction via KeeperHub.
Follow the steps to get a transaction hash for your hackathon submission.

Usage:
    python scripts/quick_start.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Settings, get_settings
from src.keeperhub.client import KeeperHubClient, ExecutionResult, ExecutionStatus

async def check_setup(settings: Settings) -> list[str]:
    """Check if environment is properly configured."""
    issues = []

    if not settings.keeperhub_api_key or settings.keeperhub_api_key == "kh-your-key-here":
        issues.append("❌ KEEPERHUB_API_KEY not set. Get one at https://app.keeperhub.com")

    if not settings.wallet_address or settings.wallet_address == "0x0000000000000000000000000000000000000000":
        issues.append("❌ WALLET_ADDRESS not set. Use your KeeperHub wallet address")

    if settings.keeperhub_mcp_url != "https://app.keeperhub.com/mcp":
        issues.append(f"⚠️  KeeperHub MCP URL is {settings.keeperhub_mcp_url}, expected https://app.keeperhub.com/mcp")

    return issues

async def execute_first_transaction(settings: Settings, simulate: bool = False) -> dict:
    """Execute the first onchain transaction via KeeperHub."""
    client = KeeperHubClient(settings)

    print("\n" + "=" * 70)
    print("  DeFi Sentinel — First Onchain Transaction")
    print("=" * 70)

    # Step 1: Health check
    print("\n[1/6] Checking KeeperHub connection...")
    health = await client.health_check()
    if health:
        print("  ✅ KeeperHub MCP server is reachable")
    else:
        print("  ⚠️  Health check failed - will try direct execution")

    # Step 2: List workflows
    print("\n[2/6] Listing available workflows...")
    try:
        workflows = await client.list_workflows()
        print(f"  ✅ Found {len(workflows)} workflows")
        for wf in workflows[:5]:
            print(f"     • {wf.name}: {wf.description[:70]}")
    except Exception as e:
        print(f"  ⚠️  Could not list workflows: {e}")

    # Step 3: List integrations
    print("\n[3/6] Listing configured integrations...")
    try:
        integrations = await client.list_integrations()
        print(f"  ✅ Found {len(integrations)} integrations")
        for integration in integrations:
            print(f"     • {integration}")
    except Exception as e:
        print(f"  ⚠️  Could not list integrations: {e}")

    # Step 4: Get wallet info
    print("\n[4/6] Getting wallet integration...")
    try:
        wallet = await client.get_wallet_integration()
        print(f"  ✅ Wallet: {wallet}")
    except Exception as e:
        print(f"  ⚠️  Could not get wallet info: {e}")

    # Step 5: Simulate transfer
    print("\n[5/6] Simulating transfer...")
    try:
        sim_result = await client.execute_transfer(
            to_address=settings.wallet_address,
            amount="1000000000000000",  # 0.001 ETH in wei
            simulate=True,
        )
        print(f"  ✅ Simulation: {sim_result.status.value}")
        if sim_result.gas_used:
            print(f"     Gas estimate: {sim_result.gas_used}")
    except Exception as e:
        print(f"  ⚠️  Simulation failed: {e}")

    # Step 6: Execute real transfer
    if simulate:
        print("\n[6/6] Skipping real execution (simulation mode)")
        return {"mode": "simulation"}

    print("\n[6/6] Executing REAL transfer...")
    print("  ⚠️  This will execute a real onchain transaction!")

    try:
        result = await client.execute_transfer(
            to_address=settings.wallet_address,
            amount="1000000000000000",  # 0.001 ETH
            simulate=False,
        )

        print(f"\n  {'=' * 50}")
        print(f"  TRANSACTION RESULT")
        print(f"  {'=' * 50}")
        print(f"  Status: {result.status.value}")
        print(f"  Chain: {result.chain}")

        if result.transaction_hash:
            print(f"  ✅ Transaction Hash: {result.transaction_hash}")
            print(f"\n  📝 SAVE THIS HASH FOR YOUR HACKATHON SUBMISSION!")
        else:
            print(f"  ⏳ Transaction pending...")
            if result.execution_id:
                print(f"  Execution ID: {result.execution_id}")

        if result.gas_used:
            print(f"  Gas Used: {result.gas_used}")

        return result.to_dict()

    except Exception as e:
        print(f"\n  ❌ Execution failed: {e}")
        print(f"\n  Troubleshooting:")
        print(f"  1. Check your KeeperHub API key is valid")
        print(f"  2. Verify wallet is configured in KeeperHub dashboard")
        print(f"  3. Check Discord: https://discord.gg/keeperhub")
        return {"error": str(e)}
    finally:
        await client.close()

async def main():
    parser = argparse.ArgumentParser(description="DeFi Sentinel - Quick Start")
    parser.add_argument("--simulate", action="store_true", help="Simulation only (no real transaction)")
    args = parser.parse_args()

    settings = get_settings()

    # Check setup
    print("Checking setup...")
    issues = await check_setup(settings)

    if issues:
        print("\nSetup Issues:")
        for issue in issues:
            print(f"  {issue}")
        print("\nPlease fix these issues and try again.")
        print("Edit .env file with your actual API keys and wallet address.")
        sys.exit(1)

    print("✅ Setup looks good!")

    # Execute transaction
    result = await execute_first_transaction(settings, simulate=args.simulate)

    # Save result
    if result and "error" not in result:
        results_file = Path("logs/first_transaction.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        results_file.write_text(json.dumps(result, indent=2))
        print(f"\nResult saved to {results_file}")

    print("\n" + "=" * 70)
    print("  Next Steps:")
    print("=" * 70)
    print("  1. Copy the transaction hash above")
    print("  2. Update README.md with the transaction link")
    print("  3. Record demo video showing the execution")
    print("  4. Submit to hackathon with transaction link")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())