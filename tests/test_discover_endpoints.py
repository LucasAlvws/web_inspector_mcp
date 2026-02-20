from unittest.mock import AsyncMock, MagicMock

import pytest

from web_inspector_mcp.tools.discover_endpoints import discover_endpoints


@pytest.mark.asyncio
async def test_discover_endpoints(mock_chrome, mock_tab):
    mock_capture = MagicMock()
    mock_capture.entries = [
        {
            'request': {'url': 'http://api.domain.com/v1/users', 'method': 'GET'},
            '_resourceType': 'Fetch',
        },
        {
            'request': {'url': 'http://img.domain.com/pic.png', 'method': 'GET'},
            '_resourceType': 'Image', # Static type, will be ignored
        },
        {
            'request': {'url': 'http://example.com/', 'method': 'GET'},
            '_resourceType': 'Document', # Document type, will be ignored
        },
        {
            'request': {'url': 'http://api.domain.com/v1/users', 'method': 'GET'},
            '_resourceType': 'XHR',
        },
        {
            'request': {'url': 'invalid-url', 'method': 'POST'},
            '_resourceType': 'XHR',
        }
    ]

    mock_record_ctx = AsyncMock()
    mock_record_ctx.__aenter__.return_value = mock_capture
    mock_tab.request.record.return_value = mock_record_ctx

    res = await discover_endpoints("http://example.com", wait=0)
    assert res['page_url'] == "http://example.com"
    assert res['total_endpoints'] == 2 # v1/users and invalid-url
    assert 'api.domain.com' in res['by_domain']

    endpoints = res['endpoints']
    assert endpoints[0]['count'] == 2 # v1/users is hit twice
    assert endpoints[0]['url'] == 'http://api.domain.com/v1/users'
    assert endpoints[0]['method'] == 'GET'
