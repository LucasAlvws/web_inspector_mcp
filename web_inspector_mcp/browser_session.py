import json as _json
from contextlib import asynccontextmanager

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


def _default_options() -> ChromiumOptions:
    options = ChromiumOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return options


def extract_result(raw):
    """
    Unwraps pydoll's CDP envelope and returns the actual value.

    pydoll's ``execute_script`` returns::

        {'id': N, 'result': {'result': {'type': 'string', 'value': '...'}}}

    This helper digs into that structure and returns just the value.
    If the value is a JSON string, it is parsed automatically.
    """
    if not isinstance(raw, dict):
        return raw
    try:
        inner = raw['result']['result']
    except (KeyError, TypeError):
        return raw

    value = inner.get('value', inner)

    if isinstance(value, str):
        try:
            return _json.loads(value)
        except (_json.JSONDecodeError, ValueError):
            return value

    return value


@asynccontextmanager
async def browser_session(url: str):
    """
    Async context manager that opens a headless Chrome, navigates to `url`,
    and yields the active tab.
    """
    async with Chrome(options=_default_options()) as browser:
        tab = await browser.start()
        await tab.go_to(url)
        yield tab


@asynccontextmanager
async def network_session(url: str, wait_seconds: int = 5):
    """
    Async context manager that opens Chrome with network monitoring enabled
    BEFORE navigation, navigates to `url`, waits for network activity to
    settle, and yields (tab, logs).

    The key difference from `browser_session` is that network events are
    enabled before `go_to()`, so ALL requests (including the initial
    document load) are captured.
    """
    import asyncio

    async with Chrome(options=_default_options()) as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        await tab.go_to(url)
        await asyncio.sleep(wait_seconds)
        logs = await tab.get_network_logs()
        yield tab, logs


async def run_js(url: str, js: str):
    """Shortcut: opens a browser, runs JS, and returns the extracted result."""
    async with browser_session(url) as tab:
        raw = await tab.execute_script(js)
        return extract_result(raw)
