"""Core AI Agent engine for DeFi Sentinel.

The agent orchestrates all strategies, makes decisions via LLM,
and coordinates with KeeperHub for onchain execution.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    IDLE = "idle"
    MONITORING = "monitoring"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class AgentDecision:
    """A decision made by the AI agent."""
    action: str
    reason: str
    priority: int  # 1 (highest) to 5 (lowest)
    parameters: dict = field(default_factory=dict)
    estimated_usd_impact: float = 0.0
    requires_approval: bool = False
    strategy: str = ""

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "reason": self.reason,
            "priority": self.priority,
            "parameters": self.parameters,
            "estimated_usd_impact": self.estimated_usd_impact,
            "requires_approval": self.requires_approval,
            "strategy": self.strategy,
        }


@dataclass
class PortfolioState:
    """Current state of the monitored portfolio."""
    total_value_usd: float = 0.0
    positions: list[dict] = field(default_factory=list)
    health_factors: dict[str, float] = field(default_factory=dict)
    pending_transactions: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_value_usd": self.total_value_usd,
            "positions": self.positions,
            "health_factors": self.health_factors,
            "pending_transactions": self.pending_transactions,
            "alerts": self.alerts,
            "timestamp": self.timestamp,
        }


class LLMClient:
    """LLM client abstraction supporting OpenAI and Anthropic."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = None
        self._initialize()

    def _initialize(self):
        if self._settings.llm_provider.value == "openai":
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self._settings.openai_api_key)
            self._model = self._settings.openai_model
        elif self._settings.llm_provider.value == "anthropic":
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self._settings.anthropic_api_key)
            self._model = self._settings.anthropic_model

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """Send a chat completion request."""
        if self._settings.llm_provider.value == "openai":
            return await self._chat_openai(system_prompt, user_message, temperature, max_tokens)
        elif self._settings.llm_provider.value == "anthropic":
            return await self._chat_anthropic(system_prompt, user_message, temperature, max_tokens)
        raise ValueError(f"Unsupported LLM provider: {self._settings.llm_provider}")

    async def _chat_openai(
        self, system_prompt: str, user_message: str, temperature: float, max_tokens: int
    ) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""

    async def _chat_anthropic(
        self, system_prompt: str, user_message: str, temperature: float, max_tokens: int
    ) -> str:
        response = await self._client.messages.create(
            model=self._model,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content[0].text if response.content else ""

    async def structured_response(
        self,
        system_prompt: str,
        user_message: str,
        schema: str,
    ) -> dict:
        """Get a structured JSON response matching a schema."""
        enhanced_system = f"{system_prompt}\n\nYou MUST respond with valid JSON matching this schema:\n{schema}"
        raw = await self.chat(enhanced_system, user_message, temperature=0.1)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response as JSON: {raw[:200]}")
            return {}


class DeFiSentinelAgent:
    """Main AI agent that orchestrates DeFi operations.

    The agent monitors portfolio state, analyzes risks and opportunities,
    makes decisions via LLM, and executes actions through KeeperHub.
    """

    SYSTEM_PROMPT = """\
You are DeFi Sentinel, an autonomous AI agent specialized in DeFi portfolio management and risk protection.

Your responsibilities:
1. MONITOR - Track portfolio positions, health factors, and market conditions
2. PROTECT - Prevent liquidations by suggesting collateral additions or repayments
3. OPTIMIZE - Identify yield optimization opportunities across protocols
4. REBALANCE - Maintain target portfolio allocations
5. ALERT - Notify users of critical events and opportunities

Decision-making principles:
- Always prioritize capital preservation over yield optimization
- Never suggest actions that exceed safety thresholds
- Provide clear reasoning for every decision
- Consider gas costs and slippage in all recommendations
- Be conservative with leverage and liquidation risks

Response format: Always return valid JSON with the following structure:
{
    "decisions": [
        {
            "action": "string - the action to take",
            "reason": "string - why this action is recommended",
            "priority": 1-5 (1=highest),
            "parameters": {},
            "estimated_usd_impact": 0.0,
            "requires_approval": true/false,
            "strategy": "string - which strategy this belongs to"
        }
    ]
}
"""

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._state = AgentState.IDLE
        self._llm: Optional[LLMClient] = None
        self._keeperhub = None
        self._strategies: dict[str, Any] = {}
        self._is_running = False
        self._decision_history: list[dict] = []
        self._max_decision_history = 100

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def initialize(self):
        """Initialize the agent and all components."""
        logger.info("Initializing DeFi Sentinel Agent...")
        self._state = AgentState.ANALYZING

        # Initialize LLM
        if self._settings.is_llm_configured():
            self._llm = LLMClient(self._settings)
            logger.info(f"LLM initialized: {self._settings.llm_provider.value}")
        else:
            logger.warning("LLM not configured - running in rule-based mode")

        # Initialize KeeperHub
        if self._settings.is_keeperhub_configured():
            from src.keeperhub.client import KeeperHubClient
            self._keeperhub = KeeperHubClient(self._settings)
            health = await self._keeperhub.health_check()
            if health:
                logger.info("KeeperHub connection established")
            else:
                logger.warning("KeeperHub health check failed - will retry on execution")
        else:
            logger.warning("KeeperHub not configured")

        # Initialize strategies
        await self._initialize_strategies()

        self._state = AgentState.IDLE
        logger.info("DeFi Sentinel Agent initialized successfully")

    async def _initialize_strategies(self):
        """Initialize all strategy modules."""
        from src.strategies.liquidation_shield import LiquidationShield
        from src.strategies.yield_optimizer import YieldOptimizer
        from src.strategies.rebalancer import PortfolioRebalancer

        self._strategies["liquidation_shield"] = LiquidationShield(
            self._settings, self._keeperhub
        )
        self._strategies["yield_optimizer"] = YieldOptimizer(
            self._settings, self._keeperhub
        )
        self._strategies["rebalancer"] = PortfolioRebalancer(
            self._settings, self._keeperhub
        )

        logger.info(f"Initialized {len(self._strategies)} strategies")

    async def analyze_portfolio(self, portfolio: PortfolioState) -> list[AgentDecision]:
        """Analyze portfolio state and generate decisions.

        Combines strategy analysis with LLM reasoning.
        """
        self._state = AgentState.ANALYZING
        logger.info("Analyzing portfolio state...")

        # Collect strategy recommendations
        all_recommendations: list[dict] = []
        for name, strategy in self._strategies.items():
            try:
                recommendations = await strategy.analyze(portfolio)
                all_recommendations.extend(recommendations)
                logger.debug(f"Strategy '{name}' produced {len(recommendations)} recommendations")
            except Exception as e:
                logger.error(f"Strategy '{name}' failed: {e}")

        # Use LLM to prioritize and validate decisions
        if self._llm and all_recommendations:
            decisions = await self._llm_decision(all_recommendations, portfolio)
        else:
            # Rule-based fallback
            decisions = self._rule_based_decision(all_recommendations)

        # Log decisions
        for decision in decisions:
            self._decision_history.append(decision.to_dict())
            if len(self._decision_history) > self._max_decision_history:
                self._decision_history.pop(0)

        self._state = AgentState.IDLE
        return decisions

    async def _llm_decision(
        self, recommendations: list[dict], portfolio: PortfolioState
    ) -> list[AgentDecision]:
        """Use LLM to process recommendations into final decisions."""
        context = json.dumps({
            "portfolio": portfolio.to_dict(),
            "recommendations": recommendations,
        }, indent=2, default=str)

        response = await self._llm.structured_response(
            system_prompt=self.SYSTEM_PROMPT,
            user_message=f"Analyze the following portfolio state and recommendations:\n\n{context}",
            schema='{"decisions": [{"action": "string", "reason": "string", "priority": "number", "parameters": "object", "estimated_usd_impact": "number", "requires_approval": "boolean", "strategy": "string"}]}',
        )

        decisions = []
        for item in response.get("decisions", []):
            try:
                decisions.append(AgentDecision(
                    action=item.get("action", ""),
                    reason=item.get("reason", ""),
                    priority=int(item.get("priority", 3)),
                    parameters=item.get("parameters", {}),
                    estimated_usd_impact=float(item.get("estimated_usd_impact", 0)),
                    requires_approval=item.get("requires_approval", False),
                    strategy=item.get("strategy", ""),
                ))
            except (TypeError, ValueError) as e:
                logger.warning(f"Invalid decision format: {e}")

        # Sort by priority
        decisions.sort(key=lambda d: d.priority)
        return decisions

    def _rule_based_decision(self, recommendations: list[dict]) -> list[AgentDecision]:
        """Fallback rule-based decision making when LLM is unavailable."""
        decisions = []
        for rec in recommendations:
            decisions.append(AgentDecision(
                action=rec.get("action", ""),
                reason=rec.get("reason", ""),
                priority=rec.get("priority", 3),
                parameters=rec.get("parameters", {}),
                estimated_usd_impact=rec.get("estimated_usd_impact", 0),
                requires_approval=rec.get("requires_approval", True),
                strategy=rec.get("strategy", ""),
            ))
        decisions.sort(key=lambda d: d.priority)
        return decisions

    async def execute_decision(self, decision: AgentDecision) -> dict:
        """Execute a single decision through KeeperHub."""
        if not self._keeperhub:
            return {"error": "KeeperHub not configured", "decision": decision.to_dict()}

        self._state = AgentState.EXECUTING
        logger.info(f"Executing decision: {decision.action}")

        try:
            result = await self._strategies.get(decision.strategy).execute(decision)
            return {
                "success": True,
                "decision": decision.to_dict(),
                "result": result,
            }
        except Exception as e:
            logger.error(f"Decision execution failed: {e}")
            return {
                "success": False,
                "decision": decision.to_dict(),
                "error": str(e),
            }
        finally:
            self._state = AgentState.IDLE

    async def run_monitoring_loop(self):
        """Main monitoring loop - runs continuously."""
        self._is_running = True
        self._state = AgentState.MONITORING

        interval = self._settings.monitor_interval_seconds
        logger.info(f"Starting monitoring loop (interval: {interval}s)")

        while self._is_running:
            try:
                await self._monitoring_cycle()
            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Monitoring cycle failed: {e}", exc_info=True)
                self._state = AgentState.ERROR
                await asyncio.sleep(interval)

            await asyncio.sleep(interval)

        self._state = AgentState.IDLE
        logger.info("Monitoring loop stopped")

    async def _monitoring_cycle(self):
        """Single monitoring cycle: fetch state, analyze, execute."""
        self._state = AgentState.MONITORING

        # Step 1: Fetch portfolio state
        portfolio = await self._fetch_portfolio_state()

        # Step 2: Analyze and get decisions
        decisions = await self.analyze_portfolio(portfolio)

        # Step 3: Execute high-priority decisions
        for decision in decisions:
            if decision.priority <= 2:  # Execute high-priority items
                if not decision.requires_approval or decision.estimated_usd_impact <= self._settings.auto_approve_max_usd:
                    await self.execute_decision(decision)
                else:
                    logger.info(
                        f"Decision requires approval: {decision.action} "
                        f"(${decision.estimated_usd_impact:.2f})"
                    )

    async def _fetch_portfolio_state(self) -> PortfolioState:
        """Fetch current portfolio state from KeeperHub and onchain."""
        from src.utils.helpers import now_ts

        portfolio = PortfolioState(timestamp=now_ts())

        if not self._keeperhub:
            logger.warning("KeeperHub not configured - returning empty portfolio")
            return portfolio

        try:
            # Fetch wallet integration for balance info
            wallet_info = await self._keeperhub.get_wallet_integration()

            # Search for lending protocol positions
            lending_protocols = ["aave-v3", "compound", "morpho"]
            for protocol in lending_protocols:
                try:
                    actions = await self._keeperhub.search_protocol_actions(protocol=protocol)
                    # Parse positions from protocol actions
                    for action in actions:
                        if "supply" in str(action).lower() or "borrow" in str(action).lower():
                            portfolio.positions.append({
                                "token_address": action.get("token_address", ""),
                                "protocol": protocol,
                                "usd_value": float(action.get("usd_value", 0)),
                                "amount": action.get("amount", "0"),
                            })
                except Exception as e:
                    logger.debug(f"Failed to fetch {protocol} positions: {e}")

            # Calculate total value
            portfolio.total_value_usd = sum(
                p.get("usd_value", 0) for p in portfolio.positions
            )

            # Fetch health factors from lending protocols
            try:
                aave_actions = await self._keeperhub.search_protocol_actions(protocol="aave-v3")
                for action in aave_actions:
                    if "health" in str(action).lower():
                        protocol_name = action.get("protocol", "aave-v3")
                        hf = float(action.get("health_factor", 1.0))
                        portfolio.health_factors[protocol_name] = hf
            except Exception as e:
                logger.debug(f"Failed to fetch health factors: {e}")

            logger.info(
                f"Portfolio state: ${portfolio.total_value_usd:,.2f}, "
                f"{len(portfolio.positions)} positions"
            )

        except Exception as e:
            logger.error(f"Failed to fetch portfolio state: {e}")

        return portfolio

    async def stop(self):
        """Stop the agent gracefully."""
        self._is_running = False
        self._state = AgentState.SHUTTING_DOWN
        logger.info("Shutting down DeFi Sentinel Agent...")

        if self._keeperhub:
            await self._keeperhub.close()

        self._state = AgentState.IDLE
        logger.info("DeFi Sentinel Agent stopped")

    def get_status(self) -> dict:
        """Get current agent status."""
        return {
            "state": self._state.value,
            "is_running": self._is_running,
            "strategies": list(self._strategies.keys()),
            "decision_count": len(self._decision_history),
            "keeperhub_configured": bool(self._keeperhub),
            "llm_configured": bool(self._llm),
        }