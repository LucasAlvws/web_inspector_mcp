from unittest.mock import AsyncMock, MagicMock

import pytest

from web_inspector_mcp.tools.capture_network import capture_network


@pytest.mark.asyncio
async def test_capture_network(mock_chrome, mock_tab):
    mock_capture = MagicMock()
    mock_capture.entries = [
        {
            'request': {
                'method': 'GET',
                'url': 'http://api.domain.com/data'
            },
            'response': {
                'status': 200,
                'bodySize': 1024
            },
            '_resourceType': 'Fetch',
            'startedDateTime': '2023-01-01T00:00:00Z'
        },
        {
            'request': {
                'method': 'GET',
                'url': 'http://img.domain.com/pic.png'
            },
            'response': {
                'status': 200,
                'bodySize': 2048
            },
            '_resourceType': 'Image',
            'startedDateTime': '2023-01-01T00:00:01Z'
        },
        {
            'request': {
                'method': 'GET',
                'url': 'invalid-url'
            },
            'response': {
                'status': 404,
                'bodySize': 0
            },
            'startedDateTime': '2023-01-01T00:00:02Z'
        }
    ]

    mock_record_ctx = AsyncMock()
    mock_record_ctx.__aenter__.return_value = mock_capture
    mock_tab.request.record.return_value = mock_record_ctx

    res = await capture_network("http://example.com", wait=0)
    assert res['page_url'] == "http://example.com"
    assert res['total_requests'] == 3
    assert res['by_type'] == {'Fetch': 1, 'Image': 1, 'Other': 1}
    assert res['by_domain'] == {'api.domain.com': 1, 'img.domain.com': 1}
    assert len(res['requests']) == 3
