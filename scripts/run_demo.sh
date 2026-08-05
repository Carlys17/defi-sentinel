#!/bin/bash
# DeFi Sentinel Demo Script
# This script runs a demo of the agent with mock data

set -e

echo "🛡️  DeFi Sentinel Demo"
echo "======================"
echo ""

# Create logs directory
mkdir -p logs

# Run the status check
echo "📊 Checking configuration..."
python -m src.main status || echo "⚠️  Some components not configured"
echo ""

# Run health checks
echo "🔍 Running health checks..."
python -m src.main check || echo "⚠️  Some checks failed"
echo ""

echo "✅ Demo completed!"
echo ""
echo "To start the agent:"
echo "  defi-sentinel start"
echo ""
echo "To start with custom interval:"
echo "  defi-sentinel start --interval 30"