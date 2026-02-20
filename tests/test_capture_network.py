import pytest

from web_inspector_mcp.tools.capture_network import _parse_log, capture_network


def test_parse_log_valid():
    log = {
        'params': {
            'requestId': '123',
            'type': 'Fetch',
            'request': {
                'url': 'http://example.com/api',
                'method': 'GET',
                'headers': {'Accept': '*/*'},
                'hasPostData': False
            }
        }
    }
    parsed = _parse_log(log)
    assert parsed == {
        'request_id': '123',
        'url': 'http://example.com/api',
        'method': 'GET',
        'type': 'Fetch',
        'headers': {'Accept': '*/*'},
        'has_post_data': False
    }

def test_parse_log_no_url():
    log = {'params': {'request': {}}}
    assert _parse_log(log) is None

@pytest.mark.asyncio
async def test_capture_network(mock_chrome, mock_tab):
    mock_tab.get_network_logs.return_value = [
        {
            'params': {
                'requestId': '1',
                'type': 'Fetch',
                'request': {'url': 'http://api.domain.com/data'}
            }
        },
        {
            'params': {
                'requestId': '2',
                'type': 'Image',
                'request': {'url': 'http://img.domain.com/pic.png'}
            }
        },
        {
            'params': {
                'requestId': '3',
                'type': None,
                'request': {'url': 'invalid-url'} # Will cause exception in urlparse but handled
            }
        }
    ]

    res = await capture_network("http://example.com", wait=0)
    assert res['page_url'] == "http://example.com"
    assert res['total_requests'] == 3
    assert res['by_type'] == {'Fetch': 1, 'Image': 1, 'Unknown': 1}
    assert res['by_domain'] == {'api.domain.com': 1, 'img.domain.com': 1, '': 1}
    assert len(res['requests']) == 3
