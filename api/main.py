# api/main.py

import sys
import os

# Add the root directory to sys.path to allow absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from typing import Dict

# Import routers from submodules
from api.endpoints import analysis, data, tasks

# Initialize FastAPI app with metadata
app = FastAPI(title="Transaction Analyzer API")

# Register route groups with prefixes and tags
app.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
app.include_router(data.router, prefix="/data", tags=["Data"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])


@app.get("/", response_class=JSONResponse)
async def root() -> Dict[str, str]:
    """
    Root endpoint to confirm the API is running.

    Returns:
        JSON containing a greeting message.
    """
    return {"message": "Transaction Analyzer API"}