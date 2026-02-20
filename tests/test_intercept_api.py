from unittest.mock import AsyncMock, MagicMock

import pytest

from web_inspector_mcp.tools.intercept_api import intercept_api


@pytest.mark.asyncio
async def test_intercept_api(mock_chrome, mock_tab):
    mock_capture = MagicMock()
    mock_capture.entries = [
        {
            'request': {
                'url': 'http://example.com/api/v1/data',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'}
            },
            '_resourceType': 'Fetch',
            'response': {'content': {'text': '{"data": "success"}'}}
        },
        {
            'request': {
                'url': 'http://example.com/img.png',
                'method': 'GET',
            },
            '_resourceType': 'Image',
            'response': {'content': {'text': '...'}}
        }
    ]

    mock_record_ctx = AsyncMock()
    mock_record_ctx.__aenter__.return_value = mock_capture
    mock_tab.request.record.return_value = mock_record_ctx

    res = await intercept_api("http://example.com", "*api*", wait=0)

    assert res['page_url'] == "http://example.com"
    assert res['matched_count'] == 1
    assert len(res['results']) == 1

    match = res['results'][0]
    assert match['url'] == 'http://example.com/api/v1/data'
    assert match['response_body'] == {'data': 'success'}
    assert match['is_json'] is True

@pytest.mark.asyncio
async def test_intercept_api_error_response(mock_chrome, mock_tab):
    mock_capture = MagicMock()
    mock_capture.entries = [
        {
            'request': {'url': 'http://example.com/api', 'method': 'GET'},
            'response': {} # Missing content, or invalid
        }
    ]
    # For error coverage, we can mock string formatting exception or similar, but
    # intercept_api uses `resp.get('content', {}).get('text')`. If it's None, it returns None.
    # Let's just verify it handles missing response body without crashing

    mock_record_ctx = AsyncMock()
    mock_record_ctx.__aenter__.return_value = mock_capture
    mock_tab.request.record.return_value = mock_record_ctx

    res = await intercept_api("http://example.com", "*api*", wait=0)

    assert res['matched_count'] == 1
    assert res['results'][0]['response_body'] is None
