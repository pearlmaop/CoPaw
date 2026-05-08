from pathlib import Path
from typing import List, Optional


def render_file_uploader():
    """Render Streamlit file uploader component. Returns list of saved paths."""
    try:
        import streamlit as st
    except ImportError:
        raise RuntimeError("streamlit not installed")

    uploaded_files = st.file_uploader(
        "上传策略文档",
        type=["png", "jpg", "jpeg", "pdf", "doc", "docx"],
        accept_multiple_files=True,
        help="支持 PNG/JPG/PDF/DOC/DOCX 格式",
    )
    return uploaded_files or []
