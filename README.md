# Tally - AI-Powered Document Analysis and Compliance Review

A comprehensive document analysis and audit tool with AI capabilities, consisting of a FastAPI backend and a modern React frontend.

## Project Overview

Tally is split into two main components:

- `tally-backend`: FastAPI backend with AI integration and document processing
- `tally-frontend`: Modern React frontend with TypeScript and TailwindCSS

## Features

### Backend Features
- **Document Upload & Storage**: Supabase integration for secure file storage
- **AI-Powered Analysis**: OpenAI GPT integration for document Q&A
- **Document Parsing**: Reducto API integration for computer vision and OCR
- **Tabular Interface**: RESTful APIs for tabular data management
- **Async Processing**: Background task processing for AI operations

### Frontend Features
- **Document Upload**: Upload and process multiple documents simultaneously
- **Tabular Review**: Review document content in a structured tabular format
- **AI Analysis**: Integration with backend AI services for document analysis
- **Control Requirements**: Define and manage compliance control requirements
- **Real-time Updates**: Live updates during document processing

## Technologies

### Backend
- FastAPI: Modern async web framework
- SQLAlchemy: Async ORM with PostgreSQL
- OpenAI: GPT models for document analysis
- Reducto: Document parsing and computer vision
- Supabase: Database and file storage
- uv: Fast Python package management

### Frontend
- React with TypeScript
- Vite for development
- TailwindCSS for styling
- React Router for navigation
- Modern component architecture

## Project Structure

```
tally/
├── tally-backend/           # FastAPI Backend
│   ├── app/
│   │   ├── config.py       # Configuration settings
│   │   ├── db/            # Database models and migrations
│   │   ├── modules/       # Feature modules (AI, controls, documents)
│   │   ├── services/      # Business logic services
│   │   └── main.py        # Application entry point
│   ├── tests/             # Backend test suite
│   └── README.md          # Backend documentation
│
├── tally-frontend/         # React Frontend
│   ├── app/               # Application core
│   │   ├── hooks/        # Custom React hooks
│   │   ├── routes/       # Application routes
│   │   └── welcome/      # Welcome components
│   ├── components/        # Shared UI components
│   │   └── ui/           # Base UI components
│   └── README.md         # Frontend documentation
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js (v16 or higher)
- PostgreSQL database
- Supabase account
- OpenAI API key
- Reducto API key

### Backend Setup

1. Install dependencies:
```bash
cd tally-backend
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
uvicorn app.main:app --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd tally-frontend
npm install
```

2. Create `.env` file:
```env
VITE_API_BASE_URL=http://localhost:8000
```

3. Start development server:
```bash
npm run dev
```

## API Documentation

Backend API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Guidelines

### Backend
- Follow FastAPI best practices
- Use async/await throughout
- Implement comprehensive error handling
- Maintain type hints and validation

### Frontend
- Use TypeScript for all new components
- Follow the existing component structure
- Utilize shared UI components
- Maintain consistent error handling

## Building for Production

### Backend
```bash
uv run uvicorn app.main:app
```

### Frontend
```bash
npm run build
```

## License

[MIT License](LICENSE) 