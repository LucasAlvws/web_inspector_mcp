import asyncio
from urllib.parse import urlparse

from web_inspector_mcp.browser_session import browser_session


async def discover_endpoints(url: str, wait: int = 5) -> dict:
    """
    Discovers all API endpoints called by a page's frontend.

    Filters out static assets (images, CSS, fonts, scripts) and returns
    only XHR/Fetch requests — the actual API calls the app makes.

    Args:
        url:  The page to load and analyze.
        wait: Seconds to wait for network activity (default: 5).
    """
    STATIC_TYPES = {'Image', 'Stylesheet', 'Font', 'Script', 'Media', 'Manifest'}

    async with browser_session() as tab:
        async with tab.request.record() as capture:
            await tab.go_to(url)
            await asyncio.sleep(wait)

        endpoints = {}

        for entry in capture.entries:
            req = entry['request']
            req_url = req['url']
            resource_type = entry.get('_resourceType', '')
            method = req['method']

            if not req_url or resource_type in STATIC_TYPES:
                continue

            # Skip the document itself
            if resource_type == 'Document':
                continue

            # Build a unique key for deduplication
            try:
                parsed = urlparse(req_url)
                # Remove query params for grouping
                clean_url = f'{parsed.scheme}://{parsed.netloc}{parsed.path}'
            except Exception:
                clean_url = req_url

            key = f'{method} {clean_url}'
            if key not in endpoints:
                endpoints[key] = {
                    'method': method,
                    'url': clean_url,
                    'full_url': req_url,
                    'type': resource_type,
                    'domain': parsed.netloc if parsed else '?',
                    'count': 0,
                    'has_query_params': bool(parsed.query) if parsed else False,
                    'has_post_data': 'postData' in req,
                }
            endpoints[key]['count'] += 1

        endpoint_list = sorted(endpoints.values(), key=lambda e: e['count'], reverse=True)

        # Group by domain
        domains = {}
        for ep in endpoint_list:
            d = ep['domain']
            if d not in domains:
                domains[d] = []
            domains[d].append(ep)

        return {
            'page_url': url,
            'total_endpoints': len(endpoint_list),
            'by_domain': {d: len(eps) for d, eps in domains.items()},
            'endpoints': endpoint_list,
        }
