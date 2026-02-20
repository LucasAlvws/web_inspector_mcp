import asyncio
from urllib.parse import urlparse

from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent

from web_inspector_mcp.browser_session import _default_options, extract_result


async def measure_performance(url: str, wait: int = 5) -> dict:
    """
    Measures network performance metrics for a page load.

    Returns timing data, request counts, total transfer size,
    and identifies the slowest/largest resources.

    Args:
        url:  The page to load and measure.
        wait: Seconds to wait for network activity (default: 5).
    """
    requests = {}
    responses = {}
    loading_finished = {}

    async def on_request(event):
        params = event.get('params', {})
        rid = params.get('requestId')
        if rid:
            request = params.get('request', {})
            requests[rid] = {
                'url': request.get('url', ''),
                'method': request.get('method', '?'),
                'type': params.get('type', '?'),
                'timestamp': params.get('timestamp', 0),
            }

    async def on_response(event):
        params = event.get('params', {})
        rid = params.get('requestId')
        if rid:
            response = params.get('response', {})
            responses[rid] = {
                'status': response.get('status', 0),
                'mime_type': response.get('mimeType', ''),
                'encoded_data_length': response.get('encodedDataLength', 0),
                'timestamp': params.get('timestamp', 0),
            }

    async def on_finished(event):
        params = event.get('params', {})
        rid = params.get('requestId')
        if rid:
            loading_finished[rid] = {
                'encoded_data_length': params.get('encodedDataLength', 0),
                'timestamp': params.get('timestamp', 0),
            }

    async with Chrome(options=_default_options()) as browser:
        tab = await browser.start()
        await tab.enable_network_events()

        await tab._connection_handler.register_callback(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)
        await tab._connection_handler.register_callback(NetworkEvent.RESPONSE_RECEIVED, on_response)
        await tab._connection_handler.register_callback(NetworkEvent.LOADING_FINISHED, on_finished)

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
    for rid, req in requests.items():
        resp = responses.get(rid, {})
        fin = loading_finished.get(rid, {})
        size = fin.get('encoded_data_length', resp.get('encoded_data_length', 0))
        total_bytes += size

        duration_ms = 0
        if req['timestamp'] and fin.get('timestamp'):
            duration_ms = round((fin['timestamp'] - req['timestamp']) * 1000, 1)

        resources.append({
            'url': req['url'][:120],
            'method': req['method'],
            'type': req['type'],
            'status': resp.get('status', '?'),
            'size_bytes': size,
            'duration_ms': duration_ms,
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
