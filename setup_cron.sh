#!/bin/bash
# ============================================================
# AI Newsletter Bot — Cron Setup
# ============================================================
# Installs a cron job to run the newsletter daily.
# Default: 8:00 AM IST (02:30 UTC)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/venv/bin/python"
MAIN="$SCRIPT_DIR/main.py"
LOG="$SCRIPT_DIR/logs/cron.log"

echo ""
echo "⏰ Setting up daily cron job..."
echo ""

# Check venv exists
if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Parse time from config
SEND_TIME=$(grep "time:" "$SCRIPT_DIR/config.yaml" | head -1 | awk -F'"' '{print $2}')
HOUR=$(echo "$SEND_TIME" | cut -d: -f1)
MINUTE=$(echo "$SEND_TIME" | cut -d: -f2)

# Convert IST to UTC (IST = UTC + 5:30)
UTC_MINUTE=$((MINUTE - 30))
UTC_HOUR=$((HOUR - 5))

if [ $UTC_MINUTE -lt 0 ]; then
    UTC_MINUTE=$((UTC_MINUTE + 60))
    UTC_HOUR=$((UTC_HOUR - 1))
fi

if [ $UTC_HOUR -lt 0 ]; then
    UTC_HOUR=$((UTC_HOUR + 24))
fi

CRON_ENTRY="$UTC_MINUTE $UTC_HOUR * * * cd $SCRIPT_DIR && $PYTHON $MAIN >> $LOG 2>&1"

echo "📋 Cron schedule:"
echo "   Config time:  ${SEND_TIME} IST"
echo "   UTC time:     $(printf '%02d:%02d' $UTC_HOUR $UTC_MINUTE) UTC"
echo "   Cron entry:   $CRON_ENTRY"
echo ""

# Check if already installed
if crontab -l 2>/dev/null | grep -q "$MAIN"; then
    echo "⚠️  Existing cron job found. Replacing..."
    crontab -l 2>/dev/null | grep -v "$MAIN" | crontab -
fi

# Install cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job installed!"
echo ""
echo "Useful commands:"
echo "  View cron jobs:    crontab -l"
echo "  View logs:         tail -f $LOG"
echo "  Remove cron job:   crontab -e  (then delete the line)"
echo ""
