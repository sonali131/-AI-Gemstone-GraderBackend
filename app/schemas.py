from pydantic import BaseModel, Field
from typing import Optional, Dict

class TaskResponse(BaseModel):
    task_id: str
    status: str

class GemstoneGrade(BaseModel):
    gemstone_type: Optional[str] = Field("Unknown", description="Predicted gemstone type")
    type_confidence: Optional[float] = Field(0.0, description="Confidence score for the type prediction")
    color_grade: Optional[str] = Field("N/A", description="Estimated color grade")
    clarity_grade: Optional[str] = Field("N/A", description="Estimated clarity grade")
    cut_estimation: Optional[str] = Field("N/A", description="Estimation of cut quality")
    carat_estimation: Optional[str] = Field("N/A", description="Estimated carat weight or dimensions")
    processing_notes: Optional[str] = Field(None, description="Notes from the AI processing")
    error: Optional[str] = Field(None, description="Error message if processing failed")

class GradingResultResponse(BaseModel):
    task_id: str
    status: str # e.g., PENDING, STARTED, SUCCESS, FAILURE, PROGRESS
    result: Optional[GemstoneGrade] = None