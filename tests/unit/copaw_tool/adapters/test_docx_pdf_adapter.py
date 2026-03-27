import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from copaw_tool.adapters.extraction.docx_pdf_adapter import DocxAdapter, PDFAdapter


def test_docx_adapter_supports():
    adapter = DocxAdapter()
    assert adapter.supports(Path("test.docx"))
    assert adapter.supports(Path("test.doc"))
    assert not adapter.supports(Path("test.pdf"))
    assert not adapter.supports(Path("test.png"))


def test_pdf_adapter_supports():
    adapter = PDFAdapter()
    assert adapter.supports(Path("test.pdf"))
    assert not adapter.supports(Path("test.docx"))
    assert not adapter.supports(Path("test.png"))


def test_docx_adapter_no_docx_library(tmp_path):
    adapter = DocxAdapter()
    fake_file = tmp_path / "test.docx"
    fake_file.write_bytes(b"fake content")
    with patch.dict("sys.modules", {"docx": None}):
        result = adapter.extract(fake_file)
    assert len(result) == 1
    assert "error" in result[0]


def test_pdf_adapter_no_pdf_library(tmp_path):
    adapter = PDFAdapter()
    fake_file = tmp_path / "test.pdf"
    fake_file.write_bytes(b"fake content")
    with patch.dict("sys.modules", {"pdfplumber": None, "fitz": None}):
        result = adapter.extract(fake_file)
    assert len(result) == 1
    assert "error" in result[0]


def test_docx_adapter_extract_success(tmp_path):
    adapter = DocxAdapter()
    fake_file = tmp_path / "test.docx"
    fake_file.write_bytes(b"fake content")

    mock_doc = MagicMock()
    mock_para = MagicMock()
    mock_para.text = "如果 充电状态==充电中"
    mock_doc.paragraphs = [mock_para]

    mock_docx_module = MagicMock()
    mock_docx_module.Document.return_value = mock_doc

    with patch.dict("sys.modules", {"docx": mock_docx_module}):
        result = adapter.extract(fake_file)
    assert len(result) == 1
    assert "如果 充电状态==充电中" in result[0]["text"]
