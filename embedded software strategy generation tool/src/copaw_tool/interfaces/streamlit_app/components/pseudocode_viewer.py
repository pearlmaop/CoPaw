def render_pseudocode(pseudocode: str):
    """Render pseudocode in Streamlit."""
    try:
        import streamlit as st
    except ImportError:
        raise RuntimeError("streamlit not installed")

    st.subheader("📝 标准化伪代码")
    if pseudocode:
        st.code(pseudocode, language="text")
    else:
        st.info("暂无伪代码，请先上传文件并开始生成。")
