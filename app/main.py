from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from pathlib import Path
import uuid

from .celery_app import celery_app # Import the Celery app instance
from .tasks import process_gemstone_image # Import your Celery task
from .schemas import TaskResponse, GradingResultResponse, GemstoneGrade
from celery.result import AsyncResult

# --- Configuration ---
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True) # Create upload directory if it doesn't exist

app = FastAPI(title="Gemstone Grader API")

# --- CORS Middleware ---
# Allow requests from your React frontend (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Vite default dev port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.post("/upload_gemstone/", response_model=TaskResponse)
async def upload_gemstone_image_for_grading(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")

    try:
        # Sanitize filename and create a unique name
        original_filename = Path(file.filename).name # Basic sanitization
        file_extension = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Dispatch the image processing task to Celery
        # Pass the path to the saved image
        task = process_gemstone_image.delay(str(file_path.resolve()))
        
        # In a real app, you might save image metadata and task ID to a database here
        # e.g., create a GemstoneImage record with task.id

        return TaskResponse(task_id=task.id, status="PENDING")

    except Exception as e:
        # Log the exception e
        print(f"Error during upload or task dispatch: {e}")
        raise HTTPException(status_code=500, detail=f"Could not process file: {str(e)}")
    finally:
        if hasattr(file, 'file') and file.file: # Ensure file object exists
            file.file.close()


@app.get("/grading_result/{task_id}", response_model=GradingResultResponse)
async def get_grading_task_result(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    
    response_data = {"task_id": task_id, "status": task_result.status}

    if task_result.successful():
        # Task completed successfully
        raw_result = task_result.result # This is the dict returned by the Celery task
        if isinstance(raw_result, dict):
            response_data["result"] = GemstoneGrade(**raw_result)
        else:
            # Should not happen if task returns a dict that matches GemstoneGrade
            response_data["result"] = GemstoneGrade(error="Unexpected result format from task.")
            response_data["status"] = "FAILURE" # Or a custom status
    elif task_result.failed():
        # Task failed
        # task_result.info often holds the exception object or a string representation
        error_info = str(task_result.info) if task_result.info else "Unknown error"
        response_data["result"] = GemstoneGrade(error=f"Task failed: {error_info}")
        response_data["status"] = "FAILURE"
    elif task_result.status in ['PENDING', 'STARTED', 'RETRY']:
        response_data["result"] = GemstoneGrade(processing_notes=f"Grading is {task_result.status.lower()}...")
    elif task_result.status == 'PROGRESS':
        # If your task updates state with 'meta'
        progress_info = task_result.info if isinstance(task_result.info, dict) else {}
        message = progress_info.get('message', 'Grading in progress...')
        response_data["result"] = GemstoneGrade(processing_notes=message)
    else:
        # Other states like REVOKED
        response_data["result"] = GemstoneGrade(processing_notes=f"Task status: {task_result.status}")
    
    return GradingResultResponse(**response_data)


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Gemstone Grader API!"}

# To run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# (from the 'backend' directory)