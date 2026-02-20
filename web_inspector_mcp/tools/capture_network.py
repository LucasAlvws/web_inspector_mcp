
from web_inspector_mcp.browser_session import network_session


def _parse_log(log: dict) -> dict | None:
    """Parse a single network log entry into a clean dict."""
    params = log.get('params', {})
    request = params.get('request', {})
    url = request.get('url')
    if not url:
        return None
    return {
        'request_id': params.get('requestId'),
        'url': url,
        'method': request.get('method', '?'),
        'type': params.get('type'),
        'headers': request.get('headers', {}),
        'has_post_data': request.get('hasPostData', False),
    }


async def capture_network(url: str, wait: int = 5) -> dict:
    """
    Opens a page and captures ALL network requests made during page load.

    Returns a summary with total request count, breakdown by type,
    and the full list of captured requests.

    Args:
        url:  The full URL to load and monitor.
        wait: Seconds to wait for network activity after page load (default: 5).
    """
    async with network_session(url, wait_seconds=wait) as (tab, logs):
        requests = []
        for log in logs:
            parsed = _parse_log(log)
            if parsed:
                requests.append(parsed)

        # Group by type
        type_counts = {}
        for req in requests:
            t = req['type'] or 'Unknown'
            type_counts[t] = type_counts.get(t, 0) + 1

        # Group by domain
        from urllib.parse import urlparse
        domain_counts = {}
        for req in requests:
            try:
                domain = urlparse(req['url']).netloc
            except Exception:
                domain = 'unknown'
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        return {
            'page_url': url,
            'total_requests': len(requests),
            'by_type': type_counts,
            'by_domain': domain_counts,
            'requests': requests,
        }
