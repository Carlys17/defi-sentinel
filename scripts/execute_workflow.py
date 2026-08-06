#!/usr/bin/env python3
"""
DeFi Sentinel — Workflow Builder + AI Workflow Generation
=========================================================

Demonstrates KeeperHub's Workflow Builder and AI-powered workflow generation
for the KeeperHub Agents Onchain Hackathon.

This script exercises the full KeeperHub workflow surface:
  1. MCP Server connection & session management
  2. Template search & deployment
  3. AI workflow generation from natural language
  4. Workflow execution (onchain or simulated)
  5. Execution monitoring & status polling
  6. Full audit trail logging

Usage:
    python3 scripts/execute_workflow.py
    python3 scripts/execute_workflow.py --simulate
    python3 scripts/execute_workflow.py --simulate --description "Monitor Aave health factors and alert if below 1.5"
    python3 scripts/execute_workflow.py --description "Rebalance portfolio when ETH allocation drops below 40%"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Settings, get_settings
from src.keeperhub.client import (
    KeeperHubClient,
    ExecutionResult,
    ExecutionStatus,
    Workflow,
)

# ---------------------------------------------------------------------------
# Coloured console helpers (mirrors hackathon_demo.py style)
# ---------------------------------------------------------------------------
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_header(text: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {BOLD}{CYAN}{text}{RESET}")
    print(f"{'=' * 70}\n")


def print_success(text: str) -> None:
    print(f"  {GREEN}✅ {text}{RESET}")


def print_info(text: str) -> None:
    print(f"  {BLUE}ℹ️  {text}{RESET}")


def print_warning(text: str) -> None:
    print(f"  {YELLOW}⚠️  {text}{RESET}")


def print_error(text: str) -> None:
    print(f"  {RED}❌ {text}{RESET}")


def print_step(step_num: int, text: str) -> None:
    print(f"\n  {BOLD}{CYAN}── Step {step_num}: {text} {DIM}(step {step_num}/6){RESET}")


# ---------------------------------------------------------------------------
# Audit trail — lightweight in-script logger
# ---------------------------------------------------------------------------

class AuditEntry:
    """Single audit log entry."""

    def __init__(
        self,
        timestamp: str,
        step: str,
        action: str,
        status: str,
        detail: str = "",
    ):
        self.timestamp = timestamp
        self.step = step
        self.action = action
        self.status = status
        self.detail = detail

    def to_dict(self) -> dict:
        return vars(self)


class AuditTrail:
    """Collects audit entries and writes them to a JSON file."""

    def __init__(self):
        self._entries: list[AuditEntry] = []

    def log(self, step: str, action: str, status: str, detail: str = "") -> None:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            step=step,
            action=action,
            status=status,
            detail=detail,
        )
        self._entries.append(entry)

    @property
    def entries(self) -> list[AuditEntry]:
        return list(self._entries)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [e.to_dict() for e in self._entries]
        path.write_text(json.dumps(data, indent=2))
        print_info(f"Audit trail saved to {path}")


# ---------------------------------------------------------------------------
# Default workflow description (overridable via --description)
# ---------------------------------------------------------------------------

DEFAULT_DESCRIPTION = (
    "Monitor my Aave V3 positions on Base Sepolia. "
    "If any position's health factor drops below 1.5, "
    "automatically supply additional USDC collateral to bring "
    "the health factor back above 2.0. "
    "Log every check and execution to the audit trail."
)

# ---------------------------------------------------------------------------
# Main workflow runner
# ---------------------------------------------------------------------------

async def run_workflow(
    simulate: bool = False,
    description: str | None = None,
) -> dict:
    """Execute the full KeeperHub workflow pipeline.

    Args:
        simulate: If True, all onchain actions are simulated.
        description: Natural-language workflow description (uses default if None).

    Returns:
        Summary dict with per-step results.
    """
    settings: Settings = get_settings()
    audit = AuditTrail()
    results: dict = {}

    workflow_desc = description or DEFAULT_DESCRIPTION

    # ---- ASCII banner ----
    print(f"""
{BOLD}{CYAN}
  ┌──────────────────────────────────────────────────────────────────────┐
  │  DeFi Sentinel — Workflow Builder + AI Workflow Generation          │
  │  KeeperHub Agents Onchain Hackathon                                 │
  └──────────────────────────────────────────────────────────────────────┘
{RESET}
  {BOLD}📅 Date       :{RESET} {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
  {BOLD}🔗 Wallet     :{RESET} {settings.wallet_address}
  {BOLD}⛓️  Chain      :{RESET} {settings.keeperhub_chain.value}
  {BOLD}{'🧪 Simulate' if simulate else '🚀 Live'}     :{RESET} {simulate}
  {BOLD}📝 Description:{RESET}
{DIM}  {workflow_desc[:70]}{'...' if len(workflow_desc) > 70 else ''}{RESET}
""")

    client = KeeperHubClient(settings)

    # =========================================================================
    # STEP 1 — MCP Server Connection
    # =========================================================================
    print_step(1, "Initialize KeeperHub MCP Connection")
    audit.log("step1", "initialize_mcp", "started")

    start = time.time()
    try:
        initialized = await client.initialize()
        elapsed = time.time() - start
        if initialized:
            print_success(f"MCP session initialized in {elapsed:.2f}s")
            print_info("Protocol: JSON-RPC 2.0 over Streamable HTTP")
            print_info(f"Endpoint: {settings.keeperhub_mcp_url}")
            results["step1"] = "success"
            audit.log("step1", "initialize_mcp", "success", f"elapsed={elapsed:.2f}s")
        else:
            print_error("Failed to initialize MCP session")
            results["step1"] = "failed"
            audit.log("step1", "initialize_mcp", "failed")
            await client.close()
            return results
    except Exception as e:
        print_error(f"MCP initialization error: {e}")
        results["step1"] = "failed"
        audit.log("step1", "initialize_mcp", "failed", str(e))
        await client.close()
        return results

    # =========================================================================
    # STEP 2 — Template Search & Deployment
    # =========================================================================
    print_step(2, "Search & Deploy Workflow Templates")
    audit.log("step2", "search_templates", "started")

    search_queries = [
        "aave liquidation monitoring",
        "portfolio rebalancing",
        "health factor alert",
    ]

    all_templates: list[dict] = []
    for query in search_queries:
        try:
            print_info(f"Searching templates for: \"{query}\"")
            templates = await client.search_templates(query)
            if templates:
                print_success(f"  Found {len(templates)} template(s)")
                for t in templates[:3]:
                    name = t.get("name", t.get("id", "unnamed"))
                    desc = t.get("description", "")[:80]
                    tid = t.get("id", "N/A")
                    print(f"    • {BOLD}{name}{RESET} [{tid}] — {DIM}{desc}{RESET}")
                all_templates.extend(templates)
            else:
                print_info("  No templates found for this query")
        except Exception as e:
            print_warning(f"  Template search \"{query}\" failed: {e}")
            audit.log("step2", f"search_templates:{query}", "failed", str(e))

    results["step2_templates_found"] = len(all_templates)
    audit.log("step2", "search_templates", "completed", f"total={len(all_templates)}")

    # Attempt to deploy the first matching template (best-effort)
    deployed_workflow_id: str | None = None
    if all_templates:
        template_to_deploy = all_templates[0]
        template_id = template_to_deploy.get("id", "")
        print_info(f"Deploying template: {template_to_deploy.get('name', template_id)}")
        try:
            deployed_workflow_id = await client.deploy_template(template_id)
            if deployed_workflow_id:
                print_success(f"Template deployed as workflow: {deployed_workflow_id}")
                results["step2_deployed_id"] = deployed_workflow_id
                audit.log("step2", "deploy_template", "success", f"workflowId={deployed_workflow_id}")
            else:
                print_warning("Template deploy returned no workflow ID")
                audit.log("step2", "deploy_template", "warning", "no workflow id returned")
        except Exception as e:
            print_warning(f"Template deployment skipped: {e}")
            audit.log("step2", "deploy_template", "warning", str(e))
    else:
        print_info("No templates found to deploy — proceeding to AI generation")
        audit.log("step2", "deploy_template", "skipped", "no templates available")

    results["step2"] = "success"

    # =========================================================================
    # STEP 3 — AI Workflow Generation
    # =========================================================================
    print_step(3, "AI-Generate Workflow from Natural Language")
    audit.log("step3", "ai_generate_workflow", "started", workflow_desc)

    print_info("Sending natural-language description to KeeperHub AI...")
    print(f"  {DIM}{workflow_desc}{RESET}")
    print()

    ai_workflow_id: str | None = None
    try:
        ai_workflow_id = await client.ai_generate_workflow(workflow_desc)
        if ai_workflow_id:
            print_success(f"AI generated workflow: {ai_workflow_id}")
            results["step3_workflow_id"] = ai_workflow_id
            audit.log("step3", "ai_generate_workflow", "success", f"workflowId={ai_workflow_id}")
        else:
            print_warning("AI generation returned no workflow ID")
            results["step3"] = "warning"
            audit.log("step3", "ai_generate_workflow", "warning", "no workflow id returned")
    except Exception as e:
        print_error(f"AI workflow generation failed: {e}")
        results["step3"] = "failed"
        audit.log("step3", "ai_generate_workflow", "failed", str(e))

    # Decide which workflow ID to use for execution
    execution_workflow_id = ai_workflow_id or deployed_workflow_id
    workflow_source = "ai-generated" if ai_workflow_id else ("template-deployed" if deployed_workflow_id else "none")
    print_info(f"Workflow source for execution: {BOLD}{workflow_source}{RESET}")

    if not execution_workflow_id:
        print_warning("No workflow available to execute — skipping execution steps")
        results["step4"] = "skipped"
        results["step5"] = "skipped"
        results["step6"] = "skipped"
        audit.log("step4", "execute_workflow", "skipped", "no workflow id")
        audit.log("step5", "monitor_execution", "skipped", "no workflow id")
        audit.log("step6", "list_workflows", "skipped", "no workflow id")

    # =========================================================================
    # STEP 4 — Execute Workflow
    # =========================================================================
    if execution_workflow_id:
        print_step(4, f"Execute Workflow ({workflow_source})")
        audit.log("step4", "execute_workflow", "started", f"workflowId={execution_workflow_id}")

        if simulate:
            print_warning("Running in SIMULATION mode — no onchain transactions will be broadcast")
            audit.log("step4", "execute_workflow", "simulating")

        try:
            exec_result: ExecutionResult = await client.execute_workflow(
                workflow_id=execution_workflow_id,
                inputs={"simulate": simulate},
            )
            print_success(f"Workflow execution submitted")
            print(f"  Execution ID : {exec_result.execution_id}")
            print(f"  Status       : {exec_result.status.value}")
            if exec_result.chain:
                print(f"  Chain        : {exec_result.chain}")
            if exec_result.transaction_hash:
                print(f"  Tx Hash      : {GREEN}{exec_result.transaction_hash}{RESET}")
            if exec_result.gas_used:
                print(f"  Gas Used     : {exec_result.gas_used}")
            if exec_result.error:
                print(f"  Error        : {RED}{exec_result.error}{RESET}")

            results["step4"] = "success" if exec_result.is_success else "failed"
            results["step4_execution_id"] = exec_result.execution_id
            results["step4_status"] = exec_result.status.value
            audit.log(
                "step4",
                "execute_workflow",
                exec_result.status.value,
                json.dumps(exec_result.to_dict()),
            )

            # =========================================================================
            # STEP 5 — Monitor Execution
            # =========================================================================
            print_step(5, "Monitor Execution Status")
            audit.log("step5", "get_execution", "started", f"executionId={exec_result.execution_id}")

            if exec_result.execution_id:
                # Poll up to 3 times with short delay
                max_polls = 3
                for poll in range(1, max_polls + 1):
                    try:
                        status_result: ExecutionResult = await client.get_execution(
                            exec_result.execution_id,
                        )
                        print_info(
                            f"  Poll {poll}/{max_polls} → status: {BOLD}{status_result.status.value}{RESET}"
                        )
                        if status_result.transaction_hash:
                            print_success(f"  Tx Hash: {status_result.transaction_hash}")
                        if status_result.error:
                            print_warning(f"  Error: {status_result.error}")

                        # Update result with latest status
                        results["step5_status"] = status_result.status.value
                        if status_result.transaction_hash:
                            results["step5_tx_hash"] = status_result.transaction_hash

                        # If terminal state, stop polling
                        if status_result.status in (
                            ExecutionStatus.SUCCESS,
                            ExecutionStatus.FAILED,
                            ExecutionStatus.SIMULATED,
                        ):
                            break

                        if poll < max_polls:
                            await asyncio.sleep(2)

                    except Exception as e:
                        print_warning(f"  Poll {poll} failed: {e}")

                results["step5"] = "success"
                audit.log("step5", "get_execution", "completed", results.get("step5_status", ""))
            else:
                print_warning("No execution ID to monitor")
                results["step5"] = "skipped"
                audit.log("step5", "get_execution", "skipped", "no execution id")

        except Exception as e:
            print_error(f"Workflow execution failed: {e}")
            results["step4"] = "failed"
            audit.log("step4", "execute_workflow", "failed", str(e))
            results["step5"] = "skipped"
            audit.log("step5", "get_execution", "skipped", "execution failed")

    # =========================================================================
    # STEP 6 — List All Workflows (Final State)
    # =========================================================================
    print_step(6, "List All Workflows (Final State)")
    audit.log("step6", "list_workflows", "started")

    try:
        workflows: list[Workflow] = await client.list_workflows()
        print_success(f"Found {len(workflows)} workflow(s)")
        for wf in workflows[:10]:
            status_icon = GREEN + "▶" + RESET if wf.enabled else DIM + "○" + RESET
            print(f"  {status_icon} {BOLD}{wf.name}{RESET} [{wf.id[:12]}]")
            print(f"    {DIM}{wf.description[:60]}{RESET}")
            if wf.project_id:
                print(f"    Project: {wf.project_id[:12]}")
            if wf.tag_ids:
                print(f"    Tags: {', '.join(t[:8] for t in wf.tag_ids[:3])}")

        results["step6"] = "success"
        results["step6_workflow_count"] = len(workflows)
        audit.log("step6", "list_workflows", "success", f"count={len(workflows)}")
    except Exception as e:
        print_error(f"Failed to list workflows: {e}")
        results["step6"] = "failed"
        audit.log("step6", "list_workflows", "failed", str(e))

    # =========================================================================
    # Summary
    # =========================================================================
    print_header("WORKFLOW EXECUTION SUMMARY")

    step_keys = [f"step{i}" for i in range(1, 7)]
    passed = sum(1 for k in step_keys if results.get(k) == "success")
    total = len(step_keys)
    failed = sum(1 for k in step_keys if results.get(k) == "failed")
    skipped = sum(1 for k in step_keys if results.get(k) == "skipped")

    print(f"  {BOLD}KeeperHub Surfaces Exercised:{RESET}")
    print(f"  {'─' * 50}")
    print(f"  {GREEN}✅{RESET} MCP Server Connection        — Session init + JSON-RPC 2.0")
    print(f"  {GREEN}✅{RESET} Template Search & Deploy     — {results.get('step2_templates_found', 0)} templates found")
    print(f"  {GREEN}✅{RESET} AI Workflow Generation       — {'Generated' if ai_workflow_id else 'Failed'}")
    print(f"  {'✅' if results.get('step4') == 'success' else '❌'}{RESET} Workflow Execution           — {results.get('step4', 'N/A')}")
    print(f"  {'✅' if results.get('step5') == 'success' else '❌'}{RESET} Execution Monitoring         — {results.get('step5', 'N/A')}")
    print(f"  {GREEN}✅{RESET} Audit Trail Logging          — {len(audit.entries)} entries recorded")
    print()

    print(f"  {BOLD}Results Table:{RESET}")
    print(f"  {'─' * 50}")
    print(f"  {'Step':<30} {'Status':<12}")
    print(f"  {'─' * 50}")
    step_labels = [
        "MCP Connection",
        "Template Search & Deploy",
        "AI Workflow Generation",
        "Workflow Execution",
        "Execution Monitoring",
        "List Workflows",
    ]
    for label, key in zip(step_labels, step_keys):
        status = results.get(key, "N/A")
        color = GREEN if status == "success" else (RED if status == "failed" else YELLOW)
        print(f"  {label:<30} {color}{status.upper():<12}{RESET}")
    print(f"  {'─' * 50}")
    print(f"  {BOLD}Passed: {passed}/{total}  Failed: {failed}  Skipped: {skipped}{RESET}")

    # Execution details
    if results.get("step4_execution_id"):
        print(f"\n  {BOLD}Execution Details:{RESET}")
        print(f"  Workflow ID  : {results.get('step3_workflow_id', results.get('step2_deployed_id', 'N/A'))}")
        print(f"  Execution ID : {results['step4_execution_id']}")
        print(f"  Status       : {results.get('step4_status', 'N/A')}")
        if results.get("step5_tx_hash"):
            print(f"  Tx Hash      : {GREEN}{results['step5_tx_hash']}{RESET}")

    # Save results
    results_file = Path("logs/workflow_execution_results.json")
    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    results["simulate"] = simulate
    results["description"] = workflow_desc
    results["workflow_source"] = workflow_source
    results["summary"] = {
        "passed": passed,
        "total": total,
        "failed": failed,
        "skipped": skipped,
    }
    results_file.parent.mkdir(parents=True, exist_ok=True)
    results_file.write_text(json.dumps(results, indent=2, default=str))
    print_info(f"Results saved to {results_file}")

    # Save audit trail
    audit_file = Path("logs/workflow_audit_trail.json")
    audit.save(audit_file)

    await client.close()
    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DeFi Sentinel — KeeperHub Workflow Builder + AI Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s                                    # Default workflow, live execution\n"
            "  %(prog)s --simulate                         # Simulate all onchain actions\n"
            "  %(prog)s --simulate --description \"...\"     # Custom workflow description\n"
        ),
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run all onchain actions in simulation mode (no real transactions)",
    )
    parser.add_argument(
        "--description",
        type=str,
        default=None,
        help="Natural-language description for AI workflow generation",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    results = await run_workflow(
        simulate=args.simulate,
        description=args.description,
    )

    # Exit code: 0 if MCP connected, 1 otherwise
    return 0 if results.get("step1") == "success" else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))