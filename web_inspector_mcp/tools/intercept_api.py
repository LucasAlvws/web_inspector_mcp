import asyncio
import fnmatch
import json

from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent

from web_inspector_mcp.browser_session import _default_options


async def intercept_api(url: str, pattern: str = '*api*', wait: int = 5) -> dict:
    """
    Monitors network requests matching a URL pattern and returns their
    response bodies. Useful for seeing what APIs a page calls.

    Args:
        url:     The page to load.
        pattern: Glob pattern to match against request URLs (default: '*api*').
                 Examples: '*api*', '*.json', '*graphql*', '*v1/*'
        wait:    Seconds to wait for network activity (default: 5).
    """
    matched_requests = {}

    async def on_request(event):
        params = event.get('params', {})
        request = params.get('request', {})
        req_url = request.get('url', '')
        rid = params.get('requestId')
        if rid and fnmatch.fnmatch(req_url.lower(), pattern.lower()):
            matched_requests[rid] = {
                'url': req_url,
                'method': request.get('method', '?'),
                'type': params.get('type'),
                'headers': request.get('headers', {}),
            }

    async with Chrome(options=_default_options()) as browser:
        tab = await browser.start()
        await tab.enable_network_events()

        await tab._connection_handler.register_callback(
            NetworkEvent.REQUEST_WILL_BE_SENT, on_request
        )

        await tab.go_to(url)
        await asyncio.sleep(wait)

        # Try to get response bodies for matched requests
        results = []
        for rid, req_info in matched_requests.items():
            try:
                body_raw = await tab.get_network_response_body(rid)
                body = body_raw if isinstance(body_raw, str) else str(body_raw)

                # Try to parse as JSON
                parsed = None
                try:
                    parsed = json.loads(body)
                except (json.JSONDecodeError, TypeError):
                    pass

                results.append({
                    **req_info,
                    'response_body': parsed if parsed else body[:2000],
                    'is_json': parsed is not None,
                })
            except Exception as e:
                results.append({
                    **req_info,
                    'response_body': None,
                    'error': str(e),
                })

    return {
        'page_url': url,
        'pattern': pattern,
        'matched_count': len(results),
        'results': results,
    }
