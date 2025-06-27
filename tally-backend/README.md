# Tally Tabular Review Backend

FastAPI backend for the Tally Tabular Review application - an AI-powered document analysis and audit tool.

## Quick Start with Simple API Server

For testing and development purposes, you can run the simplified API server that doesn't require PostgreSQL:

1. Install dependencies:
```bash
pip install fastapi uvicorn python-multipart openai reductoai supabase httpx
```

2. Run the simple API server:
```bash
python simple_api_server.py
```

The server will start on http://localhost:8001 with the following endpoints:
- `/health` - Check server health
- `/test_storage` - Test Supabase storage
- `/upload_document` - Upload documents
- `/reducto/upload_parse` - Parse documents with Reducto
- `/openai/completion` - Test OpenAI completions
- `/reducto/openai` - Process documents with Reducto and OpenAI
- `/reducto/batch_process` - Batch process documents with controls

API documentation is available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Full Application Features

## Features

- **Document Upload & Storage**: Supabase integration for secure file storage
- **AI-Powered Analysis**: OpenAI GPT integration for document Q&A
- **Document Parsing**: Reducto API integration for computer vision and OCR
- **Tabular Interface**: RESTful APIs for tabular data management
- **Async Processing**: Background task processing for AI operations

## Technologies

- **FastAPI**: Modern async web framework
- **SQLAlchemy**: Async ORM with PostgreSQL
- **OpenAI**: GPT models for document analysis
- **Reducto**: Document parsing and computer vision
- **Supabase**: Database and file storage
- **uv**: Fast Python package management

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Supabase account
- OpenAI API key
- Reducto API key

### Installation

1. Install dependencies:
```bash
uv sync
```

2. Configure settings in `.secrets.toml`:
```toml
[default]
OPENAI_API_KEY = "your_openai_key"
REDUCTO_API_KEY = "your_reducto_key"
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_key"
```

3. Run the development server:
```bash
uv run uvicorn app.main:app --reload
```

## API Endpoints

- `/api/v1/controls/` - Audit control management
- `/api/v1/documents/` - Document upload and management
- `/api/v1/tabular/` - Tabular view data
- `/api/v1/ai/` - AI response processing

## Development

This project follows FastAPI best practices with:
- Module-based architecture
- Service layer pattern
- Async/await throughout
- Comprehensive error handling
- Type hints and validation 