import asyncio
from urllib.parse import urlparse

from web_inspector_mcp.browser_session import browser_session, extract_result


async def measure_performance(url: str, wait: int = 5) -> dict:
    """
    Measures network performance metrics for a page load.

    Returns timing data, request counts, total transfer size,
    and identifies the slowest/largest resources.

    Args:
        url:  The page to load and measure.
        wait: Seconds to wait for network activity (default: 5).
    """
    async with browser_session() as tab:
        async with tab.request.record() as capture:
            await tab.go_to(url)
            await asyncio.sleep(wait)

        # Also get Navigation Timing from the browser
        timing_raw = await tab.execute_script("""
        (() => {
          const t = performance.timing;
          const nav = performance.getEntriesByType('navigation')[0] || {};
          return JSON.stringify({
            dom_content_loaded: t.domContentLoadedEventEnd - t.navigationStart,
            load_event: t.loadEventEnd - t.navigationStart,
            ttfb: t.responseStart - t.navigationStart,
            dns: t.domainLookupEnd - t.domainLookupStart,
            connect: t.connectEnd - t.connectStart,
            transfer_size: nav.transferSize || 0,
            decoded_body_size: nav.decodedBodySize || 0,
          });
        })()
        """)
        timing = extract_result(timing_raw)

    # Compute metrics
    resources = []
    total_bytes = 0
    for entry in capture.entries:
        req = entry['request']
        resp = entry['response']

        size = resp.get('bodySize', 0)
        if size < 0:
            size = resp.get('_transferSize', 0)
        if size < 0:
            size = 0

        total_bytes += size

        duration_ms = entry.get('time', 0)

        resources.append({
            'url': req['url'][:120],
            'method': req['method'],
            'type': entry.get('_resourceType', '?'),
            'status': resp.get('status', '?'),
            'size_bytes': size,
            'duration_ms': round(duration_ms, 1),
        })

    resources.sort(key=lambda r: r['duration_ms'], reverse=True)

    # Status code distribution
    status_dist = {}
    for r in resources:
        s = str(r['status'])
        status_dist[s] = status_dist.get(s, 0) + 1

    # Domain breakdown
    domain_sizes = {}
    for r in resources:
        try:
            domain = urlparse(r['url']).netloc
        except Exception:
            domain = 'unknown'
        domain_sizes[domain] = domain_sizes.get(domain, 0) + r['size_bytes']

    return {
        'page_url': url,
        'timing': timing if isinstance(timing, dict) else {},
        'total_requests': len(resources),
        'total_transfer_bytes': total_bytes,
        'total_transfer_kb': round(total_bytes / 1024, 1),
        'status_codes': status_dist,
        'transfer_by_domain': {d: round(s / 1024, 1) for d, s in domain_sizes.items()},
        'slowest_resources': resources[:10],
        'largest_resources': sorted(resources, key=lambda r: r['size_bytes'], reverse=True)[:10],
    }
