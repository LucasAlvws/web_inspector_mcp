import pytest
from pydoll.protocol.network.events import NetworkEvent

from web_inspector_mcp.tools.intercept_api import intercept_api


@pytest.mark.asyncio
async def test_intercept_api(mock_chrome, mock_tab):
    mock_tab.get_network_response_body.return_value = '{"data": "success"}'

    # We will let the tool run, but since it sleeps, we can mock `asyncio.sleep` to be fast,
    # or just let it wait 0 seconds.
    # To trigger the callback, we have to intercept the `register_callback` call.

    # We patch asyncio.sleep so we can inject events while it's "sleeping"
    import asyncio
    original_sleep = asyncio.sleep

    async def fake_sleep(wait):
        # Find the registered callback
        callback = None
        for callArgs in mock_tab._connection_handler.register_callback.call_args_list:
            if callArgs[0][0] == NetworkEvent.REQUEST_WILL_BE_SENT:
                callback = callArgs[0][1]
                break

        if callback:
            # Inject an event
            event = {
                'params': {
                    'requestId': '123',
                    'type': 'Fetch',
                    'request': {
                        'url': 'http://example.com/api/v1/data',
                        'method': 'POST',
                        'headers': {'Content-Type': 'application/json'}
                    }
                }
            }
            await callback(event)

            # Inject another event that doesn't match
            event2 = {
                'params': {
                    'requestId': '124',
                    'type': 'Image',
                    'request': {
                        'url': 'http://example.com/img.png',
                        'method': 'GET',
                    }
                }
            }
            await callback(event2)

    try:
        asyncio.sleep = fake_sleep
        res = await intercept_api("http://example.com", "*api*", wait=0)
    finally:
        asyncio.sleep = original_sleep

    assert res['page_url'] == "http://example.com"
    assert res['matched_count'] == 1
    assert len(res['results']) == 1

    match = res['results'][0]
    assert match['url'] == 'http://example.com/api/v1/data'
    assert match['response_body'] == {'data': 'success'}
    assert match['is_json'] is True

@pytest.mark.asyncio
async def test_intercept_api_error_response(mock_chrome, mock_tab):
    mock_tab.get_network_response_body.side_effect = Exception("Failed to fetch body")

    import asyncio
    original_sleep = asyncio.sleep

    async def fake_sleep(wait):
        callback = mock_tab._connection_handler.register_callback.call_args[0][1]
        await callback({
            'params': {
                'requestId': '123',
                'request': {'url': 'http://example.com/api', 'method': 'GET'}
            }
        })

    try:
        asyncio.sleep = fake_sleep
        res = await intercept_api("http://example.com", "*api*", wait=0)
    finally:
        asyncio.sleep = original_sleep

    assert res['matched_count'] == 1
    assert res['results'][0]['error'] == "Failed to fetch body"
