# CoPaw Tool - 嵌入式软件策略伪代码快速生成工具

## Overview

CoPaw Tool is a layered, domain-driven Python package for automatically generating standardized pseudocode from embedded software strategy documents.

## Features

- 📄 **Multi-format document support**: PDF, DOCX, DOC, PNG, JPG images
- 🤖 **LLM-powered extraction**: Optional OpenAI-compatible API for enhanced strategy extraction
- 📝 **Standardized pseudocode generation**: Outputs clean, structured pseudocode
- ✅ **Logic completeness checking**: Detects missing conditions, actions, and conflicts
- 📊 **Comprehensive reports**: Coverage scores and actionable recommendations
- 🔄 **Flexible workflow**: LangGraph-based pipeline with sequential fallback

## Architecture

```
src/copaw_tool/
├─ domain/        # Pure business logic (Pydantic models, rules, generators, checkers)
├─ adapters/      # External system adapters (LLM, file extractors, exporters)
├─ application/   # Orchestration (LangGraph workflow, services, DTOs)
├─ interfaces/    # Streamlit UI
└─ shared/        # Config, logging, exceptions, utilities
```

## Quick Start

### Installation

```bash
pip install -e ".[copaw_tool]"
```

### Run the Streamlit App

```bash
cp .env.example .env
# Edit .env with your API key
bash scripts/run_streamlit.sh
```

### Python API

```python
from copaw_tool.application.services.pseudocode_service import PseudocodeService

service = PseudocodeService()
pseudocode, ir = service.generate_from_text("""
如果 长续航开关状态==开启;
那么 长续航模式仪表提示标志==无效;
""")
print(pseudocode)
```

## Configuration

Copy `.env.example` to `.env` and set:

- `OPENAI_API_KEY`: Your OpenAI API key (optional, enables LLM features)
- `OPENAI_BASE_URL`: API base URL (default: `https://api.openai.com/v1`)
- `OPENAI_MODEL`: Model name (default: `gpt-4o`)

## Running Tests

```bash
python -m pytest tests/unit/copaw_tool/ tests/regression/ -v
```
