import pytest

from web_inspector_mcp.browser_session import (
    _default_options,
    browser_session,
    extract_result,
    network_session,
    run_js,
)


def test_default_options():
    options = _default_options()
    assert options is not None

def test_extract_result_dict_json():
    # Value is an actual JSON string that needs parsing
    raw = {'id': 1, 'result': {'result': {'type': 'string', 'value': '{"a": 1}'}}}
    assert extract_result(raw) == {"a": 1}

def test_extract_result_dict_plain_str():
    # Value is a literal string, not JSON
    raw = {'id': 1, 'result': {'result': {'type': 'string', 'value': 'hello'}}}
    assert extract_result(raw) == 'hello'

def test_extract_result_dict_int():
    # Value is an integer
    raw = {'id': 1, 'result': {'result': {'type': 'number', 'value': 42}}}
    assert extract_result(raw) == 42

def test_extract_result_malformed():
    raw = {'id': 1, 'result': {}}
    assert extract_result(raw) == raw

def test_extract_result_non_dict():
    assert extract_result("not a dict") == "not a dict"

@pytest.mark.asyncio
async def test_browser_session(mock_chrome, mock_tab):
    async with browser_session("http://example.com") as tab:
        assert tab == mock_tab
        tab.go_to.assert_awaited_once_with("http://example.com")

@pytest.mark.asyncio
async def test_network_session(mock_chrome, mock_tab):
    async with network_session("http://example.com", wait_seconds=0) as (tab, logs):
        assert tab == mock_tab
        assert logs == []
        tab.enable_network_events.assert_awaited_once()
        tab.go_to.assert_awaited_once_with("http://example.com")

@pytest.mark.asyncio
async def test_run_js(mock_chrome, mock_tab):
    result = await run_js("http://example.com", "return 1;")
    assert result == "some_value"
    mock_tab.go_to.assert_awaited_once_with("http://example.com")
    mock_tab.execute_script.assert_awaited_once_with("return 1;")
