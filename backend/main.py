from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = FastAPI()

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

class UIAutomatorRequest(BaseModel):
    instruction: str

class ProfileDataRequest(BaseModel):
    fileName: str
    sampleData: str

class QualityCheckerRequest(BaseModel):
    data: str
    rules: str

from typing import List, Optional
from enum import Enum

class ActionStatus(str, Enum):
    done = "done"
    failed = "failed"

class UIStep(BaseModel):
    action: str
    status: ActionStatus

class UIAutomatorResponse(BaseModel):
    steps: List[UIStep]
    summary: str

class DataStats(BaseModel):
    rows: float
    columns: float
    missingValues: float
    duplicateRows: float

class ProfileDataResponse(BaseModel):
    stats: DataStats
    insights: List[str]
    anomalies: List[str]

class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Violation(BaseModel):
    rule: str
    issue: str
    severity: Severity

class QualityCheckerResponse(BaseModel):
    violations: List[Violation]
    score: float

@app.post("/run-ui-automator")
async def run_ui_automator(request: UIAutomatorRequest):
    try:
        prompt = f'Simulate a browser-use agent task. Given this instruction: "{request.instruction}", return a JSON object describing the step-by-step execution plan and a final summary.'
        
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=UIAutomatorResponse
            )
        )
        return response.parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/profile-data")
async def profile_data(request: ProfileDataRequest):
    try:
        prompt = f'Analyze this data sample from file "{request.fileName}":\n\n{request.sampleData}\n\nProvide a data profile report in JSON format including basic stats, AI-driven insights, and potential anomalies.'
        
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=ProfileDataResponse
            )
        )
        return response.parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/check-data-quality")
async def check_data_quality(request: QualityCheckerRequest):
    try:
        prompt = f'Apply these quality rules: "{request.rules}" to this dataset snippet: "{request.data}". List all violations and suggestions.'
        
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=QualityCheckerResponse
            )
        )
        return response.parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
