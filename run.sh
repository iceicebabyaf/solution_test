#!/bin/bash

# Simple run script for the browser agent

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run setup first:"
    echo "  python3 -m venv venv"
    echo "  ./venv/bin/pip install -r requirements.txt"
    echo "  ./venv/bin/playwright install chromium"
    exit 1
fi

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set"
    echo "Please set it: export ANTHROPIC_API_KEY='your-key'"
    exit 1
fi

# Run the agent
./venv/bin/python3 main.py
