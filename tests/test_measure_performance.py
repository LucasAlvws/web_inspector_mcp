import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from web_inspector_mcp.tools.measure_performance import measure_performance


@pytest.mark.asyncio
async def test_measure_performance(mock_chrome, mock_tab):
    mock_tab.execute_script.return_value = {
        'id': 1,
        'result': {
            'result': {
                'value': json.dumps({'ttfb': 100, 'transfer_size': 1024})
            }
        }
    }

    mock_capture = MagicMock()
    mock_capture.entries = [
        {
            'request': {
                'url': 'http://example.com/api',
                'method': 'GET'
            },
            '_resourceType': 'Fetch',
            'response': {
                'status': 200,
                'bodySize': 1000
            },
            'time': 1000.0
        },
        {
            'request': {
                'url': 'http://example.com/img',
                'method': 'GET'
            },
            '_resourceType': 'Image',
            'response': {
                'status': 200,
                'bodySize': 0
            },
            'time': 0
        }
    ]

    mock_record_ctx = AsyncMock()
    mock_record_ctx.__aenter__.return_value = mock_capture
    mock_tab.request.record.return_value = mock_record_ctx

    res = await measure_performance("http://example.com", wait=0)

    assert res['page_url'] == "http://example.com"
    assert res['total_requests'] == 2
    assert res['total_transfer_bytes'] == 1000
    assert res['timing']['ttfb'] == 100
    assert len(res['slowest_resources']) == 2
    assert res['slowest_resources'][0]['duration_ms'] == 1000.0
