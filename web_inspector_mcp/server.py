from mcp.server.fastmcp import FastMCP

from web_inspector_mcp.tools.capture_network import capture_network
from web_inspector_mcp.tools.discover_endpoints import discover_endpoints
from web_inspector_mcp.tools.extract_api_schema import extract_api_schema
from web_inspector_mcp.tools.intercept_api import intercept_api
from web_inspector_mcp.tools.measure_performance import measure_performance

mcp = FastMCP("web-inspector")

# ──────────────────────────────────────────────
# Network Intelligence
# ──────────────────────────────────────────────

@mcp.tool()
async def network_capture(url: str, wait: int = 5):
    """
    Opens a page and captures ALL network requests made during page load.
    Returns a summary with total request count, breakdown by resource type
    and domain, and the full list of captured HTTP requests.

    Use this to see everything a page loads: APIs, scripts, images, fonts, etc.

    Args:
        url:  The full URL to load and monitor.
        wait: Seconds to wait for network activity after page load (default: 5).
    """
    return await capture_network(url, wait)


@mcp.tool()
async def api_interceptor(url: str, pattern: str = '*api*', wait: int = 5):
    """
    Monitors network requests matching a URL pattern and returns their
    response bodies. Intercepts API calls the frontend makes and shows
    exactly what data they return.

    Args:
        url:     The page to load.
        pattern: Glob pattern to match against request URLs (default: '*api*').
                 Examples: '*api*', '*.json', '*graphql*', '*v1/*', '*search*'
        wait:    Seconds to wait for network activity (default: 5).
    """
    return await intercept_api(url, pattern, wait)


@mcp.tool()
async def endpoint_discovery(url: str, wait: int = 5):
    """
    Discovers all API endpoints called by a page's frontend.
    Filters out static assets (images, CSS, JS, fonts) and returns only
    the dynamic requests (XHR/Fetch) — the actual API calls the app makes.

    Useful for reverse-engineering what APIs a SPA or web app consumes.

    Args:
        url:  The page to load and analyze.
        wait: Seconds to wait for network activity (default: 5).
    """
    return await discover_endpoints(url, wait)


@mcp.tool()
async def performance_metrics(url: str, wait: int = 5):
    """
    Measures network performance for a page load.
    Returns: TTFB, DOM content loaded time, total transfer size,
    request count, status code distribution, and the top 10
    slowest and largest resources.

    Args:
        url:  The page to load and measure.
        wait: Seconds to wait for network activity (default: 5).
    """
    return await measure_performance(url, wait)


@mcp.tool()
async def api_schema_extractor(url: str, pattern: str = '*api*', wait: int = 5):
    """
    Captures API responses from a page load and reverse-engineers their
    JSON schema — field names, data types, nesting structure.

    Useful for documenting undocumented APIs by observing what the frontend
    actually receives.

    Args:
        url:     The page to load and analyze.
        pattern: Glob pattern to filter API URLs (default: '*api*').
        wait:    Seconds to wait for network activity (default: 5).
    """
    return await extract_api_schema(url, pattern, wait)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
