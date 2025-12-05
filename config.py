import os
from anthropic import Anthropic

# API Configuration - MUST be set via environment variable
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Using Haiku - fast and cost-effective for browser automation
MODEL = "claude-sonnet-4-5-20250929"

# Browser configuration
BROWSER_WIDTH = 1400
BROWSER_HEIGHT = 700
SLOW_MO = 300  # milliseconds delay for visibility

# Session persistence
USER_DATA_DIR = os.path.join(os.path.dirname(__file__), ".browser_session")

# Security keywords that trigger human confirmation
DESTRUCTIVE_KEYWORDS = [
    "delete", "remove", "buy", "purchase", "pay", "order", "checkout",
    "confirm payment", "submit order", "place order", "send", "transfer",
    "cancel subscription", "unsubscribe", "logout", "sign out"
]
