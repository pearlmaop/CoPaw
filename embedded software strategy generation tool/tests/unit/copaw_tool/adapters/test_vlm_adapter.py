import pytest
from pathlib import Path
from unittest.mock import MagicMock
from copaw_tool.adapters.extraction.vlm_adapter import VLMAdapter


def test_vlm_adapter_supports():
    adapter = VLMAdapter()
    assert adapter.supports(Path("test.png"))
    assert adapter.supports(Path("test.jpg"))
    assert adapter.supports(Path("test.jpeg"))
    assert not adapter.supports(Path("test.pdf"))
    assert not adapter.supports(Path("test.docx"))


def test_vlm_adapter_no_client(tmp_path):
    adapter = VLMAdapter(llm_client=None)
    fake_image = tmp_path / "test.png"
    fake_image.write_bytes(b"\x89PNG\r\n\x1a\n")
    result = adapter.extract(fake_image)
    assert len(result) == 1
    assert "error" in result[0]


def test_vlm_adapter_with_mock_client(tmp_path):
    mock_client = MagicMock()
    mock_client.extract_from_image.return_value = "提取的策略文本"
    adapter = VLMAdapter(llm_client=mock_client)
    fake_image = tmp_path / "test.png"
    fake_image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    result = adapter.extract(fake_image)
    assert len(result) == 1
    assert result[0]["text"] == "提取的策略文本"
    assert result[0]["type"] == "image"


def test_vlm_adapter_client_exception(tmp_path):
    mock_client = MagicMock()
    mock_client.extract_from_image.side_effect = Exception("API error")
    adapter = VLMAdapter(llm_client=mock_client)
    fake_image = tmp_path / "test.png"
    fake_image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    result = adapter.extract(fake_image)
    assert "error" in result[0]
