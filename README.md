# 🔍 Web Inspector MCP

A **Model Context Protocol (MCP) server** for network intelligence, powered by [Pydoll](https://pydoll.tech/). It gives LLMs the ability to capture, intercept, and analyze all network traffic from any web page — using a real headless Chromium browser under the hood.

## ✨ Features

| Tool | Description |
|---|---|
| `network_capture` | Captures **all** HTTP requests during page load |
| `api_interceptor` | Filters requests by URL pattern and returns response bodies |
| `endpoint_discovery` | Maps API endpoints the frontend calls (ignores static assets) |
| `performance_metrics` | Measures TTFB, transfer size, slowest/largest resources |
| `api_schema_extractor` | Reverse-engineers JSON schema from API responses |

## 📦 Installation

```bash
pip install mcp pydoll-python
```

## 🚀 Usage Examples

Here are example prompts you can use with any LLM that supports MCP:

### `network_capture` — See everything a page loads

> *"Open https://mercadolivre.com.br and show me all the network requests it makes on load. I want to see the domains and resource types."*

---

### `api_interceptor` — Intercept API calls and read their responses

> *"Go to https://github.com/autoscrape-labs/pydoll and intercept all requests that contain `*api*` in the URL. Show me the JSON each API returns."*

---

### `endpoint_discovery` — Map all API endpoints a frontend uses

> *"Discover all API endpoints that the frontend at https://pydoll.tech/ calls. Ignore static files like CSS and images."*

---

### `performance_metrics` — Measure network performance

> *"Measure the network performance of https://g1.globo.com/. I want the TTFB, total page weight, and the top 10 heaviest and slowest resources."*

---

### `api_schema_extractor` — Reverse-engineer API contracts

> *"Open https://pydoll.tech/ and capture the JSON responses from the APIs it calls. Reverse-engineer the schema of each API — I want to know the fields, types, and structure."*

---

### 💡 Combining tools

> *"First run a `network_capture` on https://mysite.com, then use `api_interceptor` with pattern `*graphql*` to see what the GraphQL API returns, and finally extract the schema with `api_schema_extractor`."*

## ⚙️ Configuration

Add this to your MCP client config:

```json
{
  "mcpServers": {
    "web-inspector": {
      "command": "python",
      "args": ["-m", "web_inspector_mcp.server"]
    }
  }
}
```

## 📄 License

MIT