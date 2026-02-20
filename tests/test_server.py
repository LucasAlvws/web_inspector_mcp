from unittest.mock import AsyncMock

import pytest

from web_inspector_mcp.server import (
    api_interceptor,
    api_schema_extractor,
    endpoint_discovery,
    main,
    mcp,
    network_capture,
    performance_metrics,
)


@pytest.fixture
def mock_tools(monkeypatch):
    monkeypatch.setattr("web_inspector_mcp.server.capture_network", AsyncMock(return_value={"captured": True}))
    monkeypatch.setattr("web_inspector_mcp.server.intercept_api", AsyncMock(return_value={"intercepted": True}))
    monkeypatch.setattr("web_inspector_mcp.server.discover_endpoints", AsyncMock(return_value={"discovered": True}))
    monkeypatch.setattr("web_inspector_mcp.server.measure_performance", AsyncMock(return_value={"measured": True}))
    monkeypatch.setattr("web_inspector_mcp.server.extract_api_schema", AsyncMock(return_value={"extracted": True}))

@pytest.mark.asyncio
async def test_network_capture_tool(mock_tools):
    res = await network_capture("http://example.com", 2)
    assert res == {"captured": True}

@pytest.mark.asyncio
async def test_api_interceptor_tool(mock_tools):
    res = await api_interceptor("http://example.com", "*api*", 2)
    assert res == {"intercepted": True}

@pytest.mark.asyncio
async def test_endpoint_discovery_tool(mock_tools):
    res = await endpoint_discovery("http://example.com", 2)
    assert res == {"discovered": True}

@pytest.mark.asyncio
async def test_performance_metrics_tool(mock_tools):
    res = await performance_metrics("http://example.com", 2)
    assert res == {"measured": True}

@pytest.mark.asyncio
async def test_api_schema_extractor_tool(mock_tools):
    res = await api_schema_extractor("http://example.com", "*api*", 2)
    assert res == {"extracted": True}

def test_main(monkeypatch):
    mock_run = AsyncMock()
    monkeypatch.setattr(mcp, "run", mock_run)
    main()
    mock_run.assert_called_once()
