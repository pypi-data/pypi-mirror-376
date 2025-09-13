import pytest
import pytest_asyncio

from unittest.mock import AsyncMock, patch, Mock

from flybase_mcp_server.__main__ import get_flybase_gene_summary, get_flybase_gene_ontology

@pytest.mark.asyncio
async def test_get_flybase_gene_summary():
    mock_response = AsyncMock()
    mock_response.raise_for_status = Mock()
    mock_response.json = Mock(return_value = {
        "resultset": {
            "result": [
                {"summary": "Some summary"}
            ]
        }
    })
    with patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_response)):
        result = await get_flybase_gene_summary("FBgn0000001")
        assert result == "Some summary"

@pytest.mark.asyncio
async def test_get_flybase_gene_ontology():
    mock_response = AsyncMock()
    mock_response.raise_for_status = Mock()
    mock_response.json = Mock(return_value={
        "resultset": {
            "result": [
                {
                    "slim_ids_order": ["GO:0008150", "GO:0009987"],
                    "slim_names_order": ["biological_process", "cellular_process"]
                }
            ]
        }
    })

    with patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_response)):
        result = await get_flybase_gene_ontology("FBgn0000001", "biological_process")

    assert isinstance(result, tuple)
    assert result[0] == "GO:0008150, GO:0009987"
    assert result[1] == "biological_process, cellular_process"

