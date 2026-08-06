"""Tests for KeeperHub MCP client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError

from src.keeperhub.client import KeeperHubClient, ExecutionResult, ExecutionStatus, Workflow
from config.settings import Settings


@pytest.fixture
def settings():
    """Settings with KeeperHub configured."""
    return Settings(
        keeperhub_api_key="kh_test_123",
        keeperhub_chain="base_sepolia",
    )


@pytest.fixture
def client(settings):
    """KeeperHub client with mocked httpx."""
    c = KeeperHubClient(settings)
    c._client = AsyncMock()
    c._initialized = True
    return c


class TestExecutionResult:
    def test_success_status(self):
        result = ExecutionResult(
            execution_id="test-123",
            status=ExecutionStatus.SUCCESS,
            transaction_hash="0xabc",
        )
        assert result.is_success is True
        assert result.execution_id == "test-123"
        assert result.transaction_hash == "0xabc"

    def test_simulated_status(self):
        result = ExecutionResult(
            execution_id="sim-123",
            status=ExecutionStatus.SIMULATED,
        )
        assert result.is_success is True

    def test_failed_status(self):
        result = ExecutionResult(
            execution_id="fail-123",
            status=ExecutionStatus.FAILED,
            error="Insufficient balance",
        )
        assert result.is_success is False
        assert result.error == "Insufficient balance"

    def test_to_dict(self):
        result = ExecutionResult(
            execution_id="test-123",
            status=ExecutionStatus.SUCCESS,
            transaction_hash="0xabc",
            chain="base",
            gas_used=21000,
        )
        d = result.to_dict()
        assert d["execution_id"] == "test-123"
        assert d["status"] == "success"
        assert d["gas_used"] == 21000


class TestWorkflow:
    def test_workflow_creation(self):
        wf = Workflow(
            id="wf-123",
            name="Test Workflow",
            description="A test workflow",
            enabled=True,
            project_id="proj-1",
            tag_ids=["tag-1"],
        )
        assert wf.id == "wf-123"
        assert wf.name == "Test Workflow"
        assert wf.enabled is True


class TestKeeperHubClient:
    @pytest.mark.asyncio
    async def test_is_configured(self, settings, client):
        assert client.is_configured is True

    @pytest.mark.asyncio
    async def test_is_not_configured(self):
        bad_settings = Settings(keeperhub_api_key="")
        c = KeeperHubClient(bad_settings)
        assert c.is_configured is False

    @pytest.mark.asyncio
    async def test_initialize_success(self, settings):
        c = KeeperHubClient(settings)
        mock_response = MagicMock()
        mock_response.json.return_value = {"protocolVersion": "2024-11-05"}
        mock_response.headers = {"mcp-session-id": "session-123"}
        mock_response.raise_for_status = MagicMock()
        c._client = AsyncMock()
        c._client.post = AsyncMock(return_value=mock_response)

        result = await c.initialize()
        assert result is True
        assert c._initialized is True
        assert c._session_id == "session-123"

    @pytest.mark.asyncio
    async def test_initialize_failure(self, settings):
        c = KeeperHubClient(settings)
        c._client = AsyncMock()
        c._client.post = AsyncMock(side_effect=Exception("Connection failed"))

        result = await c.initialize()
        assert result is False
        assert c._initialized is False

    @pytest.mark.asyncio
    async def test_execute_transfer_success(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": '{"executionId": "exec-123", "status": "success", "transactionHash": "0xabc"}'}],
        }
        mock_response.raise_for_status = MagicMock()
        client._client.post = AsyncMock(return_value=mock_response)

        result = await client.execute_transfer(
            to_address="0x1234567890123456789012345678901234567890",
            amount="1000000000000000000",
        )
        assert result.execution_id == "exec-123"
        assert result.status == ExecutionStatus.SUCCESS
        assert result.transaction_hash == "0xabc"

    @pytest.mark.asyncio
    async def test_execute_transfer_simulate(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": '{"executionId": "sim-123", "status": "simulated"}'}],
        }
        mock_response.raise_for_status = MagicMock()
        client._client.post = AsyncMock(return_value=mock_response)

        result = await client.execute_transfer(
            to_address="0x1234567890123456789012345678901234567890",
            amount="1000000000000000000",
            simulate=True,
        )
        assert result.status == ExecutionStatus.SIMULATED

    @pytest.mark.asyncio
    async def test_execute_contract_call(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": '{"executionId": "exec-456", "status": "success"}'}],
        }
        mock_response.raise_for_status = MagicMock()
        client._client.post = AsyncMock(return_value=mock_response)

        result = await client.execute_contract_call(
            contract_address="0xabcdef1234567890abcdef1234567890abcdef12",
            data="0xa9059cbb",
            value="0",
        )
        assert result.execution_id == "exec-456"

    @pytest.mark.asyncio
    async def test_list_workflows(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": '{"workflows": [{"id": "wf-1", "name": "Test", "description": "D", "enabled": true}]}'}],
        }
        mock_response.raise_for_status = MagicMock()
        client._client.post = AsyncMock(return_value=mock_response)

        workflows = await client.list_workflows()
        assert len(workflows) == 1
        assert isinstance(workflows[0], Workflow)
        assert workflows[0].id == "wf-1"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, client):
        """Test that retries work on transient failures."""
        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "content": [{"type": "text", "text": '{"executionId": "exec-ok"}'}],
            }
            mock_response.raise_for_status = MagicMock()
            return mock_response

        client._client.post = mock_post
        client._retry_count = 3

        result = await client.execute_transfer(
            to_address="0x1234567890123456789012345678901234567890",
            amount="1000000000000000000",
        )
        assert call_count == 3  # retried twice before success
        assert result.execution_id == "exec-ok"

    @pytest.mark.asyncio
    async def test_generate_idempotency_key(self, client):
        key1 = client._generate_idempotency_key("transfer", {"to": "0x1", "amount": "100"})
        key2 = client._generate_idempotency_key("transfer", {"to": "0x1", "amount": "100"})
        key3 = client._generate_idempotency_key("transfer", {"to": "0x2", "amount": "100"})

        assert key1 == key2  # same params = same key
        assert key1 != key3  # different params = different key

    @pytest.mark.asyncio
    async def test_close(self, client):
        await client.close()
        client._client.aclose.assert_called_once()