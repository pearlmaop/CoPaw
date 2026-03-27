import pytest
import importlib


def test_app_module_importable():
    """Smoke test: verify app module can be imported."""
    try:
        import copaw_tool.interfaces.streamlit_app.app as app_module
        assert hasattr(app_module, "main")
    except ImportError as e:
        pytest.skip(f"Import error (likely streamlit not installed): {e}")


def test_components_importable():
    """Verify component modules are importable."""
    from copaw_tool.interfaces.streamlit_app.components import file_uploader
    from copaw_tool.interfaces.streamlit_app.components import pseudocode_viewer
    from copaw_tool.interfaces.streamlit_app.components import report_viewer
    assert callable(file_uploader.render_file_uploader)
    assert callable(pseudocode_viewer.render_pseudocode)
    assert callable(report_viewer.render_report)


def test_main_function_exists():
    """Verify main function exists in app module."""
    from copaw_tool.interfaces.streamlit_app import app
    assert callable(app.main)
