# Tally Project Structure

This document outlines the structure of the Tally tabular review application, which consists of a backend API service and a frontend React application.

## Overview

```
tally-onsite/
├── tally-backend/          # FastAPI backend service
├── tally-frontend/         # React Router frontend application
├── Backend-design-proposal.md
├── UI-design-proposal.md
├── highlevel-application-requirements.md
└── [other documentation files]
```

## Backend Structure (`tally-backend/`)

The backend is built with FastAPI and follows a modular architecture:

```
tally-backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration settings
│   ├── models.py                  # Database models
│   ├── schemas.py                 # Pydantic schemas for API
│   ├── routes.py                  # Main API routes
│   ├── db/
│   │   ├── base.py               # Database base models
│   │   └── engine.py             # Database engine configuration
│   ├── modules/
│   │   └── controls/
│   │       ├── routes.py         # Control-specific routes
│   │       └── service.py        # Control business logic
│   └── services/
│       ├── ai_service.py         # OpenAI integration service
│       ├── document_service.py   # Document processing service
│       └── storage_service.py    # File storage service
```

### Key Backend Components:
- **AI Service**: Integrates with OpenAI for document analysis
- **Document Service**: Handles document processing via Reducto
- **Storage Service**: Manages file uploads and storage
- **Controls Module**: Manages audit controls/questions

## Frontend Structure (`tally-frontend/`)

The frontend is built with React Router v7 and uses TanStack Table for the tabular interface:

```
tally-frontend/
├── app/
│   ├── root.tsx                   # Root layout component
│   ├── app.css                    # Global styles with Tailwind
│   ├── routes.ts                  # Route configuration
│   ├── routes/
│   │   ├── tabular-review.tsx     # Main tabular review route (index)
│   │   └── home.tsx               # Welcome/home route
│   └── welcome/
│       └── welcome.tsx            # Welcome page component
├── components/
│   ├── tabular-review.tsx         # Main tabular review component
│   └── ui/                        # Reusable UI components
│       ├── button.tsx
│       ├── checkbox.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── select.tsx
│       └── table.tsx
├── lib/
│   └── utils.ts                   # Utility functions (cn helper)
├── public/
│   └── favicon.ico
├── package.json
├── tsconfig.json
├── vite.config.ts
└── react-router.config.ts
```

### Key Frontend Components:

#### Main Application
- **`app/routes/tabular-review.tsx`**: Primary route displaying the tabular interface
- **`components/tabular-review.tsx`**: Core component implementing the table with TanStack Table

#### UI Components (`components/ui/`)
- Built with Radix UI primitives and Tailwind CSS
- Follows shadcn/ui design patterns
- Reusable across the application

#### Features Implemented:
- **Document Management**: Upload, display, and delete documents
- **Control Management**: Create, edit, and delete audit controls/questions
- **Dynamic Table**: Rows = documents, columns = controls
- **AI Integration**: Mock API calls simulating Reducto + OpenAI processing
- **Real-time States**: Loading, completed, error states for each cell
- **Citations**: Display AI response citations
- **Regeneration**: Ability to regenerate AI responses

## Path Configuration

### TypeScript Path Mapping
```json
"paths": {
  "~/*": ["./app/*"],        // Maps to app directory
  "@/*": ["./*"]             // Maps to project root
}
```

### Import Patterns:
- **App components**: Use `~` alias (e.g., `~/routes/home`)
- **Components outside app**: Use relative paths (e.g., `../../components/tabular-review`)
- **UI components**: Use relative paths from components directory

## Development

### Frontend Development Server
```bash
cd tally-frontend
npm run dev
# Runs on http://localhost:5173/
```

### Backend Development Server
```bash
cd tally-backend
uvicorn app.main:app --reload
# Runs on http://localhost:8000/
```

## Architecture Notes

1. **Frontend-Backend Separation**: Complete separation with API communication
2. **Component Structure**: Follows React best practices with small, focused components
3. **State Management**: Uses React hooks and Context for state management
4. **Styling**: Tailwind CSS with custom design system
5. **Type Safety**: Full TypeScript implementation
6. **API Integration**: Designed for REST API communication with the FastAPI backend

## Current Implementation Status

- ✅ Frontend tabular review interface complete
- ✅ Mock AI processing simulation
- ✅ Document and control management
- ✅ Real-time loading states
- 🚧 Backend API implementation (in progress)
- 🚧 Real Reducto + OpenAI integration (planned)
- 🚧 Authentication system (planned) 