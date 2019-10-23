import asyncio

import pytest

from instagram.agents.web_agent import WebAgent
from instagram.agents.web_agent_account import WebAgentAccount
from tests.settings import creds


@pytest.fixture(scope="module")
def settings():
    return {
        "headers": {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 "
            + "Firefox/61.0"
        }
    }


@pytest.fixture(scope="module")
def agent():
    return WebAgent()


@pytest.fixture(scope="module")
def agent_account(settings):
    agent = WebAgentAccount(creds["login"])
    agent.auth(password=creds["password"], settings=settings)
    return agent


@pytest.fixture(scope="module")
def event_loop():
    return asyncio.new_event_loop()
