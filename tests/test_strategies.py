"""Tests for DeFi strategies (liquidation shield, yield optimizer, rebalancer)."""

import os
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from config.settings import Settings
from src.strategies.liquidation_shield import LendingPosition, LiquidationShield
from src.strategies.rebalancer import PortfolioRebalancer
from src.strategies.yield_optimizer import YieldOpportunity, YieldOptimizer


@contextmanager
def _isolated_env():
    """Temporarily remove DeFi Sentinel env vars from the process."""
    keys = [
        "LLM_PROVIDER",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "KEEPERHUB_API_KEY",
        "KEEPERHUB_CHAIN",
        "PORTFOLIO_TARGETS",
        "LIQUIDATION_THRESHOLD",
        "LIQUIDATION_CRITICAL",
        "AUTO_APPROVE_MAX_USD",
    ]
    saved = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ.pop(k, None)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _empty_settings(**kwargs) -> Settings:
    """Build Settings without loading local .env, so tests are deterministic."""
    return Settings(_env_file=None, **kwargs)


@pytest.fixture
def settings():
    with _isolated_env():
        return _empty_settings(
            liquidation_threshold=1.5,
            liquidation_critical=1.2,
            portfolio_rebalance_threshold=5.0,
            auto_approve_max_usd=100.0,
            portfolio_targets=(
                "0x0000000000000000000000000000000000000000:60;"
                "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913:40"
            ),
        )


class TestLiquidationShield:
    @pytest.mark.asyncio
    async def test_critical_health_factor_triggers_emergency(self, settings):
        shield = LiquidationShield(settings, keeperhub=None)
        shield._positions = [
            LendingPosition(
                protocol="aave-v3",
                market="USDC",
                supplied_amount=1000,
                supplied_usd=1000,
                borrowed_amount=800,
                borrowed_usd=800,
                health_factor=1.1,
                liquidation_threshold=0.8,
                liquidation_bonus=0.05,
                supply_apr=3.0,
                borrow_apr=4.0,
            )
        ]
        shield._get_positions = AsyncMock(return_value=shield._positions)

        recs = await shield.analyze(None)
        assert len(recs) == 1
        assert recs[0]["action"] == "emergency_repay_debt"
        assert recs[0]["priority"] == 1
        assert recs[0]["requires_approval"] is False

    @pytest.mark.asyncio
    async def test_warning_health_factor_suggests_collateral(self, settings):
        shield = LiquidationShield(settings, keeperhub=None)
        shield._positions = [
            LendingPosition(
                protocol="compound",
                market="USDC",
                supplied_amount=1000,
                supplied_usd=1000,
                borrowed_amount=800,
                borrowed_usd=800,
                health_factor=1.4,
                liquidation_threshold=0.8,
                liquidation_bonus=0.05,
                supply_apr=3.0,
                borrow_apr=4.0,
            )
        ]
        shield._get_positions = AsyncMock(return_value=shield._positions)

        recs = await shield.analyze(None)
        assert len(recs) == 1
        assert recs[0]["action"] == "add_collateral"
        assert recs[0]["priority"] == 2
        assert recs[0]["requires_approval"] is True

    @pytest.mark.asyncio
    async def test_safe_health_factor_no_recommendation(self, settings):
        shield = LiquidationShield(settings, keeperhub=None)
        shield._positions = [
            LendingPosition(
                protocol="aave-v3",
                market="USDC",
                supplied_amount=1000,
                supplied_usd=1000,
                borrowed_amount=100,
                borrowed_usd=100,
                health_factor=5.0,
                liquidation_threshold=0.8,
                liquidation_bonus=0.05,
                supply_apr=3.0,
                borrow_apr=4.0,
            )
        ]
        shield._get_positions = AsyncMock(return_value=shield._positions)

        recs = await shield.analyze(None)
        assert recs == []

    @pytest.mark.asyncio
    async def test_execute_simulates_before_broadcast(self, settings):
        keeperhub = MagicMock()
        keeperhub.execute_protocol_action = AsyncMock(
            side_effect=[
                MagicMock(is_success=True, execution_id="sim-1", transaction_hash=None),
                MagicMock(
                    is_success=True,
                    execution_id="exec-1",
                    transaction_hash="0xabc",
                    status=MagicMock(value="success"),
                ),
            ]
        )
        shield = LiquidationShield(settings, keeperhub=keeperhub)

        decision = MagicMock()
        decision.parameters = {
            "protocol": "aave-v3",
            "action": "supply",
            "market": "USDC",
            "amount": "1000",
        }

        result = await shield.execute(decision)

        assert keeperhub.execute_protocol_action.call_count == 2
        # First call is the simulation
        assert keeperhub.execute_protocol_action.await_args_list[0].kwargs["simulate"] is True
        # Broadcast call omits simulate (defaults to False in the client)
        assert keeperhub.execute_protocol_action.await_args_list[1].kwargs.get("simulate") is None
        assert result["transaction_hash"] == "0xabc"

    @pytest.mark.asyncio
    async def test_execute_aborts_on_simulation_failure(self, settings):
        keeperhub = MagicMock()
        keeperhub.execute_protocol_action = AsyncMock(
            return_value=MagicMock(is_success=False, error="revert")
        )
        shield = LiquidationShield(settings, keeperhub=keeperhub)

        decision = MagicMock()
        decision.parameters = {
            "protocol": "aave-v3",
            "action": "supply",
            "market": "USDC",
            "amount": "1000",
        }

        with pytest.raises(RuntimeError):
            await shield.execute(decision)

        assert keeperhub.execute_protocol_action.await_count == 1  # never broadcast


class TestYieldOptimizer:
    @pytest.mark.asyncio
    async def test_better_yield_creates_recommendation(self, settings):
        optimizer = YieldOptimizer(settings, keeperhub=None)
        optimizer._current_allocations = {
            "usdc-aave": {
                "token": "USDC",
                "protocol": "aave-v3",
                "apr": 3.0,
                "amount_usd": 5000,
            }
        }
        optimizer._opportunities = [
            YieldOpportunity(
                protocol="yearn-v3",
                market="USDC",
                token="USDC",
                apr=5.0,
                tvl_usd=1000000,
                risk_score=2.0,
                is_stablecoin=True,
            )
        ]
        optimizer._fetch_opportunities = AsyncMock(return_value=optimizer._opportunities)

        recs = await optimizer.analyze(None)
        assert len(recs) == 1
        assert recs[0]["action"] == "reallocate_yield"
        assert recs[0]["parameters"]["to_protocol"] == "yearn-v3"
        assert recs[0]["requires_approval"] is False  # low risk auto-executes

    @pytest.mark.asyncio
    async def test_no_opportunity_no_recommendation(self, settings):
        optimizer = YieldOptimizer(settings, keeperhub=None)
        optimizer._current_allocations = {
            "usdc-aave": {
                "token": "USDC",
                "protocol": "aave-v3",
                "apr": 5.0,
                "amount_usd": 5000,
            }
        }
        optimizer._opportunities = [
            YieldOpportunity(
                protocol="compound",
                market="USDC",
                token="USDC",
                apr=3.5,
                tvl_usd=1000000,
                risk_score=2.0,
            )
        ]
        optimizer._fetch_opportunities = AsyncMock(return_value=optimizer._opportunities)

        recs = await optimizer.analyze(None)
        assert recs == []

    @pytest.mark.asyncio
    async def test_high_risk_opportunity_requires_approval(self, settings):
        optimizer = YieldOptimizer(settings, keeperhub=None)
        optimizer._current_allocations = {
            "usdc-aave": {
                "token": "USDC",
                "protocol": "aave-v3",
                "apr": 3.0,
                "amount_usd": 5000,
            }
        }
        optimizer._opportunities = [
            YieldOpportunity(
                protocol="morpho",
                market="USDC",
                token="USDC",
                apr=6.0,
                tvl_usd=1000000,
                risk_score=8.0,
            )
        ]
        optimizer._fetch_opportunities = AsyncMock(return_value=optimizer._opportunities)

        recs = await optimizer.analyze(None)
        assert len(recs) == 1
        assert recs[0]["requires_approval"] is True

    @pytest.mark.asyncio
    async def test_execute_withdraw_then_deposit(self, settings):
        keeperhub = MagicMock()
        keeperhub.execute_protocol_action = AsyncMock(
            side_effect=[
                MagicMock(is_success=True, transaction_hash="0xwithdraw"),
                MagicMock(is_success=True, transaction_hash="0xdeposit"),
            ]
        )
        optimizer = YieldOptimizer(settings, keeperhub=keeperhub)

        decision = MagicMock()
        decision.parameters = {
            "from_protocol": "aave-v3",
            "to_protocol": "yearn-v3",
            "token": "USDC",
            "amount_usd": 5000,
            "current_apr": 3.0,
            "new_apr": 5.0,
        }

        result = await optimizer.execute(decision)

        assert result["withdraw_tx"] == "0xwithdraw"
        assert result["deposit_tx"] == "0xdeposit"
        assert keeperhub.execute_protocol_action.await_count == 2


class TestPortfolioRebalancer:
    @pytest.mark.asyncio
    async def test_deviation_triggers_rebalance(self, settings):
        rebalancer = PortfolioRebalancer(settings, keeperhub=None)

        portfolio = MagicMock()
        portfolio.total_value_usd = 10000
        portfolio.positions = [
            {"token_address": "0x0000000000000000000000000000000000000000", "usd_value": 8000},
            {"token_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "usd_value": 2000},
        ]

        recs = await rebalancer.analyze(portfolio)
        # ETH at 80% vs 60% target, USDC at 20% vs 40% target — both deviate
        assert len(recs) == 2
        reduce = [r for r in recs if r["action"] == "rebalance_reduce"]
        increase = [r for r in recs if r["action"] == "rebalance_increase"]
        assert len(reduce) == 1
        assert len(increase) == 1
        assert reduce[0]["parameters"]["direction"] == "reduce"

    @pytest.mark.asyncio
    async def test_no_deviation_no_recommendation(self, settings):
        rebalancer = PortfolioRebalancer(settings, keeperhub=None)

        portfolio = MagicMock()
        portfolio.total_value_usd = 10000
        portfolio.positions = [
            {"token_address": "0x0000000000000000000000000000000000000000", "usd_value": 6000},
            {"token_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "usd_value": 4000},
        ]

        recs = await rebalancer.analyze(portfolio)
        assert recs == []

    @pytest.mark.asyncio
    async def test_empty_portfolio_no_recommendation(self, settings):
        rebalancer = PortfolioRebalancer(settings, keeperhub=None)

        portfolio = MagicMock()
        portfolio.total_value_usd = 0
        portfolio.positions = []

        recs = await rebalancer.analyze(portfolio)
        assert recs == []

    @pytest.mark.asyncio
    async def test_execute_simulates_then_broadcasts(self, settings):
        keeperhub = MagicMock()
        keeperhub.execute_transfer = AsyncMock(
            side_effect=[
                MagicMock(is_success=True, execution_id="sim-1"),
                MagicMock(
                    is_success=True,
                    execution_id="exec-1",
                    transaction_hash="0xabc",
                    status=MagicMock(value="success"),
                    gas_used=21000,
                ),
            ]
        )
        rebalancer = PortfolioRebalancer(settings, keeperhub=keeperhub)

        decision = MagicMock()
        decision.parameters = {
            "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "direction": "increase",
            "amount_usd": 2000,
        }

        result = await rebalancer.execute(decision)

        assert keeperhub.execute_transfer.await_count == 2
        # First call is the simulation (simulate=True)
        assert keeperhub.execute_transfer.await_args_list[0].kwargs["simulate"] is True
        # Broadcast call omits simulate (defaults to False in the client)
        assert keeperhub.execute_transfer.await_args_list[1].kwargs.get("simulate") is None
        assert result["transaction_hash"] == "0xabc"
