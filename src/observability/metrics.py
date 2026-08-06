"""Prometheus metrics for DeFi Sentinel."""

import logging

from prometheus_client import Counter, Gauge, Histogram, Summary

logger = logging.getLogger(__name__)


# Agent metrics
AGENT_STATE = Gauge(
    "defi_sentinel_agent_state",
    "Current agent state (1=active, 0=idle)",
)

MONITORING_CYCLES_TOTAL = Counter(
    "defi_sentinel_monitoring_cycles_total",
    "Total number of monitoring cycles completed",
)

MONITORING_CYCLE_DURATION = Histogram(
    "defi_sentinel_monitoring_cycle_duration_seconds",
    "Time taken for a monitoring cycle",
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
)

# Decision metrics
DECISIONS_TOTAL = Counter(
    "defi_sentinel_decisions_total",
    "Total decisions made by the agent",
    ["strategy", "action"],
)

DECISION_EXECUTIONS_TOTAL = Counter(
    "defi_sentinel_decision_executions_total",
    "Total decision executions",
    ["strategy", "status"],
)

DECISION_EXECUTION_DURATION = Histogram(
    "defi_sentinel_decision_execution_duration_seconds",
    "Time taken to execute a decision",
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
)

# Portfolio metrics
PORTFOLIO_VALUE_USD = Gauge(
    "defi_sentinel_portfolio_value_usd",
    "Current portfolio value in USD",
)

PORTFOLIO_POSITIONS_COUNT = Gauge(
    "defi_sentinel_portfolio_positions_count",
    "Number of active portfolio positions",
)

HEALTH_FACTOR_MIN = Gauge(
    "defi_sentinel_health_factor_min",
    "Minimum health factor across all positions",
)

# Transaction metrics
TRANSACTIONS_TOTAL = Counter(
    "defi_sentinel_transactions_total",
    "Total onchain transactions",
    ["status", "chain"],
)

TRANSACTION_GAS_USED = Summary(
    "defi_sentinel_transaction_gas_used",
    "Gas used per transaction",
)

TRANSACTION_VALUE_USD = Summary(
    "defi_sentinel_transaction_value_usd",
    "Transaction value in USD",
)

TRANSACTION_DURATION = Histogram(
    "defi_sentinel_transaction_duration_seconds",
    "Time to confirm a transaction",
    buckets=[5, 15, 30, 60, 120, 300],
)

# Error metrics
ERRORS_TOTAL = Counter(
    "defi_sentinel_errors_total",
    "Total errors encountered",
    ["source", "error_type"],
)

# Notification metrics
NOTIFICATIONS_TOTAL = Counter(
    "defi_sentinel_notifications_total",
    "Total notifications sent",
    ["provider", "level"],
)


class MetricsCollector:
    """Collect and expose metrics."""

    def __init__(self):
        logger.info("Metrics collector initialized")

    def record_monitoring_cycle(self, duration: float):
        """Record a completed monitoring cycle."""
        MONITORING_CYCLES_TOTAL.inc()
        MONITORING_CYCLE_DURATION.observe(duration)

    def record_decision(self, strategy: str, action: str, executed: bool = False, status: str = ""):
        """Record a decision."""
        DECISIONS_TOTAL.labels(strategy=strategy, action=action).inc()
        if executed:
            DECISION_EXECUTIONS_TOTAL.labels(strategy=strategy, status=status).inc()

    def record_portfolio_update(
        self, value_usd: float, positions_count: int, min_health_factor: float
    ):
        """Record portfolio state update."""
        PORTFOLIO_VALUE_USD.set(value_usd)
        PORTFOLIO_POSITIONS_COUNT.set(positions_count)
        HEALTH_FACTOR_MIN.set(min_health_factor)

    def record_transaction(self, status: str, chain: str, gas_used: int = 0, value_usd: float = 0):
        """Record a transaction."""
        TRANSACTIONS_TOTAL.labels(status=status, chain=chain).inc()
        if gas_used:
            TRANSACTION_GAS_USED.observe(gas_used)
        if value_usd:
            TRANSACTION_VALUE_USD.observe(value_usd)

    def record_error(self, source: str, error_type: str):
        """Record an error."""
        ERRORS_TOTAL.labels(source=source, error_type=error_type).inc()

    def record_notification(self, provider: str, level: str):
        """Record a notification."""
        NOTIFICATIONS_TOTAL.labels(provider=provider, level=level).inc()
