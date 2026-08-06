"""Liquidation Shield Strategy.

Monitors lending positions and automatically protects against liquidation
by adding collateral or repaying debt when health factors approach danger zones.
"""

import logging
from dataclasses import dataclass
from typing import Any

from config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class LendingPosition:
    """Represents a lending position on a protocol."""

    protocol: str  # aave-v3, compound, etc.
    market: str  # e.g., "USDC"
    supplied_amount: float
    supplied_usd: float
    borrowed_amount: float
    borrowed_usd: float
    health_factor: float
    liquidation_threshold: float
    liquidation_bonus: float
    supply_apr: float
    borrow_apr: float


class LiquidationShield:
    """Strategy to protect against liquidation.

    Monitors health factors and takes protective actions:
    1. ALERT - When health factor approaches threshold
    2. ADD_COLLATERAL - Deposit more collateral
    3. REPAY_DEBT - Repay partial or full debt
    4. LIQUIDATE_POSITION - Emergency: withdraw everything
    """

    def __init__(self, settings: Settings, keeperhub=None):
        self._settings = settings
        self._keeperhub = keeperhub
        self._positions: list[LendingPosition] = []

    async def analyze(self, portfolio_state: Any) -> list[dict]:
        """Analyze portfolio for liquidation risks.

        Returns list of recommendations with priority ordering.
        """
        recommendations = []

        # Get current lending positions
        positions = await self._get_positions()

        for pos in positions:
            # Critical: health factor below critical threshold
            if pos.health_factor <= self._settings.liquidation_critical:
                recommendations.append(
                    {
                        "action": "emergency_repay_debt",
                        "reason": (
                            f"CRITICAL: {pos.protocol} {pos.market} position has "
                            f"health factor {pos.health_factor:.2f} (critical threshold: "
                            f"{self._settings.liquidation_critical}). Immediate debt "
                            f"repayment required to avoid liquidation."
                        ),
                        "priority": 1,
                        "parameters": {
                            "protocol": pos.protocol,
                            "market": pos.market,
                            "action": "repay",
                            "repay_percentage": 100,  # repay all
                        },
                        "estimated_usd_impact": pos.borrowed_usd,
                        "requires_approval": False,  # emergency auto-execute
                        "strategy": "liquidation_shield",
                    }
                )

            # Warning: health factor below warning threshold
            elif pos.health_factor <= self._settings.liquidation_threshold:
                recommendations.append(
                    {
                        "action": "add_collateral",
                        "reason": (
                            f"WARNING: {pos.protocol} {pos.market} position has "
                            f"health factor {pos.health_factor:.2f} (warning threshold: "
                            f"{self._settings.liquidation_threshold}). Adding collateral "
                            f"to improve safety margin."
                        ),
                        "priority": 2,
                        "parameters": {
                            "protocol": pos.protocol,
                            "market": pos.market,
                            "action": "supply",
                            "target_health_factor": 2.0,
                        },
                        "estimated_usd_impact": self._calculate_collateral_needed(pos),
                        "requires_approval": True,
                        "strategy": "liquidation_shield",
                    }
                )

            # Info: approaching threshold
            elif pos.health_factor <= self._settings.liquidation_threshold * 1.2:
                recommendations.append(
                    {
                        "action": "monitor_closely",
                        "reason": (
                            f"INFO: {pos.protocol} {pos.market} position health factor "
                            f"{pos.health_factor:.2f} is approaching warning threshold. "
                            f"Monitoring closely."
                        ),
                        "priority": 4,
                        "parameters": {
                            "protocol": pos.protocol,
                            "market": pos.market,
                        },
                        "estimated_usd_impact": 0,
                        "requires_approval": False,
                        "strategy": "liquidation_shield",
                    }
                )

        return recommendations

    async def execute(self, decision: Any) -> dict:
        """Execute a liquidation protection decision."""
        if not self._keeperhub:
            raise RuntimeError("KeeperHub client not configured")

        params = decision.parameters
        protocol = params.get("protocol", "aave-v3")
        action = params.get("action", "supply")

        # Simulate first
        logger.info(f"Simulating {action} on {protocol}...")
        sim_result = await self._keeperhub.execute_protocol_action(
            protocol=protocol,
            action=action,
            params={
                "market": params.get("market", ""),
                "amount": params.get("amount", "0"),
            },
            simulate=True,
        )

        if not sim_result.is_success:
            raise RuntimeError(f"Simulation failed: {sim_result.error}")

        # Execute
        logger.info(f"Executing {action} on {protocol}...")
        result = await self._keeperhub.execute_protocol_action(
            protocol=protocol,
            action=action,
            params={
                "market": params.get("market", ""),
                "amount": params.get("amount", "0"),
            },
        )

        return {
            "execution_id": result.execution_id,
            "transaction_hash": result.transaction_hash,
            "status": result.status.value,
            "gas_used": result.gas_used,
        }

    async def _get_positions(self) -> list[LendingPosition]:
        """Fetch current lending positions from KeeperHub."""
        if not self._keeperhub:
            return []

        positions = []
        try:
            # Query Aave v3 positions
            aave_actions = await self._keeperhub.search_protocol_actions(protocol="aave-v3")
            for action in aave_actions:
                try:
                    pos = LendingPosition(
                        protocol="aave-v3",
                        market=action.get("market", action.get("token", "USDC")),
                        supplied_amount=float(action.get("supplied_amount", 0)),
                        supplied_usd=float(action.get("supplied_usd", 0)),
                        borrowed_amount=float(action.get("borrowed_amount", 0)),
                        borrowed_usd=float(action.get("borrowed_usd", 0)),
                        health_factor=float(action.get("health_factor", 2.0)),
                        liquidation_threshold=float(action.get("liquidation_threshold", 0.8)),
                        liquidation_bonus=float(action.get("liquidation_bonus", 0.05)),
                        supply_apr=float(action.get("supply_apr", 0)),
                        borrow_apr=float(action.get("borrow_apr", 0)),
                    )
                    positions.append(pos)
                except (ValueError, TypeError):
                    continue

            # Also query Compound
            compound_actions = await self._keeperhub.search_protocol_actions(protocol="compound")
            for action in compound_actions:
                try:
                    pos = LendingPosition(
                        protocol="compound",
                        market=action.get("market", action.get("token", "USDC")),
                        supplied_amount=float(action.get("supplied_amount", 0)),
                        supplied_usd=float(action.get("supplied_usd", 0)),
                        borrowed_amount=float(action.get("borrowed_amount", 0)),
                        borrowed_usd=float(action.get("borrowed_usd", 0)),
                        health_factor=float(action.get("health_factor", 2.0)),
                        liquidation_threshold=float(action.get("liquidation_threshold", 0.8)),
                        liquidation_bonus=float(action.get("liquidation_bonus", 0.05)),
                        supply_apr=float(action.get("supply_apr", 0)),
                        borrow_apr=float(action.get("borrow_apr", 0)),
                    )
                    positions.append(pos)
                except (ValueError, TypeError):
                    continue

            self._positions = positions
            logger.info(f"Fetched {len(positions)} lending positions")

        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")

        return self._positions

    def _calculate_collateral_needed(self, position: LendingPosition) -> float:
        """Calculate how much collateral is needed to reach target health factor."""
        target_hf = 2.0
        if position.borrowed_usd == 0:
            return 0.0

        # Simplified calculation
        current_equity = position.supplied_usd - position.borrowed_usd
        target_equity = position.borrowed_usd * target_hf / position.liquidation_threshold
        return max(0, target_equity - current_equity)
