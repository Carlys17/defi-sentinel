"""Yield Optimizer Strategy.

Monitors yield rates across DeFi protocols and suggests/recommends
capital reallocation to maximize returns while managing risk.
"""

import logging
from dataclasses import dataclass
from typing import Any

from config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class YieldOpportunity:
    """Represents a yield opportunity on a protocol."""

    protocol: str
    market: str
    token: str
    apr: float
    tvl_usd: float
    risk_score: float  # 1 (low) to 10 (high)
    is_stablecoin: bool = False
    lock_period_days: int = 0


class YieldOptimizer:
    """Strategy to optimize yield across DeFi protocols.

    Monitors rates and suggests reallocation when better opportunities exist.
    """

    # Minimum APR improvement to trigger reallocation
    MIN_APR_IMPROVEMENT = 0.5  # percentage points

    # Maximum acceptable risk score for auto-execution
    MAX_AUTO_RISK_SCORE = 5.0

    def __init__(self, settings: Settings, keeperhub=None):
        self._settings = settings
        self._keeperhub = keeperhub
        self._current_allocations: dict[str, dict] = {}
        self._opportunities: list[YieldOpportunity] = []

    async def analyze(self, portfolio_state: Any) -> list[dict]:
        """Analyze portfolio for yield optimization opportunities.

        Returns list of recommendations.
        """
        recommendations = []

        # Fetch current opportunities
        opportunities = await self._fetch_opportunities()

        # Compare current allocations with best opportunities
        for allocation in self._current_allocations.values():
            token = allocation.get("token", "")
            current_protocol = allocation.get("protocol", "")
            current_apr = allocation.get("apr", 0.0)
            amount_usd = allocation.get("amount_usd", 0.0)

            # Find better opportunities for this token
            better_options = [
                opp
                for opp in opportunities
                if opp.token == token and opp.apr > current_apr + self.MIN_APR_IMPROVEMENT
            ]

            if better_options:
                # Sort by risk-adjusted return
                better_options.sort(key=lambda o: o.apr / max(o.risk_score, 1))
                best = better_options[0]

                recommendations.append(
                    {
                        "action": "reallocate_yield",
                        "reason": (
                            f"Yield opportunity: {best.protocol} offers {best.apr:.2f}% APR "
                            f"for {best.token} vs current {current_apr:.2f}% on "
                            f"{current_protocol}. Potential improvement: "
                            f"{best.apr - current_apr:.2f}% APR on ${amount_usd:,.2f}."
                        ),
                        "priority": 3 if best.risk_score <= self.MAX_AUTO_RISK_SCORE else 4,
                        "parameters": {
                            "from_protocol": current_protocol,
                            "to_protocol": best.protocol,
                            "token": token,
                            "amount_usd": amount_usd,
                            "current_apr": current_apr,
                            "new_apr": best.apr,
                        },
                        "estimated_usd_impact": (
                            amount_usd * (best.apr - current_apr) / 100
                        ),  # annual impact
                        "requires_approval": best.risk_score > self.MAX_AUTO_RISK_SCORE,
                        "strategy": "yield_optimizer",
                    }
                )

        return recommendations

    async def execute(self, decision: Any) -> dict:
        """Execute a yield optimization decision."""
        if not self._keeperhub:
            raise RuntimeError("KeeperHub client not configured")

        params = decision.parameters
        from_protocol = params.get("from_protocol", "")
        to_protocol = params.get("to_protocol", "")
        token = params.get("token", "")

        # Step 1: Withdraw from current protocol
        logger.info(f"Withdrawing from {from_protocol}...")
        withdraw_result = await self._keeperhub.execute_protocol_action(
            protocol=from_protocol,
            action="withdraw",
            params={"token": token, "amount": "max"},
        )

        if not withdraw_result.is_success:
            raise RuntimeError(f"Withdrawal failed: {withdraw_result.error}")

        # Step 2: Deposit to new protocol
        logger.info(f"Depositing to {to_protocol}...")
        deposit_result = await self._keeperhub.execute_protocol_action(
            protocol=to_protocol,
            action="supply",
            params={"token": token, "amount": "max"},
        )

        if not deposit_result.is_success:
            # Emergency: try to return to original protocol
            logger.error("Deposit failed! Attempting to return funds...")
            await self._keeperhub.execute_protocol_action(
                protocol=from_protocol,
                action="supply",
                params={"token": token, "amount": "max"},
            )
            raise RuntimeError(f"Deposit failed: {deposit_result.error}")

        return {
            "withdraw_tx": withdraw_result.transaction_hash,
            "deposit_tx": deposit_result.transaction_hash,
            "from_protocol": from_protocol,
            "to_protocol": to_protocol,
            "token": token,
        }

    async def _fetch_opportunities(self) -> list[YieldOpportunity]:
        """Fetch current yield opportunities from KeeperHub."""
        if not self._keeperhub:
            return []

        try:
            # Search for supply actions across protocols
            protocols = ["aave-v3", "compound", "morpho", "yearn-v3", "spark"]
            all_actions = []

            for protocol in protocols:
                try:
                    actions = await self._keeperhub.search_protocol_actions(protocol=protocol)
                    all_actions.extend(actions)
                except Exception as e:
                    logger.warning(f"Failed to fetch {protocol} actions: {e}")

            # Convert to opportunities
            opportunities = []
            for action in all_actions:
                try:
                    opp = YieldOpportunity(
                        protocol=action.get("protocol", protocol),
                        market=action.get("market", ""),
                        token=action.get("token", action.get("asset", "USDC")),
                        apr=float(action.get("apr", action.get("apy", 0.0))),
                        tvl_usd=float(action.get("tvl_usd", 0.0)),
                        risk_score=float(action.get("risk_score", 5.0)),
                        is_stablecoin=action.get("is_stablecoin", False),
                        lock_period_days=int(action.get("lock_period_days", 0)),
                    )
                    opportunities.append(opp)
                except (ValueError, TypeError):
                    continue

            self._opportunities = opportunities
            logger.info(f"Fetched {len(opportunities)} yield opportunities")
            return opportunities

        except Exception as e:
            logger.error(f"Failed to fetch opportunities: {e}")
            return []
