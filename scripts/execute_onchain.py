#!/usr/bin/env python3
"""
DeFi Sentinel — Real Onchain Execution via KeeperHub
=====================================================

This script executes REAL onchain transactions through KeeperHub's MCP server.
It is the core execution flow that proves our agent can transact onchain.

Usage:
    python scripts/execute_onchain.py              # Full execution flow
    python scripts/execute_onchain.py --simulate   # Simulation only (no broadcast)
    python scripts/execute_onchain.py --transfer   # Execute a token transfer
    python scripts/execute_onchain.py --status     # Check execution status

Requirements:
    - KeeperHub API key in .env (KEEPERHUB_API_KEY)
    - Wallet configured (KEEPERHUB_CHAIN, WALLET_ADDRESS)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Settings, get_settings
from src.keeperhub.client import ExecutionResult, KeeperHubClient
from src.observability.audit import AuditEventType, AuditTrail
from src.utils.helpers import now_iso

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class OnchainExecutor:
    """Handles real onchain execution via KeeperHub."""

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._keeperhub = KeeperHubClient(self._settings)
        self._audit = AuditTrail()
        self._results: list[dict] = []

    @property
    def results(self) -> list[dict]:
        return self._results

    async def initialize(self) -> bool:
        """Initialize connections and verify setup."""
        logger.info("Initializing OnchainExecutor...")

        # Check KeeperHub connection
        health = await self._keeperhub.health_check()
        if not health:
            logger.warning("KeeperHub health check failed - will try direct execution")

        # List available workflows
        try:
            workflows = await self._keeperhub.list_workflows()
            logger.info(f"Available workflows: {len(workflows)}")
            for wf in workflows[:5]:
                logger.info(f"  - {wf.name}: {wf.description[:80]}")
        except Exception as e:
            logger.warning(f"Could not list workflows: {e}")

        # List integrations
        try:
            integrations = await self._keeperhub.list_integrations()
            logger.info(f"Configured integrations: {len(integrations)}")
            for integration in integrations:
                logger.info(f"  - {integration}")
        except Exception as e:
            logger.warning(f"Could not list integrations: {e}")

        # Get wallet info
        try:
            wallet = await self._keeperhub.get_wallet_integration()
            logger.info(f"Wallet: {wallet}")
        except Exception as e:
            logger.warning(f"Could not get wallet info: {e}")

        # Search for protocol actions
        try:
            actions = await self._keeperhub.search_protocol_actions(protocol="aave-v3")
            logger.info(f"Aave v3 actions: {len(actions)}")
            for action in actions[:3]:
                logger.info(f"  - {action}")
        except Exception as e:
            logger.warning(f"Could not search protocol actions: {e}")

        self._audit.log(
            AuditEventType.AGENT_STARTED,
            "onchain_executor",
            {
                "chain": self._settings.keeperhub_chain.value,
                "keeperhub_configured": self._settings.is_keeperhub_configured(),
            },
        )

        logger.info("OnchainExecutor initialized")
        return True

    async def execute_transfer(
        self,
        to_address: str,
        amount: str,
        token_address: str | None = None,
        simulate: bool = False,
    ) -> ExecutionResult:
        """Execute a token transfer via KeeperHub."""
        logger.info(f"Executing transfer: {amount} to {to_address}")
        if token_address:
            logger.info(f"Token: {token_address}")

        self._audit.log(
            AuditEventType.TRANSACTION_SENT,
            "onchain_executor",
            {
                "type": "transfer",
                "to": to_address,
                "amount": amount,
                "token": token_address or "native",
                "simulate": simulate,
                "timestamp": now_iso(),
            },
        )

        try:
            result = await self._keeperhub.execute_transfer(
                to_address=to_address,
                amount=amount,
                token_address=token_address,
                simulate=simulate,
            )

            if not simulate and result.execution_id:
                logger.info(f"Transfer broadcast, polling execution {result.execution_id}...")
                result = await self._keeperhub.wait_for_execution(result.execution_id)

            self._audit.log(
                AuditEventType.TRANSACTION_CONFIRMED
                if result.is_success
                else AuditEventType.TRANSACTION_FAILED,
                "onchain_executor",
                {
                    "execution_id": result.execution_id,
                    "status": result.status.value,
                    "transaction_hash": result.transaction_hash,
                    "chain": result.chain,
                    "gas_used": result.gas_used,
                    "error": result.error,
                },
            )

            self._results.append(result.to_dict())
            return result

        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            self._audit.log(
                AuditEventType.TRANSACTION_FAILED,
                "onchain_executor",
                {"error": str(e)},
            )
            raise

    async def execute_contract_call(
        self,
        contract_address: str,
        data: str,
        value: str = "0",
        simulate: bool = False,
    ) -> ExecutionResult:
        """Execute a contract call via KeeperHub."""
        logger.info(f"Executing contract call: {contract_address}")

        self._audit.log(
            AuditEventType.TRANSACTION_SENT,
            "onchain_executor",
            {
                "type": "contract_call",
                "contract": contract_address,
                "data": data[:100],
                "value": value,
                "simulate": simulate,
                "timestamp": now_iso(),
            },
        )

        try:
            result = await self._keeperhub.execute_contract_call(
                contract_address=contract_address,
                data=data,
                value=value,
                simulate=simulate,
            )

            if not simulate and result.execution_id:
                logger.info(f"Contract call broadcast, polling execution {result.execution_id}...")
                result = await self._keeperhub.wait_for_execution(result.execution_id)

            self._audit.log(
                AuditEventType.TRANSACTION_CONFIRMED
                if result.is_success
                else AuditEventType.TRANSACTION_FAILED,
                "onchain_executor",
                {
                    "execution_id": result.execution_id,
                    "status": result.status.value,
                    "transaction_hash": result.transaction_hash,
                    "chain": result.chain,
                },
            )

            self._results.append(result.to_dict())
            return result

        except Exception as e:
            logger.error(f"Contract call failed: {e}")
            self._audit.log(
                AuditEventType.TRANSACTION_FAILED,
                "onchain_executor",
                {"error": str(e)},
            )
            raise

    async def execute_protocol_action(
        self,
        protocol: str,
        action: str,
        params: dict,
        simulate: bool = False,
    ) -> ExecutionResult:
        """Execute a DeFi protocol action via KeeperHub."""
        logger.info(f"Executing {protocol} {action}: {params}")

        self._audit.log(
            AuditEventType.TRANSACTION_SENT,
            "onchain_executor",
            {
                "type": "protocol_action",
                "protocol": protocol,
                "action": action,
                "params": params,
                "simulate": simulate,
                "timestamp": now_iso(),
            },
        )

        try:
            result = await self._keeperhub.execute_protocol_action(
                protocol=protocol,
                action=action,
                params=params,
                simulate=simulate,
            )

            if not simulate and result.execution_id:
                logger.info(
                    f"Protocol action broadcast, polling execution {result.execution_id}..."
                )
                result = await self._keeperhub.wait_for_execution(result.execution_id)

            self._audit.log(
                AuditEventType.TRANSACTION_CONFIRMED
                if result.is_success
                else AuditEventType.TRANSACTION_FAILED,
                "onchain_executor",
                {
                    "execution_id": result.execution_id,
                    "status": result.status.value,
                    "transaction_hash": result.transaction_hash,
                    "chain": result.chain,
                },
            )

            self._results.append(result.to_dict())
            return result

        except Exception as e:
            logger.error(f"Protocol action failed: {e}")
            self._audit.log(
                AuditEventType.TRANSACTION_FAILED,
                "onchain_executor",
                {"error": str(e)},
            )
            raise

    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: dict | None = None,
    ) -> ExecutionResult:
        """Execute a KeeperHub workflow."""
        logger.info(f"Executing workflow: {workflow_id}")

        try:
            result = await self._keeperhub.execute_workflow(
                workflow_id=workflow_id,
                inputs=inputs,
            )

            if result.execution_id:
                logger.info(f"Workflow broadcast, polling execution {result.execution_id}...")
                result = await self._keeperhub.wait_for_execution(result.execution_id)

            self._results.append(result.to_dict())
            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise

    async def check_and_execute(
        self,
        read_condition: dict,
        execute_action: dict,
    ) -> ExecutionResult:
        """Execute a conditional transaction."""
        logger.info("Executing check-and-execute")

        try:
            result = await self._keeperhub.execute_check_and_execute(
                read_condition=read_condition,
                execute_action=execute_action,
            )

            if result.execution_id:
                logger.info(
                    f"Check-and-execute broadcast, polling execution {result.execution_id}..."
                )
                result = await self._keeperhub.wait_for_execution(result.execution_id)

            self._results.append(result.to_dict())
            return result

        except Exception as e:
            logger.error(f"Check-and-execute failed: {e}")
            raise

    def get_summary(self) -> dict:
        """Get execution summary."""
        return {
            "total_executions": len(self._results),
            "successful": sum(1 for r in self._results if r.get("status") == "success"),
            "failed": sum(1 for r in self._results if r.get("status") == "failed"),
            "pending": sum(1 for r in self._results if r.get("status") == "pending"),
            "simulated": sum(1 for r in self._results if r.get("status") == "simulated"),
            "results": self._results,
            "audit_summary": self._audit.get_summary(),
        }

    async def close(self):
        """Close connections."""
        await self._keeperhub.close()


async def main():
    parser = argparse.ArgumentParser(description="DeFi Sentinel - Real Onchain Execution")
    parser.add_argument("--simulate", action="store_true", help="Simulation mode (no broadcast)")
    parser.add_argument("--transfer", action="store_true", help="Execute a test transfer")
    parser.add_argument("--status", action="store_true", help="Check execution status")
    parser.add_argument("--execution-id", type=str, help="Check status of specific execution")
    parser.add_argument("--to", type=str, help="Recipient address for transfer")
    parser.add_argument("--amount", type=str, help="Amount to transfer (wei)")
    parser.add_argument(
        "--token", type=str, help="Token address (ERC20) or 'native' for native token"
    )
    args = parser.parse_args()

    settings = get_settings()

    # Validate configuration
    if not settings.is_keeperhub_configured():
        logger.error("KeeperHub not configured. Set KEEPERHUB_API_KEY in .env")
        sys.exit(1)

    executor = OnchainExecutor(settings)

    try:
        await executor.initialize()

        if args.status:
            if args.execution_id:
                result = await executor._keeperhub.get_execution(args.execution_id)
                print(json.dumps(result.to_dict(), indent=2))
            else:
                summary = executor.get_summary()
                print(json.dumps(summary, indent=2))
            return

        if args.transfer:
            to_address = args.to or settings.wallet_address
            amount = args.amount or "1000000000000000"  # 0.001 ETH in wei
            token = args.token

            if not to_address:
                logger.error("--to address required for transfer")
                sys.exit(1)

            result = await executor.execute_transfer(
                to_address=to_address,
                amount=amount,
                token_address=token if token and token != "native" else None,
                simulate=args.simulate,
            )

            print("\n" + "=" * 60)
            print("TRANSFER RESULT")
            print("=" * 60)
            print(json.dumps(result.to_dict(), indent=2))

            if result.transaction_hash:
                print(f"\n✅ Transaction Hash: {result.transaction_hash}")
                print(f"   Chain: {result.chain}")
                print(f"   Status: {result.status.value}")

            return

        # Default: Run full execution demo
        print("\n" + "=" * 60)
        print("DeFi Sentinel - Onchain Execution Demo")
        print("=" * 60)

        # Step 1: List available workflows
        print("\n[1/5] Listing available workflows...")
        try:
            workflows = await executor._keeperhub.list_workflows()
            print(f"  Found {len(workflows)} workflows")
            for wf in workflows[:3]:
                print(f"  - {wf.name}: {wf.description[:60]}")
        except Exception as e:
            print(f"  Error: {e}")

        # Step 2: Search protocol actions
        print("\n[2/5] Searching protocol actions...")
        try:
            actions = await executor._keeperhub.search_protocol_actions(protocol="aave-v3")
            print(f"  Found {len(actions)} Aave v3 actions")
            for action in actions[:3]:
                print(f"  - {action}")
        except Exception as e:
            print(f"  Error: {e}")

        # Step 3: Execute a test transfer (simulation)
        print("\n[3/5] Executing test transfer (simulation)...")
        try:
            result = await executor.execute_transfer(
                to_address=settings.wallet_address or "0x0000000000000000000000000000000000000000",
                amount="1000000000000000",  # 0.001 ETH
                simulate=True,
            )
            print(f"  Status: {result.status.value}")
            print(f"  Gas estimate: {result.gas_used}")
        except Exception as e:
            print(f"  Error: {e}")

        # Step 4: Execute real transfer (if not simulating)
        if not args.simulate:
            print("\n[4/5] Executing real transfer...")
            try:
                result = await executor.execute_transfer(
                    to_address=settings.wallet_address
                    or "0x0000000000000000000000000000000000000000",
                    amount="1000000000000000",  # 0.001 ETH
                    simulate=False,
                )
                print(f"  Status: {result.status.value}")
                if result.transaction_hash:
                    print(f"  Transaction Hash: {result.transaction_hash}")
                    print(f"  Chain: {result.chain}")
            except Exception as e:
                print(f"  Error: {e}")
        else:
            print("\n[4/5] Skipping real execution (simulation mode)")

        # Step 5: Show summary
        print("\n[5/5] Execution Summary")
        summary = executor.get_summary()
        print(json.dumps(summary, indent=2))

        # Save results to file
        results_file = Path("logs/execution_results.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        results_file.write_text(json.dumps(summary, indent=2))
        print(f"\nResults saved to {results_file}")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await executor.close()


if __name__ == "__main__":
    asyncio.run(main())
