#!/usr/bin/env python3
"""
DeFi Sentinel — Quick Start: Execute First Onchain Transaction
===============================================================

This script helps you execute your FIRST real onchain transaction via KeeperHub.

Usage:
    python3 scripts/quick_start.py              # Full flow with real transaction
    python3 scripts/quick_start.py --simulate   # Simulation only
    python3 scripts/quick_start.py --status     # Check status
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Settings, get_settings
from src.keeperhub.client import KeeperHubClient
from src.observability.audit import AuditEventType, AuditTrail


async def check_setup(settings: Settings) -> list[str]:
    """Check if environment is properly configured."""
    issues = []

    if not settings.keeperhub_api_key or settings.keeperhub_api_key == "kh-your-key-here":
        issues.append("❌ KEEPERHUB_API_KEY not set. Get one at https://app.keeperhub.com")

    return issues


async def execute_first_transaction(settings: Settings, simulate: bool = False) -> dict:
    """Execute the first onchain transaction via KeeperHub."""
    client = KeeperHubClient(settings)
    audit = AuditTrail()

    print("\n" + "=" * 70)
    print("  DeFi Sentinel — First Onchain Transaction")
    print("=" * 70)

    # Step 1: Initialize MCP session
    print("\n[1/6] Initializing KeeperHub MCP session...")
    initialized = await client.initialize()
    if initialized:
        print("  ✅ MCP session initialized")
    else:
        print("  ❌ Failed to initialize MCP session")
        return {"error": "MCP initialization failed"}

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

    # Step 4: List action schemas
    print("\n[4/6] Listing action schemas...")
    try:
        await client.list_action_schemas()
        print("  ✅ Found action schemas")
    except Exception as e:
        print(f"  ⚠️  Could not list action schemas: {e}")

    # Step 5: Simulate transfer
    print("\n[5/6] Simulating transfer...")
    try:
        sim_result = await client.execute_transfer(
            to_address=settings.wallet_address,
            amount="0.001",  # 0.001 BASE
            simulate=True,
        )
        print(f"  ✅ Simulation result: {sim_result.status.value}")
        if sim_result.error:
            print(f"     Error: {sim_result.error}")
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
            amount="0.001",  # 0.001 BASE
            simulate=False,
        )

        print(f"\n  {'=' * 50}")
        print("  TRANSACTION RESULT")
        print(f"  {'=' * 50}")
        print(f"  Status: {result.status.value}")
        print(f"  Chain: {result.chain}")

        if result.transaction_hash:
            print(f"  ✅ Transaction Hash: {result.transaction_hash}")
            print("\n  📝 SAVE THIS HASH FOR YOUR HACKATHON SUBMISSION!")
        else:
            print("  ⏳ Transaction pending...")
            if result.execution_id:
                print(f"  Execution ID: {result.execution_id}")

        if result.gas_used:
            print(f"  Gas Used: {result.gas_used}")

        # Log to audit trail
        audit.log(
            AuditEventType.TRANSACTION_SENT,
            "quick_start",
            {
                "execution_id": result.execution_id,
                "status": result.status.value,
                "transaction_hash": result.transaction_hash,
                "chain": result.chain,
            },
        )

        return result.to_dict()

    except Exception as e:
        print(f"\n  ❌ Execution failed: {e}")
        print("\n  Troubleshooting:")
        print("  1. Check your KeeperHub API key is valid")
        print("  2. Verify wallet is configured in KeeperHub dashboard")
        print("  3. Check Discord: https://discord.gg/keeperhub")
        return {"error": str(e)}
    finally:
        await client.close()


async def main():
    parser = argparse.ArgumentParser(description="DeFi Sentinel - Quick Start")
    parser.add_argument("--simulate", action="store_true", help="Simulation only")
    parser.add_argument("--status", action="store_true", help="Check execution status")
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
        sys.exit(1)

    print("✅ Setup looks good!")

    # Execute transaction
    result = await execute_first_transaction(settings, simulate=args.simulate)

    # Save result
    if result:
        results_file = Path("logs/first_transaction.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        results_file.write_text(json.dumps(result, indent=2, default=str))
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
