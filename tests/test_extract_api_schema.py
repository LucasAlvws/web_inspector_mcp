import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from web_inspector_mcp.tools.extract_api_schema import (
    _infer_schema,
    _infer_type,
    extract_api_schema,
)


def test_infer_type():
    assert _infer_type(None) == 'null'
    assert _infer_type(True) == 'boolean'
    assert _infer_type(42) == 'integer'
    assert _infer_type(3.14) == 'number'
    assert _infer_type("hello") == 'string'
    assert _infer_type([1, 2]) == 'array<integer>'
    assert _infer_type([]) == 'array<unknown>'
    assert _infer_type({"a": 1}) == 'object'


def test_infer_schema():
    data = {"user": {"id": 1, "name": "Alice", "roles": ["admin", "user"]}}
    schema = _infer_schema(data)
    assert schema['type'] == 'object'
    assert schema['properties']['user']['type'] == 'object'
    assert schema['properties']['user']['properties']['id']['type'] == 'integer'
    assert schema['properties']['user']['properties']['roles']['type'] == 'array'
    assert schema['properties']['user']['properties']['roles']['items']['type'] == 'string'


@pytest.mark.asyncio
async def test_extract_api_schema(mock_chrome, mock_tab):
    response_data = {"id": 1, "name": "Test"}

    mock_capture = MagicMock()
    mock_capture.entries = [
        {
            'request': {'url': 'http://example.com/api/users', 'method': 'GET'},
            'response': {'content': {'text': json.dumps(response_data)}},
        }
    ]

    mock_record_ctx = AsyncMock()
    mock_record_ctx.__aenter__.return_value = mock_capture
    mock_tab.request.record.return_value = mock_record_ctx

    res = await extract_api_schema("http://example.com", "*api*", wait=0)

    assert res['apis_found'] == 1
    assert len(res['schemas']) == 1

    schema = res['schemas'][0]
    assert schema['endpoint'] == 'http://example.com/api/users'
    assert schema['method'] == 'GET'
    assert schema['response_schema']['type'] == 'object'
    assert set(schema['sample_keys']) == {'id', 'name'}


@pytest.mark.asyncio
async def test_extract_api_schema_invalid_json(mock_chrome, mock_tab):
    mock_capture = MagicMock()
    mock_capture.entries = [
        {
            'request': {'url': 'http://example.com/api', 'method': 'GET'},
            'response': {'content': {'text': '<html>Not JSON</html>'}},
        }
    ]
    mock_record_ctx = AsyncMock()
    mock_record_ctx.__aenter__.return_value = mock_capture
    mock_tab.request.record.return_value = mock_record_ctx

    res = await extract_api_schema("http://example.com", "*api*", wait=0)

    assert res['apis_found'] == 0
