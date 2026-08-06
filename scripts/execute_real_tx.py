#!/usr/bin/env python3
"""
DeFi Sentinel — Execute Real Onchain Transaction via KeeperHub
===============================================================

This script executes a real onchain transaction through KeeperHub's MCP server.

Usage:
    python3 scripts/execute_real_tx.py              # Execute real transaction
    python3 scripts/execute_real_tx.py --simulate   # Simulation only
    python3 scripts/execute_real_tx.py --check      # Check wallet balance

Requirements:
    - KeeperHub API key configured in .env
    - Wallet funded with testnet tokens (Base Sepolia)
    - Get testnet BASE from: https://www.base.org/sepolia-faucet
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
from src.observability.audit import AuditTrail, AuditEventType

# Wallet integration ID from KeeperHub
WALLET_ID = "q457sq2pyt2dc01g3i48j"
WALLET_ADDRESS = "0x749B59edC27F53E74fF93A6ef32a57be6E5F05f3"


async def check_wallet_balance(client: KeeperHubClient) -> dict:
    """Check wallet balance by attempting a simulation."""
    print("\nChecking wallet balance...")
    try:
        result = await client._execute_tool("execute_transfer", {
            "chain_id": "84532",
            "to_address": WALLET_ADDRESS,
            "amount": "1",  # Minimal amount to check balance
            "simulate": True,
            "integrationId": WALLET_ID,
        })
        
        text = result.get("content", [{}])[0].get("text", "")
        print(f"Balance check result: {text[:500]}")
        return result
    except Exception as e:
        print(f"Balance check error: {e}")
        return {}


async def execute_transfer(
    client: KeeperHubClient,
    to_address: str,
    amount: str,
    simulate: bool = False,
) -> ExecutionResult:
    """Execute a token transfer via KeeperHub."""
    params = {
        "chain_id": "84532",  # Base Sepolia
        "to_address": to_address,
        "amount": amount,
        "integrationId": WALLET_ID,
    }

    print(f"\nExecuting transfer: {amount} wei to {to_address}")
    print(f"  Chain: Base Sepolia (84532)")
    print(f"  From: {WALLET_ADDRESS}")
    print(f"  Simulate: {simulate}")

    try:
        result = await client._execute_tool(
            "execute_transfer",
            params,
            simulate=simulate,
        )

        # Parse result
        text = result.get("content", [{}])[0].get("text", "")
        print(f"\nResult: {text[:1000]}")

        # Try to parse as JSON
        try:
            data = json.loads(text)
            return ExecutionResult(
                execution_id=data.get("executionId", ""),
                status=ExecutionStatus(data.get("status", "pending")),
                transaction_hash=data.get("transactionHash"),
                chain=data.get("chain", "84532"),
                gas_used=data.get("gasUsed"),
                error=data.get("error"),
                result=data,
            )
        except json.JSONDecodeError:
            return ExecutionResult(
                execution_id="",
                status=ExecutionStatus.SIMULATED if simulate else ExecutionStatus.PENDING,
                error=text if "error" in text.lower() else None,
                result=result,
            )

    except Exception as e:
        print(f"Transfer failed: {e}")
        return ExecutionResult(
            execution_id="",
            status=ExecutionStatus.FAILED,
            error=str(e),
        )


async def execute_real_transaction(simulate: bool = False) -> dict:
    """Execute a real onchain transaction via KeeperHub."""
    settings = get_settings()
    client = KeeperHubClient(settings)
    audit = AuditTrail()

    print("\n" + "=" * 70)
    print("  DeFi Sentinel — Real Onchain Transaction")
    print("=" * 70)

    # Step 1: Initialize MCP session
    print("\n[1/5] Initializing KeeperHub MCP session...")
    initialized = await client.initialize()
    if not initialized:
        print("  ❌ Failed to initialize MCP session")
        return {"error": "MCP initialization failed"}
    print("  ✅ MCP session initialized")

    # Step 2: Check wallet balance
    print("\n[2/5] Checking wallet balance...")
    balance_result = await check_wallet_balance(client)

    # Step 3: Simulate transfer
    print("\n[3/5] Simulating transfer...")
    sim_result = await execute_transfer(
        client,
        to_address=WALLET_ADDRESS,  # Transfer to self for testing
        amount="1000000000000000",  # 0.001 ETH in wei
        simulate=True,
    )

    if sim_result.error and "insufficient" in sim_result.error.lower():
        print("\n  ⚠️  Wallet has insufficient balance!")
        print("  Please fund your wallet with testnet BASE tokens:")
        print("  → https://www.base.org/sepolia-faucet")
        print("  → Or use Chainlink Faucet: https://faucets.chain.link/base-sepolia")
        return {"error": "Insufficient balance", "wallet_address": WALLET_ADDRESS}

    # Step 4: Execute real transfer (if not simulating)
    if simulate:
        print("\n[4/5] Skipping real execution (simulation mode)")
        return {"mode": "simulation", "result": sim_result.to_dict()}

    print("\n[4/5] Executing REAL transfer...")
    print("  ⚠️  This will execute a real onchain transaction!")

    result = await execute_transfer(
        client,
        to_address=WALLET_ADDRESS,  # Transfer to self
        amount="1000000000000000",  # 0.001 ETH
        simulate=False,
    )

    # Step 5: Show result
    print("\n[5/5] Transaction Result")
    print("=" * 50)
    print(f"  Status: {result.status.value}")
    print(f"  Chain: {result.chain}")

    if result.transaction_hash:
        print(f"  ✅ Transaction Hash: {result.transaction_hash}")
        print(f"  🔗 Explorer: https://sepolia.basescan.org/tx/{result.transaction_hash}")
        print(f"\n  📝 SAVE THIS FOR YOUR HACKATHON SUBMISSION!")
    else:
        print(f"  ⏳ Transaction pending...")
        if result.execution_id:
            print(f"  Execution ID: {result.execution_id}")

    if result.error:
        print(f"  ❌ Error: {result.error}")

    # Log to audit trail
    audit.log(
        AuditEventType.TRANSACTION_SENT,
        "execute_real_tx",
        {
            "execution_id": result.execution_id,
            "status": result.status.value,
            "transaction_hash": result.transaction_hash,
            "chain": result.chain,
            "to_address": WALLET_ADDRESS,
            "amount": "1000000000000000",
        },
    )

    await client.close()
    return result.to_dict()


async def main():
    parser = argparse.ArgumentParser(description="DeFi Sentinel - Execute Real Transaction")
    parser.add_argument("--simulate", action="store_true", help="Simulation only")
    parser.add_argument("--check", action="store_true", help="Check wallet balance")
    args = parser.parse_args()

    settings = get_settings()
    client = KeeperHubClient(settings)

    await client.initialize()

    if args.check:
        await check_wallet_balance(client)
    else:
        result = await execute_real_transaction(simulate=args.simulate)

        # Save result
        if result:
            results_file = Path("logs/execution_result.json")
            results_file.parent.mkdir(parents=True, exist_ok=True)
            results_file.write_text(json.dumps(result, indent=2, default=str))
            print(f"\nResult saved to {results_file}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())