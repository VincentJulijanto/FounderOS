"""
Shared test configuration for the FounderOS suite.

The test suite is hermetic: it must run keyless and offline, exercising the
mock fixtures of every agent / provider / MCP method. If a real QWEN_API_KEY
happens to be present in .env (live mode), unit tests would otherwise make
network calls and hang. We force mock mode for the whole session so the suite
behaves the same with or without credentials. A live smoke test (Sprint B) is
run deliberately and separately, never through this suite.
"""

from backend.config import settings
from backend.mcp.client import mcp_client

# Force mock mode at import time — before any agent / provider is constructed.
settings.use_mock_llm = True
# The singleton computed .live at import; pin it to mock to stay offline.
mcp_client.live = False
