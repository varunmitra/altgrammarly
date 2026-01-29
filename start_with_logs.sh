#!/bin/bash
# Start AltGrammarly with logs visible in terminal

cd "$(dirname "$0")"
source venv/bin/activate

echo "=================================================="
echo "Starting AltGrammarly with DEBUG logging..."
echo "Watch this terminal for detailed logs"
echo "=================================================="
echo ""

python main.py
