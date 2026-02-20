import asyncio

from web_inspector_mcp.browser_session import browser_session


async def main():
    async with browser_session() as tab:
        async with tab.request.record() as capture:
            await tab.go_to("https://httpbin.org/get")
            await asyncio.sleep(2)

        for e in capture.entries:
            if "httpbin.org/get" in e["request"]["url"]:
                print("KEYS in response:", e["response"].keys())
                print("CONTENT keys:", e["response"].get("content", {}).keys())
                print("BODY:", e["response"]["content"]["text"])

if __name__ == "__main__":
    asyncio.run(main())
