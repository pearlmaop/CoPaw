from typing import Dict, Any


def render_report(report: Dict[str, Any]):
    """Render completeness report in Streamlit."""
    try:
        import streamlit as st
    except ImportError:
        raise RuntimeError("streamlit not installed")

    st.subheader("📊 逻辑完整性报告")
    if not report:
        st.info("暂无报告。")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("规则总数", report.get("total_rules", 0))
    with col2:
        st.metric("问题数量", report.get("issue_count", 0))
    with col3:
        st.metric("覆盖度评分", f"{report.get('coverage_score', 0):.1f}%")

    issues = report.get("issues", [])
    if issues:
        st.warning(f"发现 {len(issues)} 个问题：")
        for issue in issues:
            severity = issue.get("severity", "low")
            emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
            st.write(f"{emoji} **[{severity.upper()}]** {issue.get('message', '')}")
            if issue.get("suggestion"):
                st.caption(f"建议：{issue['suggestion']}")

    conclusion = report.get("conclusion", "")
    if conclusion:
        st.info(f"**结论：** {conclusion}")

    recommendations = report.get("recommendations", [])
    if recommendations:
        st.subheader("改进建议")
        for rec in recommendations:
            st.write(f"- {rec}")
