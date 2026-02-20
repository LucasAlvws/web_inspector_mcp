import pytest

from web_inspector_mcp.tools.discover_endpoints import discover_endpoints


@pytest.mark.asyncio
async def test_discover_endpoints(mock_chrome, mock_tab):
    mock_tab.get_network_logs.return_value = [
        {
            'params': {
                'requestId': '1',
                'type': 'Fetch',
                'request': {'url': 'http://api.domain.com/v1/users', 'method': 'GET'}
            }
        },
        {
            'params': {
                'requestId': '2',
                'type': 'Image', # Static type, will be ignored
                'request': {'url': 'http://img.domain.com/pic.png', 'method': 'GET'}
            }
        },
        {
            'params': {
                'requestId': '3',
                'type': 'Document', # Document type, will be ignored
                'request': {'url': 'http://example.com/', 'method': 'GET'}
            }
        },
        {
            'params': {
                'requestId': '4',
                'type': 'XHR',
                'request': {'url': 'http://api.domain.com/v1/users', 'method': 'GET'} # Duplicate to count up
            }
        },
        {
            'params': {
                'requestId': '5',
                'type': 'XHR',
                'request': {'url': 'invalid-url', 'method': 'POST'} # Will be kept despite parsing err
            }
        }
    ]

    res = await discover_endpoints("http://example.com", wait=0)
    assert res['page_url'] == "http://example.com"
    assert res['total_endpoints'] == 2 # v1/users and invalid-url
    assert 'api.domain.com' in res['by_domain']

    endpoints = res['endpoints']
    assert endpoints[0]['count'] == 2 # v1/users is hit twice
    assert endpoints[0]['url'] == 'http://api.domain.com/v1/users'
    assert endpoints[0]['method'] == 'GET'
