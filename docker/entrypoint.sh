#!/bin/bash
set -e

echo "================================================"
echo "  LimaCharlie Claude Code Environment"
echo "================================================"
echo ""
echo "The lc-essentials plugin is pre-configured."
echo ""
echo "On first run, authenticate with LimaCharlie:"
echo "  /mcp"
echo ""
echo "This opens your browser for OAuth. Once approved,"
echo "you're ready to use all LimaCharlie skills!"
echo "================================================"
echo ""

# Launch Claude Code
exec claude "$@"
