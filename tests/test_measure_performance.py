import json

import pytest
from pydoll.protocol.network.events import NetworkEvent

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

    import asyncio
    original_sleep = asyncio.sleep

    async def fake_sleep(wait):
        callbacks = {}
        for callArgs in mock_tab._connection_handler.register_callback.call_args_list:
            callbacks[callArgs[0][0]] = callArgs[0][1]

        on_request = callbacks.get(NetworkEvent.REQUEST_WILL_BE_SENT)
        on_response = callbacks.get(NetworkEvent.RESPONSE_RECEIVED)
        on_finished = callbacks.get(NetworkEvent.LOADING_FINISHED)

        await on_request({
            'params': {
                'requestId': '1',
                'timestamp': 1000.0,
                'request': {'url': 'http://example.com/api', 'method': 'GET'},
                'type': 'Fetch'
            }
        })

        await on_response({
            'params': {
                'requestId': '1',
                'timestamp': 1000.5,
                'response': {'status': 200, 'mimeType': 'application/json', 'encodedDataLength': 500}
            }
        })

        await on_finished({
            'params': {
                'requestId': '1',
                'timestamp': 1001.0,
                'encodedDataLength': 1000
            }
        })

        await on_request({'params': {'requestId': '2', 'timestamp': 1.0}})
        await on_response({'params': {'requestId': '2'}})

    try:
        asyncio.sleep = fake_sleep
        res = await measure_performance("http://example.com", wait=0)
    finally:
        asyncio.sleep = original_sleep

    assert res['page_url'] == "http://example.com"
    assert res['total_requests'] == 2
    assert res['total_transfer_bytes'] == 1000
    assert res['timing']['ttfb'] == 100
    assert len(res['slowest_resources']) == 2
    assert res['slowest_resources'][0]['duration_ms'] == 1000.0
