#!/bin/bash
# View AltGrammarly logs in real-time

LOG_FILE="/Users/vmitra/Work/VibeCode/altgrammarly/altgrammarly.log"

if [ -f "$LOG_FILE" ]; then
    echo "Monitoring AltGrammarly logs (press Ctrl+C to stop)..."
    echo "=========================================="
    tail -f "$LOG_FILE"
else
    echo "Log file not found at: $LOG_FILE"
    echo "Make sure the app is running first!"
fi
