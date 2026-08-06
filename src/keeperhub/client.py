"""KeeperHub MCP Server client for DeFi Sentinel.

Provides a high-level interface to KeeperHub's MCP tools for:
- Workflow management (create, execute, monitor)
- Direct onchain execution (transfers, contract calls)
- DeFi protocol actions (Aave, Uniswap, etc.)
- AI-assisted workflow generation
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import httpx

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SIMULATED = "simulated"


@dataclass
class ExecutionResult:
    """Result of a KeeperHub workflow or transaction execution."""
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    transaction_hash: Optional[str] = None
    chain: str = ""
    gas_used: Optional[int] = None
    gas_price_gwei: Optional[float] = None
    error: Optional[str] = None
    logs: list[dict] = field(default_factory=list)
    raw_response: Optional[dict] = None
    timestamp: float = field(default_factory=time.time)

    @property
    def is_success(self) -> bool:
        return self.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SIMULATED)

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "status": self.status.value,
            "transaction_hash": self.transaction_hash,
            "chain": self.chain,
            "gas_used": self.gas_used,
            "gas_price_gwei": self.gas_price_gwei,
            "error": self.error,
            "logs": self.logs,
            "timestamp": self.timestamp,
        }


@dataclass
class Workflow:
    """Represents a KeeperHub workflow."""
    id: str
    name: str
    description: str
    slug: str = ""
    is_paid: bool = False
    price_usd: Optional[float] = None
    input_schema: Optional[dict] = None
    tags: list[str] = field(default_factory=list)


class KeeperHubClient:
    """High-level client for KeeperHub MCP Server.

    Handles authentication, request building, retries, and error handling.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._base_url = self._settings.keeperhub_mcp_url.rstrip("/")
        self._api_key = self._settings.keeperhub_api_key

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._default_headers(),
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
        self._retry_count = 3
        self._retry_delay = 1.0

    def _default_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _generate_idempotency_key(self, tool_name: str, params: dict) -> str:
        """Generate an idempotency key for retry-safe execution."""
        import uuid
        payload = json.dumps({"tool": tool_name, "params": params, "uuid": str(uuid.uuid4())}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    async def _execute_tool(
        self,
        tool_name: str,
        params: dict,
        simulate: bool = False,
        idempotency_key: Optional[str] = None,
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
            request_body["params"]["simulate"] = True
        if idempotency_key:
            request_body["params"]["idempotency_key"] = idempotency_key

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
                    wait_time = self._retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                elif status == 402:
                    # Payment required - x402/MPP challenge
                    logger.info("402 challenge received - agentic wallet will handle payment")
                    # Try to parse the challenge
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
                wait_time = self._retry_delay * (2 ** attempt)
                logger.warning(f"Connection error, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)

        raise Exception(f"Tool '{tool_name}' failed after {self._retry_count} retries")

    # ---- Workflow Operations ----

    async def list_workflows(self, tags: Optional[list[str]] = None) -> list[Workflow]:
        """List available workflows."""
        params: dict = {}
        if tags:
            params["tags"] = tags

        result = await self._execute_tool("list_workflows", params)
        workflows = []
        for wf in result.get("workflows", []):
            workflows.append(Workflow(
                id=wf.get("id", ""),
                name=wf.get("name", ""),
                description=wf.get("description", ""),
                slug=wf.get("slug", ""),
                is_paid=wf.get("is_paid", False),
                price_usd=wf.get("price_usd"),
                input_schema=wf.get("input_schema"),
                tags=wf.get("tags", []),
            ))
        return workflows

    async def search_workflows(self, query: str) -> list[Workflow]:
        """Search workflows by query string."""
        result = await self._execute_tool("search_workflows", {"query": query})
        workflows = []
        for wf in result.get("workflows", []):
            workflows.append(Workflow(
                id=wf.get("id", ""),
                name=wf.get("name", ""),
                description=wf.get("description", ""),
                slug=wf.get("slug", ""),
                is_paid=wf.get("is_paid", False),
                price_usd=wf.get("price_usd"),
                input_schema=wf.get("input_schema"),
                tags=wf.get("tags", []),
            ))
        return workflows

    async def create_workflow(
        self,
        name: str,
        description: str,
        workflow_def: dict,
    ) -> str:
        """Create a new workflow. Returns workflow ID."""
        result = await self._execute_tool("create_workflow", {
            "name": name,
            "description": description,
            "definition": workflow_def,
        })
        return result.get("workflow_id", "")

    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: Optional[dict] = None,
    ) -> ExecutionResult:
        """Execute a workflow and return the result."""
        params = {"workflow_id": workflow_id}
        if inputs:
            params["inputs"] = inputs

        result = await self._execute_tool("execute_workflow", params)
        return ExecutionResult(
            workflow_id=workflow_id,
            execution_id=result.get("execution_id"),
            status=ExecutionStatus(result.get("status", "pending")),
            transaction_hash=result.get("transaction_hash"),
            logs=result.get("logs", []),
            raw_response=result,
        )

    async def get_execution(self, execution_id: str) -> ExecutionResult:
        """Get execution status and logs."""
        result = await self._execute_tool("get_execution", {"execution_id": execution_id})
        return ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus(result.get("status", "pending")),
            transaction_hash=result.get("transaction_hash"),
            gas_used=result.get("gas_used"),
            gas_price_gwei=result.get("gas_price_gwei"),
            error=result.get("error"),
            logs=result.get("logs", []),
            raw_response=result,
        )

    async def ai_generate_workflow(
        self,
        description: str,
    ) -> dict:
        """Use AI to generate a workflow from natural language."""
        result = await self._execute_tool("ai_generate_workflow", {
            "description": description,
        })
        return result

    # ---- Direct Onchain Execution ----

    async def get_direct_execution_status(self, execution_id: str) -> dict:
        """Get status of a direct execution (transfer or contract call).

        Returns tx hash and result for polling until completion.
        """
        return await self._execute_tool("get_direct_execution_status", {
            "execution_id": execution_id,
        })

    async def execute_transfer(
        self,
        to_address: str,
        amount: str,
        token_address: Optional[str] = None,
        simulate: bool = False,
    ) -> ExecutionResult:
        """Execute a native or ERC20 token transfer.

        Args:
            to_address: Recipient address
            amount: Amount in wei (for native) or token decimals
            token_address: ERC20 token address (None for native transfers)
            simulate: If True, simulate without broadcasting
        """
        params: dict = {
            "to": to_address,
            "amount": amount,
            "chain": self._settings.keeperhub_chain.value,
        }
        if token_address:
            params["token_address"] = token_address

        idem_key = self._generate_idempotency_key("execute_transfer", params)

        if simulate:
            result = await self._execute_tool("execute_transfer", params, simulate=True)
            return ExecutionResult(
                status=ExecutionStatus.SIMULATED,
                chain=self._settings.keeperhub_chain.value,
                gas_used=result.get("gas_estimate"),
                raw_response=result,
            )

        result = await self._execute_tool(
            "execute_transfer", params, idempotency_key=idem_key
        )
        return ExecutionResult(
            execution_id=result.get("execution_id"),
            status=ExecutionStatus(result.get("status", "pending")),
            transaction_hash=result.get("transaction_hash"),
            chain=self._settings.keeperhub_chain.value,
            gas_used=result.get("gas_used"),
            raw_response=result,
        )

    async def execute_contract_call(
        self,
        contract_address: str,
        data: str,
        value: str = "0",
        simulate: bool = False,
    ) -> ExecutionResult:
        """Execute a contract call.

        Args:
            contract_address: Target contract address
            data: Calldata (hex string)
            value: Native token value in wei
            simulate: If True, simulate without broadcasting
        """
        params = {
            "to": contract_address,
            "data": data,
            "value": value,
            "chain": self._settings.keeperhub_chain.value,
        }
        idem_key = self._generate_idempotency_key("execute_contract_call", params)

        if simulate:
            result = await self._execute_tool(
                "execute_contract_call", params, simulate=True
            )
            return ExecutionResult(
                status=ExecutionStatus.SIMULATED,
                chain=self._settings.keeperhub_chain.value,
                gas_used=result.get("gas_estimate"),
                raw_response=result,
            )

        result = await self._execute_tool(
            "execute_contract_call", params, idempotency_key=idem_key
        )
        return ExecutionResult(
            execution_id=result.get("execution_id"),
            status=ExecutionStatus(result.get("status", "pending")),
            transaction_hash=result.get("transaction_hash"),
            chain=self._settings.keeperhub_chain.value,
            gas_used=result.get("gas_used"),
            raw_response=result,
        )

    async def execute_check_and_execute(
        self,
        read_condition: dict,
        execute_action: dict,
    ) -> ExecutionResult:
        """Execute a conditional transaction (read + execute).

        The transaction only executes if the read condition is met.
        """
        params = {
            "read_condition": read_condition,
            "execute_action": execute_action,
            "chain": self._settings.keeperhub_chain.value,
        }
        result = await self._execute_tool("execute_check_and_execute", params)
        return ExecutionResult(
            execution_id=result.get("execution_id"),
            status=ExecutionStatus(result.get("status", "pending")),
            transaction_hash=result.get("transaction_hash"),
            chain=self._settings.keeperhub_chain.value,
            raw_response=result,
        )

    # ---- DeFi Protocol Actions ----

    async def search_protocol_actions(
        self, protocol: Optional[str] = None, action: Optional[str] = None
    ) -> list[dict]:
        """Search available DeFi protocol actions."""
        params: dict = {}
        if protocol:
            params["protocol"] = protocol
        if action:
            params["action"] = action

        result = await self._execute_tool("search_protocol_actions", params)
        return result.get("actions", [])

    async def execute_protocol_action(
        self,
        protocol: str,
        action: str,
        params: dict,
        simulate: bool = False,
    ) -> ExecutionResult:
        """Execute a DeFi protocol action (e.g. Aave supply, Uniswap swap).

        Args:
            protocol: Protocol name (e.g. 'aave-v3', 'uniswap')
            action: Action name (e.g. 'supply', 'swap', 'withdraw')
            params: Action-specific parameters
            simulate: If True, simulate without broadcasting
        """
        call_params = {
            "protocol": protocol,
            "action": action,
            "params": params,
            "chain": self._settings.keeperhub_chain.value,
        }
        idem_key = self._generate_idempotency_key(
            f"{protocol}/{action}", params
        )

        if simulate:
            result = await self._execute_tool(
                "execute_protocol_action", call_params, simulate=True
            )
            return ExecutionResult(
                status=ExecutionStatus.SIMULATED,
                chain=self._settings.keeperhub_chain.value,
                gas_used=result.get("gas_estimate"),
                raw_response=result,
            )

        result = await self._execute_tool(
            "execute_protocol_action", call_params, idempotency_key=idem_key
        )
        return ExecutionResult(
            execution_id=result.get("execution_id"),
            status=ExecutionStatus(result.get("status", "pending")),
            transaction_hash=result.get("transaction_hash"),
            chain=self._settings.keeperhub_chain.value,
            gas_used=result.get("gas_used"),
            raw_response=result,
        )

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

    async def call_workflow(self, slug: str, inputs: Optional[dict] = None) -> dict:
        """Call a marketplace workflow by slug."""
        params: dict = {"slug": slug}
        if inputs:
            params["inputs"] = inputs

        return await self._execute_tool("call_workflow", params)

    # ---- Wallet & Integrations ----

    async def list_integrations(self) -> list[dict]:
        """List configured integrations."""
        result = await self._execute_tool("list_integrations", {})
        return result.get("integrations", [])

    async def get_wallet_integration(self) -> dict:
        """Get wallet integration details."""
        return await self._execute_tool("get_wallet_integration", {})

    # ---- Validation ----

    async def validate_workflow(self, workflow_def: dict) -> dict:
        """Validate a workflow definition."""
        return await self._execute_tool("validate_workflow", {"definition": workflow_def})

    # ---- Lifecycle ----

    async def health_check(self) -> bool:
        """Check if KeeperHub MCP server is reachable."""
        try:
            response = await self._client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()