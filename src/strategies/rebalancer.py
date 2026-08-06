"""Portfolio Rebalancer Strategy.

Monitors portfolio allocation and rebalances when deviations exceed
configured thresholds.
"""

import logging
from typing import Any

from config.settings import Settings

logger = logging.getLogger(__name__)


class PortfolioRebalancer:
    """Strategy to maintain target portfolio allocations.

    Monitors actual vs target allocation and triggers rebalancing
    when deviations exceed the configured threshold.
    """

    def __init__(self, settings: Settings, keeperhub=None):
        self._settings = settings
        self._keeperhub = keeperhub
        self._targets = settings.parsed_portfolio_targets

    async def analyze(self, portfolio_state: Any) -> list[dict]:
        """Analyze portfolio allocation and suggest rebalancing.

        Returns list of recommendations.
        """
        recommendations = []
        total_value = portfolio_state.total_value_usd

        if total_value == 0 or not self._targets:
            return recommendations

        # Calculate current allocation percentages
        current_allocation = self._calculate_allocation(portfolio_state)

        # Check each target
        for target in self._targets:
            token = target["token_address"]
            target_pct = target["percentage"]

            current_pct = self._get_current_pct(current_allocation, token, total_value)
            deviation = current_pct - target_pct

            if abs(deviation) >= self._settings.portfolio_rebalance_threshold:
                direction = "reduce" if deviation > 0 else "increase"
                amount_to_move = abs(deviation) / 100 * total_value

                recommendations.append(
                    {
                        "action": f"rebalance_{direction}",
                        "reason": (
                            f"Portfolio rebalance: {token[:10]}... allocation is "
                            f"{current_pct:.1f}% vs target {target_pct:.1f}% "
                            f"(deviation: {deviation:+.1f}%). "
                            f"Need to {direction} by ${amount_to_move:,.2f}."
                        ),
                        "priority": 3,
                        "parameters": {
                            "token": token,
                            "direction": direction,
                            "amount_usd": amount_to_move,
                            "current_pct": current_pct,
                            "target_pct": target_pct,
                        },
                        "estimated_usd_impact": amount_to_move * 0.001,  # estimated gas/slippage
                        "requires_approval": amount_to_move > self._settings.auto_approve_max_usd,
                        "strategy": "rebalancer",
                    }
                )

        return recommendations

    async def execute(self, decision: Any) -> dict:
        """Execute a rebalancing decision."""
        if not self._keeperhub:
            raise RuntimeError("KeeperHub client not configured")

        params = decision.parameters
        token = params.get("token", "")
        direction = params.get("direction", "")
        amount_usd = params.get("amount_usd", 0)

        logger.info(f"Rebalancing: {direction} {token[:10]}... by ${amount_usd:,.2f}")

        # Simulate first
        sim_result = await self._keeperhub.execute_transfer(
            to_address=self._settings.wallet_address,
            amount=str(int(amount_usd * 1e18)),  # simplified
            token_address=token if token != "0x0000000000000000000000000000000000000000" else None,
            simulate=True,
        )

        if not sim_result.is_success:
            raise RuntimeError(f"Rebalance simulation failed: {sim_result.error}")

        # Execute
        result = await self._keeperhub.execute_transfer(
            to_address=self._settings.wallet_address,
            amount=str(int(amount_usd * 1e18)),
            token_address=token if token != "0x0000000000000000000000000000000000000000" else None,
        )

        return {
            "execution_id": result.execution_id,
            "transaction_hash": result.transaction_hash,
            "status": result.status.value,
            "token": token,
            "direction": direction,
            "amount_usd": amount_usd,
        }

    def _calculate_allocation(self, portfolio_state: Any) -> dict[str, float]:
        """Calculate current allocation by token."""
        allocation: dict[str, float] = {}
        for position in portfolio_state.positions:
            token = position.get("token_address", "")
            usd_value = position.get("usd_value", 0.0)
            allocation[token] = allocation.get(token, 0.0) + usd_value
        return allocation

    def _get_current_pct(self, allocation: dict[str, float], token: str, total: float) -> float:
        """Get current allocation percentage for a token."""
        if total == 0:
            return 0.0
        return (allocation.get(token, 0.0) / total) * 100
