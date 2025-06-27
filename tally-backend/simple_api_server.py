import asyncio
import os
from contextlib import asynccontextmanager
from tempfile import SpooledTemporaryFile
from typing import Any

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel
from reducto import AsyncClient as ReductoClient
from supabase import AsyncClient, acreate_client
from supabase.lib.client_options import AsyncClientOptions

# Supabase configuration
SUPABASE_URL = "https://tofyxmdctxlagncvqhpg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRvZnl4bWRjdHhsYWduY3ZxaHBnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA5NTc1NzEsImV4cCI6MjA2NjUzMzU3MX0.zhDlAV3a35hL1pe6LZ4nytDYMrWsDdAzqGR1i4MZW_M"
# Database Configuration (using Supabase PostgreSQL)
DATABASE_URL = "postgresql://postgres:f2Kzb3IK4%5EB6FJ@db.tofyxmdctxlagncvqhpg.supabase.co:5432/postgres"

# Reducto configuration
REDUCTO_API_KEY = os.getenv("REDUCTO_API_KEY")
REDUCTO_BASE_URL = "https://platform.reducto.ai"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initialize Supabase client options
options = AsyncClientOptions(
    postgrest_client_timeout=10,
    storage_client_timeout=10
)

# Global variables for clients
supabase: AsyncClient = None
reducto_client: ReductoClient = None

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize clients on startup
    global supabase, reducto_client
    supabase = await acreate_client(SUPABASE_URL, SUPABASE_KEY, options=options)
    reducto_client = ReductoClient(api_key=REDUCTO_API_KEY)

    yield
    # Clean up on shutdown
    if supabase:
        await supabase.auth.sign_out()
        await supabase.postgrest.aclose()
    if reducto_client:
        await reducto_client.aclose()

# Initialize FastAPI app with lifespan
app = FastAPI(title="Async Supabase Test Server", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

class HealthResponse(BaseModel):
    status: str
    supabase_connection: bool
    details: dict[str, Any]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health of the server and Supabase connection."""
    try:
        # Test Supabase connection by fetching version
        version = await supabase.table('pg_version').select("*").execute()
        supabase_connected = True
        details = {
            "version": version.data if version.data else "Unknown",
            "error": None
        }
    except Exception as e:
        supabase_connected = False
        details = {
            "version": None,
            "error": str(e)
        }

    return HealthResponse(
        status="healthy" if supabase_connected else "unhealthy",
        supabase_connection=supabase_connected,
        details=details
    )

@app.get("/test_storage")
async def test_storage():
    """Test Supabase Storage functionality."""
    try:
        # List all storage buckets
        buckets = await supabase.storage.list_buckets()
        return {
            "status": "success",
            "buckets": [bucket.name for bucket in buckets],
            "error": None
        }
    except Exception as e:
        return {
            "status": "error",
            "buckets": None,
            "error": str(e)
        }

@app.post("/upload_document")
async def upload_document(
    file: UploadFile = File(...),
    bucket_name: str = "documents"  # Default bucket name
):
    """Upload a document to Supabase Storage bucket."""
    try:
        # Read file content
        content = await file.read()

        # Create a temporary file
        with SpooledTemporaryFile() as temp_file:
            temp_file.write(content)
            temp_file.seek(0)

            # Ensure the bucket exists
            try:
                await supabase.storage.get_bucket(bucket_name)
            except Exception as e:
                if "bucket not found" in str(e).lower():
                    # Create bucket if it doesn't exist
                    try:
                        await supabase.storage.create_bucket(
                            bucket_name,
                            options={
                                "public": True  # Make bucket public
                            }
                        )
                    except Exception as create_error:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to create bucket: {str(create_error)}"
                        )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error accessing bucket: {str(e)}"
                    )

            # Upload file to Supabase storage with public access
            file_path = f"{file.filename}"
            try:
                result = await supabase.storage.from_(bucket_name).upload(
                    file_path,
                    temp_file,
                    file_options={
                        "content-type": file.content_type,
                        "x-upsert": "true"  # Override if file exists
                    }
                )

                # Get the public URL
                file_url = supabase.storage.from_(bucket_name).get_public_url(file_path)

                return {
                    "status": "success",
                    "message": "File uploaded successfully",
                    "details": {
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "size": len(content),
                        "bucket": bucket_name,
                        "path": file_path,
                        "public_url": file_url
                    }
                }
            except Exception as upload_error:
                # Get more detailed error information
                error_msg = str(upload_error)
                if hasattr(upload_error, 'response'):
                    try:
                        error_msg = upload_error.response.json()
                    except:
                        error_msg = upload_error.response.text if hasattr(upload_error.response, 'text') else str(upload_error)

                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file: {error_msg}"
                )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@app.get("/test_database")
async def test_database():
    """Test Supabase Database functionality."""
    try:
        # Test database connection with a simple query
        result = await supabase.table("test_table").select("*").limit(1).execute()
        return {
            "status": "success",
            "message": "Database connection successful",
            "data": result.data,
            "error": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": None,
            "data": None,
            "error": str(e)
        }

@app.post("/reducto/upload_parse")
async def upload_parse(file: UploadFile = File(...)):
    """Test Reducto document processing directly without Supabase storage."""
    try:
        # Read file content
        content = await file.read()

        # Send to Reducto parse endpoint
        upload = await reducto_client.upload(
            file=content,
        )
        parse_result = await reducto_client.parse.run(document_url=upload)

        # Debug: Log the actual structure of parse_result
        print(f"Parse result type: {type(parse_result)}")
        print(f"Parse result preview: {str(parse_result)[:500]}...")

        # If it's a complex object, try to extract text content
        if hasattr(parse_result, 'content'):
            text_content = parse_result.content
        elif hasattr(parse_result, 'text'):
            text_content = parse_result.text
        elif isinstance(parse_result, dict):
            # Try common text field names
            text_content = (
                parse_result.get('content') or
                parse_result.get('text') or
                parse_result.get('body') or
                str(parse_result)
            )
        else:
            text_content = str(parse_result)

        print(f"Extracted text content: {text_content[:200]}...")

        # Return combined results
        return {
            "parse_result": parse_result,
            "text_content": text_content,  # Add extracted text for frontend
            "status": "success"
        }

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reducto API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )

class ControlInput(BaseModel):
    """Input model for control data."""
    title: str
    description: str

class OpenAIRequest(BaseModel):
    """Input model for OpenAI completion request."""
    input_text: str

@app.post("/openai/completion")
async def openai_completion(request: OpenAIRequest):
    """Test OpenAI completion API."""
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",  # or "gpt-4" for standard GPT-4
            messages=[
                {"role": "system", "content": "You are an AI assistant specialized in analyzing documents for compliance and control requirements. Make sure you are concise and explain in a paragraph with 2-3 sentences why. Avoid using bullet points, lists, numbered lists, or other markdown formatting."},
                {"role": "user", "content": request.input_text}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        return {
            "response": response.choices[0].message.content,
            "usage": response.usage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get OpenAI completion: {str(e)}")

@app.post("/reducto/openai")
async def reducto_openai(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(...)
):
    """Process a document with Reducto and OpenAI."""
    try:
        # Read file content
        content = await file.read()

        # Send to Reducto parse endpoint
        upload = await reducto_client.upload(
            file=content,
        )
        parse_result = await reducto_client.parse.run(document_url=upload)

        # Extract text content from parse result
        if hasattr(parse_result, 'content'):
            text_content = parse_result.content
        elif hasattr(parse_result, 'text'):
            text_content = parse_result.text
        elif isinstance(parse_result, dict):
            # Try common text field names
            text_content = (
                parse_result.get('content') or
                parse_result.get('text') or
                parse_result.get('body') or
                str(parse_result)
            )
        else:
            text_content = str(parse_result)

        # Create control prompt from title and description
        control_prompt = f"Title: {title}\nDescription: {description}"

        # Send to OpenAI with extracted text content
        openai_response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant specialized in analyzing documents for compliance and control requirements."
                },
                {
                    "role": "user",
                    "content": f"Please analyze the following document content against this control requirement:\n\n{control_prompt}\n\nDocument content:\n{text_content}"
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )

        return {
            "reducto_processing": {
                "parse_result": parse_result,
            },
            "openai_analysis": {
                "response": openai_response.choices[0].message.content,
                "usage": openai_response.usage
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

class BatchControlsInput(BaseModel):
    """Input model for batch control processing."""
    controls: list[ControlInput]

class DocumentControlsRequest(BaseModel):
    """Request model for document-controls evaluation."""
    document_content: str
    controls: list[ControlInput]

async def evaluate_control(control: ControlInput, document_content: str) -> dict:
    """Helper function to evaluate a single control against a document."""
    try:
        prompt = f"""
        Document Content: {document_content}
        
        Control:
        Title: {control.title}
        Description: {control.description}
        
        Evaluate if the document complies with this control. Provide a detailed explanation.
        """

        completion = await openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert at evaluating document compliance with controls."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        return {
            "control": control.dict(),
            "evaluation": completion.choices[0].message.content,
            "status": "success"
        }
    except Exception as e:
        return {
            "control": control.dict(),
            "evaluation": None,
            "status": "error",
            "error": str(e)
        }

@app.post("/reducto/batch_process")
async def batch_process(
    file: UploadFile = File(...),
    controls_json: str = Form(...)
):
    """
    Process multiple controls against a document in parallel.
    
    1. Uploads and parses document through Reducto
    2. Evaluates all controls against the document content in parallel
    """
    try:
        # Parse controls input
        controls_data = BatchControlsInput.parse_raw(controls_json)

        # Read and process document
        content = await file.read()
        upload = await reducto_client.upload(file=content)
        parse_result = await reducto_client.parse.run(document_url=upload)

        # Extract text content from parse result
        if hasattr(parse_result, 'content'):
            text_content = parse_result.content
        elif hasattr(parse_result, 'text'):
            text_content = parse_result.text
        elif isinstance(parse_result, dict):
            # Try common text field names
            text_content = (
                parse_result.get('content') or
                parse_result.get('text') or
                parse_result.get('body') or
                str(parse_result)
            )
        else:
            text_content = str(parse_result)

        if not text_content:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract content from document"
            )

        # Process all controls in parallel
        evaluation_tasks = [
            evaluate_control(control, text_content)  # Use extracted text_content here
            for control in controls_data.controls
        ]
        evaluations = await asyncio.gather(*evaluation_tasks)

        return {
            "status": "success",
            "document": {
                "filename": file.filename,
                "parse_result": parse_result
            },
            "evaluations": evaluations
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid controls JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process batch request: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Changed port to 8001
