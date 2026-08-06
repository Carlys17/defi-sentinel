"""KeeperHub MCP client for DeFi Sentinel.

Provides async HTTP client for KeeperHub's MCP server with:
- Workflow management (list, create, execute, monitor)
- Direct onchain execution (transfer, contract call, check-and-execute)
- DeFi protocol actions (Aave, Compound, Morpho, Yearn, etc.)
- AI-assisted workflow generation
- x402/MPP payment support
- Built-in retry logic with exponential backoff
- Idempotency key generation for retry-safe execution
- MCP session management (initialize → notifications/initialized → tools)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from enum import StrEnum

import httpx

from config.settings import Settings

logger = logging.getLogger(__name__)


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SIMULATED = "simulated"


@dataclass
class Workflow:
    id: str
    name: str
    description: str
    enabled: bool = True
    project_id: str | None = None
    tag_ids: list[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    execution_id: str
    status: ExecutionStatus
    transaction_hash: str | None = None
    chain: str | None = None
    gas_used: int | None = None
    error: str | None = None
    result: dict | None = None

    @property
    def is_success(self) -> bool:
        return self.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SIMULATED)

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "status": self.status.value,
            "transaction_hash": self.transaction_hash,
            "chain": self.chain,
            "gas_used": self.gas_used,
            "error": self.error,
            "result": self.result,
        }


class KeeperHubClient:
    """Async HTTP client for KeeperHub MCP server.

    Implements the MCP protocol with proper session management:
    1. Initialize session
    2. Send notifications/initialized
    3. Execute tools via tools/call
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._session_id: str | None = None
        self._initialized = False
        self._retry_count = 3
        self._retry_delay = 2.0

        self._client = httpx.AsyncClient(
            base_url=settings.keeperhub_mcp_url.rstrip("/"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.keeperhub_api_key}",
            },
            timeout=30.0,
            follow_redirects=False,
        )

    @property
    def is_configured(self) -> bool:
        return self._settings.is_keeperhub_configured()

    async def initialize(self) -> bool:
        """Initialize MCP session.

        Must be called before any tool execution.
        Returns True if session is initialized.
        """
        if self._initialized:
            return True

        try:
            # Step 1: Initialize
            response = await self._client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "defi-sentinel",
                            "version": "1.0.0",
                        },
                    },
                },
            )
            response.raise_for_status()
            response.json()

            # Get session ID from response header
            self._session_id = response.headers.get("mcp-session-id")
            if self._session_id:
                self._client.headers["mcp-session-id"] = self._session_id

            # Step 2: Send notifications/initialized
            await self._client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                },
            )

            self._initialized = True
            logger.info("KeeperHub MCP session initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MCP session: {e}")
            return False

    async def _ensure_initialized(self) -> None:
        """Ensure MCP session is initialized before tool execution."""
        if not self._initialized:
            success = await self.initialize()
            if not success:
                raise Exception("Failed to initialize KeeperHub MCP session")

    async def _execute_tool(
        self,
        tool_name: str,
        params: dict,
        simulate: bool = False,
        idempotency_key: str | None = None,
    ) -> dict:
        """Execute an MCP tool via KeeperHub's HTTP endpoint.

        Uses JSON-RPC 2.0 over streamable HTTP as per KeeperHub docs.

        Args:
            tool_name: MCP tool name (e.g. 'execute_transfer')
            params: Tool parameters
            simulate: If True, simulate without broadcasting
            idempotency_key: Key for retry-safe execution

        Returns:
            Tool response as dict

        Raises:
            httpx.HTTPStatusError: On HTTP errors
            Exception: On tool execution errors
        """
        await self._ensure_initialized()

        request_body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params,
            },
        }
        if simulate:
            request_body["params"]["arguments"]["simulate"] = True
        if idempotency_key:
            request_body["params"]["arguments"]["idempotency_key"] = idempotency_key

        for attempt in range(1, self._retry_count + 1):
            try:
                logger.debug(
                    f"Executing tool '{tool_name}' (attempt {attempt}/{self._retry_count})"
                )
                response = await self._client.post("/mcp", json=request_body)
                response.raise_for_status()
                result = response.json()

                # Handle MCP error format
                if "error" in result:
                    error_msg = result["error"].get("message", "Unknown MCP error")
                    logger.error(f"Tool '{tool_name}' failed: {error_msg}")
                    raise Exception(error_msg)

                # Handle content format from MCP
                content = result.get("content", [])
                if content and isinstance(content, list):
                    for item in content:
                        if item.get("type") == "text":
                            try:
                                return json.loads(item["text"])
                            except json.JSONDecodeError:
                                return {"text": item["text"]}

                return result.get("result", {})

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 429:
                    wait_time = self._retry_delay * (2**attempt)
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                elif status == 402:
                    # Payment required - x402/MPP challenge
                    logger.info("402 challenge received - agentic wallet will handle payment")
                    try:
                        challenge = e.response.json()
                        logger.info(f"x402 challenge: {challenge}")
                    except Exception:
                        pass
                    raise
                elif status == 401:
                    logger.error("Authentication failed - check your API key")
                    raise
                elif attempt == self._retry_count:
                    raise
                await asyncio.sleep(self._retry_delay)
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt == self._retry_count:
                    raise
                wait_time = self._retry_delay * (2**attempt)
                logger.warning(f"Connection error, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)

        raise Exception(f"Tool '{tool_name}' failed after {self._retry_count} retries")

    def _generate_idempotency_key(self, tool_name: str, params: dict) -> str:
        """Generate a deterministic idempotency key for retry-safe execution.

        Keys must be stable for identical arguments so that a retry of the
        same operation is deduplicated by KeeperHub instead of double-spending.
        """
        payload = json.dumps(
            {"tool": tool_name, "params": params},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    async def health_check(self) -> bool:
        """Check if KeeperHub MCP server is reachable."""
        try:
            initialized = await self.initialize()
            return initialized
        except Exception:
            return False

    # ---- Workflow Management ----

    async def list_workflows(self, project_id: str | None = None) -> list[Workflow]:
        """List all workflows, optionally filtered by project."""
        params = {"projectId": project_id} if project_id else {}
        result = await self._execute_tool("list_workflows", params)
        workflows = result.get("workflows", [])
        return [
            Workflow(
                id=wf.get("id", ""),
                name=wf.get("name", ""),
                description=wf.get("description", ""),
                enabled=wf.get("enabled", True),
                project_id=wf.get("projectId"),
                tag_ids=wf.get("tagIds", []),
            )
            for wf in workflows
        ]

    async def get_workflow(self, workflow_id: str) -> dict:
        """Get a single workflow by ID."""
        return await self._execute_tool("get_workflow", {"workflowId": workflow_id})

    async def create_workflow(
        self,
        name: str,
        description: str,
        nodes: list[dict],
        edges: list[dict],
        enabled: bool = False,
    ) -> str:
        """Create a workflow with nodes and edges."""
        result = await self._execute_tool(
            "create_workflow",
            {
                "name": name,
                "description": description,
                "nodes": nodes,
                "edges": edges,
                "enabled": enabled,
            },
        )
        return result.get("workflowId", "")

    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: dict | None = None,
    ) -> ExecutionResult:
        """Execute a workflow and return execution result."""
        result = await self._execute_tool(
            "execute_workflow",
            {"workflowId": workflow_id, "inputs": inputs or {}},
        )
        return ExecutionResult(
            execution_id=result.get("executionId", ""),
            status=ExecutionStatus(result.get("status", "pending")),
            transaction_hash=result.get("transactionHash"),
            chain=result.get("chain"),
            gas_used=result.get("gasUsed"),
            error=result.get("error"),
            result=result,
        )

    async def get_execution(self, execution_id: str) -> ExecutionResult:
        """Get execution status and logs."""
        result = await self._execute_tool("get_execution", {"executionId": execution_id})
        return ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus(result.get("status", "pending")),
            transaction_hash=result.get("transactionHash"),
            chain=result.get("chain"),
            gas_used=result.get("gasUsed"),
            error=result.get("error"),
            result=result,
        )

    async def wait_for_execution(
        self,
        execution_id: str,
        timeout: float = 120.0,
        poll_interval: float = 5.0,
    ) -> ExecutionResult:
        """Poll an execution until it reaches a terminal state.

        Used after broadcasting a transaction so the agent observes the
        final outcome (completed / failed) instead of a raw ``pending``.

        Args:
            execution_id: Execution ID to poll.
            timeout: Maximum total wait time in seconds.
            poll_interval: Delay between status polls in seconds.

        Returns:
            The terminal ExecutionResult.
        """
        deadline = asyncio.get_event_loop().time() + timeout
        while True:
            result = await self.get_execution(execution_id)
            if result.status in (ExecutionStatus.SUCCESS, ExecutionStatus.FAILED):
                return result
            if asyncio.get_event_loop().time() >= deadline:
                logger.warning(
                    f"Execution {execution_id} did not reach terminal state "
                    f"within {timeout}s (last status: {result.status.value})"
                )
                return result
            await asyncio.sleep(poll_interval)

    async def ai_generate_workflow(self, description: str) -> str:
        """Generate a workflow from natural language description."""
        result = await self._execute_tool(
            "ai_generate_workflow",
            {"description": description},
        )
        return result.get("workflowId", "")

    # ---- Direct Onchain Execution ----

    async def get_direct_execution_status(self, execution_id: str) -> dict:
        """Get status of a direct execution (transfer or contract call)."""
        return await self._execute_tool(
            "get_direct_execution_status",
            {"execution_id": execution_id},
        )

    async def execute_transfer(
        self,
        to_address: str,
        amount: str,
        token_address: str | None = None,
        simulate: bool = False,
    ) -> ExecutionResult:
        """Execute a token transfer via KeeperHub.

        Args:
            to_address: Recipient address
            amount: Amount in wei (as string)
            token_address: ERC20 token address (None for native token)
            simulate: If True, simulate without broadcasting

        Returns:
            ExecutionResult with status and transaction hash
        """
        params = {
            "chain_id": self._settings.keeperhub_chain.value,
            "to_address": to_address,
            "amount": amount,
        }
        if token_address:
            params["token_address"] = token_address

        idempotency_key = self._generate_idempotency_key("execute_transfer", params)
        result = await self._execute_tool(
            "execute_transfer",
            params,
            simulate=simulate,
            idempotency_key=idempotency_key if not simulate else None,
        )

        return ExecutionResult(
            execution_id=result.get("executionId", result.get("execution_id", "")),
            status=ExecutionStatus(result.get("status", "simulated" if simulate else "pending")),
            transaction_hash=result.get("transactionHash", result.get("transaction_hash")),
            chain=result.get("chain"),
            gas_used=result.get("gasUsed", result.get("gas_used")),
            error=result.get("error"),
            result=result,
        )

    async def execute_contract_call(
        self,
        contract_address: str,
        data: str,
        value: str = "0",
        simulate: bool = False,
    ) -> ExecutionResult:
        """Execute a contract call via KeeperHub."""
        params = {
            "chain_id": self._settings.keeperhub_chain.value,
            "contract_address": contract_address,
            "data": data,
            "value": value,
        }

        idempotency_key = self._generate_idempotency_key("execute_contract_call", params)
        result = await self._execute_tool(
            "execute_contract_call",
            params,
            simulate=simulate,
            idempotency_key=idempotency_key if not simulate else None,
        )

        return ExecutionResult(
            execution_id=result.get("executionId", result.get("execution_id", "")),
            status=ExecutionStatus(result.get("status", "simulated" if simulate else "pending")),
            transaction_hash=result.get("transactionHash", result.get("transaction_hash")),
            chain=result.get("chain"),
            gas_used=result.get("gasUsed", result.get("gas_used")),
            error=result.get("error"),
            result=result,
        )

    async def execute_check_and_execute(
        self,
        read_condition: dict,
        execute_action: dict,
    ) -> ExecutionResult:
        """Execute a conditional transaction."""
        params = {
            "read_condition": read_condition,
            "execute_action": execute_action,
        }
        result = await self._execute_tool("execute_check_and_execute", params)

        return ExecutionResult(
            execution_id=result.get("executionId", result.get("execution_id", "")),
            status=ExecutionStatus(result.get("status", "pending")),
            transaction_hash=result.get("transactionHash", result.get("transaction_hash")),
            chain=result.get("chain"),
            gas_used=result.get("gasUsed", result.get("gas_used")),
            error=result.get("error"),
            result=result,
        )

    # ---- Protocol Actions ----

    async def search_protocol_actions(
        self,
        protocol: str | None = None,
        action_type: str | None = None,
    ) -> list[dict]:
        """Search for available DeFi protocol actions."""
        params = {}
        if protocol:
            params["protocol"] = protocol
        if action_type:
            params["actionType"] = action_type

        result = await self._execute_tool("search_protocol_actions", params)
        return result.get("actions", [])

    async def execute_protocol_action(
        self,
        protocol: str,
        action: str,
        params: dict,
        simulate: bool = False,
    ) -> ExecutionResult:
        """Execute a DeFi protocol action.

        Args:
            protocol: Protocol name (e.g. 'aave-v3')
            action: Action slug (e.g. 'supply')
            params: Action parameters
            simulate: If True, simulate without broadcasting
        """
        action_params = {
            "actionType": f"{protocol}/{action}",
            **params,
        }

        idempotency_key = self._generate_idempotency_key("execute_protocol_action", action_params)
        result = await self._execute_tool(
            "execute_protocol_action",
            action_params,
            simulate=simulate,
            idempotency_key=idempotency_key if not simulate else None,
        )

        return ExecutionResult(
            execution_id=result.get("executionId", result.get("execution_id", "")),
            status=ExecutionStatus(result.get("status", "simulated" if simulate else "pending")),
            transaction_hash=result.get("transactionHash", result.get("transaction_hash")),
            chain=result.get("chain"),
            gas_used=result.get("gasUsed", result.get("gas_used")),
            error=result.get("error"),
            result=result,
        )

    # ---- Chains & Action Schemas ----

    async def list_chains(self) -> list[dict]:
        """List supported blockchain networks."""
        result = await self._execute_tool("list_chains", {})
        return result.get("chains", [])

    async def get_chain(self, chain_id: str) -> dict:
        """Get details for a specific chain."""
        return await self._execute_tool("get_chain", {"chain_id": chain_id})

    async def list_action_schemas(self) -> list[dict]:
        """List available action schemas, triggers, supported chains."""
        return await self._execute_tool("list_action_schemas", {})

    # ---- Templates ----

    async def search_templates(self, query: str) -> list[dict]:
        """Search pre-built workflow templates."""
        result = await self._execute_tool("search_templates", {"query": query})
        return result.get("templates", [])

    async def deploy_template(self, template_id: str) -> str:
        """Clone a public template into the org as a new workflow."""
        result = await self._execute_tool("deploy_template", {"template_id": template_id})
        return result.get("workflow_id", "")

    async def tools_documentation(self) -> dict:
        """Get documentation for all KeeperHub MCP tools with examples."""
        return await self._execute_tool("tools_documentation", {})

    # ---- Marketplace ----

    async def search_workflows(self, query: str) -> list[dict]:
        """Search listed workflows callable by external agents."""
        result = await self._execute_tool("search_workflows", {"query": query})
        return result.get("workflows", [])

    async def call_workflow(self, slug: str, inputs: dict) -> dict:
        """Invoke a listed workflow by slug."""
        return await self._execute_tool("call_workflow", {"slug": slug, "inputs": inputs})

    # ---- Integrations ----

    async def list_integrations(self) -> list[str]:
        """List configured integrations for the org."""
        result = await self._execute_tool("list_integrations", {})
        return result.get("integrations", [])

    async def get_wallet_integration(self) -> dict:
        """Get wallet integration details."""
        return await self._execute_tool("get_wallet_integration", {})

    # ---- Projects & Tags ----

    async def list_projects(self) -> list[dict]:
        """List workflow projects."""
        result = await self._execute_tool("list_projects", {})
        return result.get("projects", [])

    async def create_project(self, name: str, description: str = "") -> str:
        """Create a new workflow project."""
        result = await self._execute_tool(
            "create_project",
            {"name": name, "description": description},
        )
        return result.get("projectId", "")

    async def list_tags(self) -> list[dict]:
        """List workflow tags."""
        result = await self._execute_tool("list_tags", {})
        return result.get("tags", [])

    async def create_tag(self, name: str, color: str = "#FF0000") -> str:
        """Create a new workflow tag."""
        result = await self._execute_tool("create_tag", {"name": name, "color": color})
        return result.get("tagId", "")

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
