#!/bin/bash

echo "🤖 Setting up Autonomous Browser Agent..."
echo ""

# Check Python version
python_version=$(python3 --version 2>&1)
echo "✓ Python found: $python_version"

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo ""
echo "🌐 Installing Playwright Chromium browser..."
playwright install chromium

# Check for API key
echo ""
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY environment variable not set"
    echo "   Please set it before running:"
    echo "   export ANTHROPIC_API_KEY='your-key-here'"
else
    echo "✓ ANTHROPIC_API_KEY is set"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the agent:"
echo "  cd browser_agent"
echo "  python main.py"
