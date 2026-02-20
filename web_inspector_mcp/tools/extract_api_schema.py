import asyncio
import json
from urllib.parse import urlparse

from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent

from web_inspector_mcp.browser_session import _default_options


def _infer_type(value) -> str:
    """Infer a simple type name from a JSON value."""
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, int):
        return 'integer'
    if isinstance(value, float):
        return 'number'
    if isinstance(value, str):
        return 'string'
    if isinstance(value, list):
        if value:
            return f'array<{_infer_type(value[0])}>'
        return 'array<unknown>'
    if isinstance(value, dict):
        return 'object'
    return type(value).__name__


def _infer_schema(data, max_depth: int = 3, depth: int = 0) -> dict:
    """Recursively infer a JSON schema-like structure from data."""
    if depth >= max_depth:
        return {'type': _infer_type(data)}

    if isinstance(data, dict):
        properties = {}
        for key, value in data.items():
            properties[key] = _infer_schema(value, max_depth, depth + 1)
        return {'type': 'object', 'properties': properties}

    if isinstance(data, list) and data:
        item_schema = _infer_schema(data[0], max_depth, depth + 1)
        return {'type': 'array', 'items': item_schema, 'length': len(data)}

    return {'type': _infer_type(data)}


async def extract_api_schema(url: str, pattern: str = '*api*', wait: int = 5) -> dict:
    """
    Captures API responses from a page load and infers their JSON schema.

    Finds all requests matching the pattern that return JSON, then
    reverse-engineers the response structure (field names, types, nesting).

    Args:
        url:     The page to load and analyze.
        pattern: Glob pattern to filter API URLs (default: '*api*').
        wait:    Seconds to wait for network activity (default: 5).
    """
    import fnmatch

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
            }

    async with Chrome(options=_default_options()) as browser:
        tab = await browser.start()
        await tab.enable_network_events()

        await tab._connection_handler.register_callback(
            NetworkEvent.REQUEST_WILL_BE_SENT, on_request
        )

        await tab.go_to(url)
        await asyncio.sleep(wait)

        schemas = []
        for rid, req_info in matched_requests.items():
            try:
                body_raw = await tab.get_network_response_body(rid)
                body = body_raw if isinstance(body_raw, str) else str(body_raw)

                parsed = json.loads(body)
                schema = _infer_schema(parsed)

                try:
                    parsed_url = urlparse(req_info['url'])
                    endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                except Exception:
                    endpoint = req_info['url']

                schemas.append({
                    'endpoint': endpoint,
                    'method': req_info['method'],
                    'full_url': req_info['url'],
                    'response_schema': schema,
                    'sample_keys': list(parsed.keys()) if isinstance(parsed, dict) else None,
                })
            except (json.JSONDecodeError, TypeError):
                continue
            except Exception:
                continue

    return {
        'page_url': url,
        'pattern': pattern,
        'apis_found': len(schemas),
        'schemas': schemas,
    }
