# api/main.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi import FastAPI
from api.endpoints import analysis, data, tasks

app = FastAPI(title="Transaction Analyzer API")

app.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
app.include_router(data.router, prefix="/data", tags=["Data"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])


@app.get("/")
async def root():
    return {"message": "Transaction Analyzer API"}

