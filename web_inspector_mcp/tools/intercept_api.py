import asyncio
import fnmatch
import json

from web_inspector_mcp.browser_session import browser_session


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
    async with browser_session() as tab:
        async with tab.request.record() as capture:
            await tab.go_to(url)
            await asyncio.sleep(wait)

        # Try to get response bodies for matched requests
        results = []
        for entry in capture.entries:
            req = entry['request']
            resp = entry['response']
            req_url = req['url']

            if not fnmatch.fnmatch(req_url.lower(), pattern.lower()):
                continue

            body_raw = resp.get('content', {}).get('text')

            req_info = {
                'url': req_url,
                'method': req.get('method', '?'),
                'type': entry.get('_resourceType'),
                'headers': req.get('headers', {}),
            }

            try:
                # If body_raw is None, we just set body to empty string for parsing check,
                # but keep track that it's actually missing
                body = body_raw if isinstance(body_raw, str) else str(body_raw) if body_raw is not None else ""

                # Try to parse as JSON
                parsed = None
                if body_raw is not None:
                    try:
                        parsed = json.loads(body)
                    except (json.JSONDecodeError, TypeError):
                        pass

                results.append({
                    **req_info,
                    'response_body': parsed if parsed else (body[:2000] if body_raw is not None else None),
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
