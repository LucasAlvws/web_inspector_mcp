import asyncio
from collections import Counter
from urllib.parse import urlparse

from web_inspector_mcp.browser_session import browser_session


async def capture_network(url: str, wait: int = 5) -> dict:
    """
    Opens a page and captures ALL network requests made during page load.

    Returns a summary with total request count, breakdown by type,
    and the full list of captured requests.

    Args:
        url:  The full URL to load and monitor.
        wait: Seconds to wait for network activity after page load (default: 5).
    """
    async with browser_session() as tab:
        # Use HAR recording to capture all network activity
        async with tab.request.record() as capture:
            await tab.go_to(url)
            await asyncio.sleep(wait)

        # Process captured entries
        requests = []
        type_counts = Counter()
        domain_counts = Counter()

        for entry in capture.entries:
            req = entry['request']
            resp = entry['response']

            # Extract request info
            request_info = {
                'method': req['method'],
                'url': req['url'],
                'status': resp['status'],
                'type': entry.get('_resourceType', 'Other'),
                'timestamp': entry['startedDateTime'],
                'size': resp.get('bodySize', 0),
            }
            requests.append(request_info)

            # Count by type
            resource_type = entry.get('_resourceType', 'Other')
            type_counts[resource_type] += 1

            # Count by domain
            try:
                domain = urlparse(req['url']).netloc
                if domain:
                    domain_counts[domain] += 1
            except Exception:
                pass

        return {
            'page_url': url,
            'total_requests': len(requests),
            'by_type': dict(type_counts),
            'by_domain': dict(domain_counts),
            'requests': requests,
        }
