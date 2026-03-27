"""Main Streamlit app for CoPaw Tool."""
import uuid
from pathlib import Path


def _save_uploaded_file(uploaded_file, upload_dir: Path) -> Path:
    """Save a Streamlit uploaded file to disk."""
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / f"{uuid.uuid4().hex}_{uploaded_file.name}"
    dest.write_bytes(uploaded_file.read())
    return dest


def main():
    try:
        import streamlit as st
    except ImportError:
        raise RuntimeError("streamlit is required. Install with: pip install streamlit")

    from copaw_tool.shared.config.settings import Settings
    from copaw_tool.application.workflows.strategy_workflow import build_workflow
    from copaw_tool.adapters.exporters.markdown_exporter import MarkdownExporter
    from copaw_tool.interfaces.streamlit_app.components.file_uploader import render_file_uploader
    from copaw_tool.interfaces.streamlit_app.components.pseudocode_viewer import render_pseudocode
    from copaw_tool.interfaces.streamlit_app.components.report_viewer import render_report

    st.set_page_config(page_title="嵌入式软件策略伪代码生成工具", layout="wide")
    st.title("🔧 嵌入式软件策略伪代码快速生成工具")
    st.caption("CoPaw Tool v0.1.0 — 上传策略文档，自动生成标准化伪代码并检查逻辑完整性。")

    settings = Settings.from_env()
    upload_dir = Path(settings.upload_dir)

    with st.sidebar:
        st.header("⚙️ 配置")
        api_key = st.text_input("OpenAI API Key", value=settings.llm.api_key, type="password")
        base_url = st.text_input("API Base URL", value=settings.llm.base_url)
        model = st.text_input("Model", value=settings.llm.model)
        use_llm = st.checkbox("使用 LLM 增强提取", value=bool(api_key))

    uploaded_files = render_file_uploader()

    if st.button("🚀 开始生成", type="primary", disabled=not uploaded_files):
        saved_paths = []
        for uf in uploaded_files:
            saved_paths.append(str(_save_uploaded_file(uf, upload_dir)))

        llm_client = None
        if use_llm and api_key:
            from copaw_tool.adapters.llm.openai_client import OpenAIClient
            llm_client = OpenAIClient(api_key=api_key, base_url=base_url, model=model)

        workflow = build_workflow()
        initial_state = {
            "task_id": uuid.uuid4().hex,
            "file_paths": saved_paths,
            "errors": [],
            "llm_client": llm_client,
        }

        with st.spinner("处理中，请稍候..."):
            if hasattr(workflow, "invoke"):
                final_state = workflow.invoke(initial_state)
            else:
                final_state = workflow(initial_state)

        final_output = final_state.get("final_output") or {}
        pseudocode = final_output.get("pseudocode") or final_state.get("pseudocode", "")
        report = final_output.get("report") or final_state.get("completeness_report", {})
        errors = final_state.get("errors", [])

        if errors:
            for err in errors:
                st.error(err)

        col1, col2 = st.columns(2)
        with col1:
            render_pseudocode(pseudocode)
            if pseudocode:
                exporter = MarkdownExporter()
                md_content = exporter.export_pseudocode(pseudocode)
                st.download_button(
                    "⬇️ 下载伪代码 (Markdown)",
                    data=md_content.encode("utf-8"),
                    file_name="pseudocode.md",
                    mime="text/markdown",
                )
        with col2:
            render_report(report)
            if report:
                from copaw_tool.domain.model.report_model import CompletenessReport
                try:
                    report_obj = CompletenessReport(**report)
                    exporter = MarkdownExporter()
                    md_report = exporter.export_report(report_obj)
                    st.download_button(
                        "⬇️ 下载报告 (Markdown)",
                        data=md_report.encode("utf-8"),
                        file_name="report.md",
                        mime="text/markdown",
                    )
                except Exception:
                    pass


if __name__ == "__main__":
    main()
