import pytest
import os
from typing import Optional


@pytest.fixture
def get_config() -> tuple[Optional[str], Optional[str]]:
    api_key = os.getenv("AGENTPILOT_API_KEY")
    api_url = os.getenv("AGENTPILOT_API_URL")
    return api_key, api_url
