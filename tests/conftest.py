from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_tab():
    tab = AsyncMock()
    tab.go_to = AsyncMock()
    tab.execute_script = AsyncMock(return_value={"id": 1, "result": {"result": {"type": "string", "value": "some_value"}}})
    tab.enable_network_events = AsyncMock()
    tab.get_network_logs = AsyncMock(return_value=[])
    tab.get_network_response_body = AsyncMock(return_value="{}")

    # Needs to mock the connection handler callback registration
    tab._connection_handler = MagicMock()
    tab._connection_handler.register_callback = AsyncMock()
    return tab

@pytest.fixture
def mock_chrome(mock_tab, monkeypatch):
    chrome_instance = AsyncMock()
    chrome_instance.start = AsyncMock(return_value=mock_tab)

    # We mock out the async context manager logic:
    # async with Chrome(...) as browser:
    chrome_instance.__aenter__ = AsyncMock(return_value=chrome_instance)
    chrome_instance.__aexit__ = AsyncMock(return_value=None)

    mock_chrome_cls = MagicMock(return_value=chrome_instance)
    monkeypatch.setattr("web_inspector_mcp.browser_session.Chrome", mock_chrome_cls)
    monkeypatch.setattr("web_inspector_mcp.tools.extract_api_schema.Chrome", mock_chrome_cls)
    monkeypatch.setattr("web_inspector_mcp.tools.intercept_api.Chrome", mock_chrome_cls)
    monkeypatch.setattr("web_inspector_mcp.tools.measure_performance.Chrome", mock_chrome_cls)
    return chrome_instance
