# api/endpoints/analysis.py
from fastapi import APIRouter
from tasks.analyzer_tasks import analyze_blocks, analyze_block_range
from pydantic import BaseModel

router = APIRouter()

class BlockAnalysisRequest(BaseModel):
    depth_blocks: int

class BlockRangeAnalysisRequest(BaseModel):
    start_block: int
    end_block: int

@router.post("/blocks")
async def start_block_analysis(request: BlockAnalysisRequest):
    if request.depth_blocks <= 0:
        return {"error": "depth_blocks must be positive"}
    task = analyze_blocks.delay(depth_blocks=request.depth_blocks)
    return {"task_id": task.id, "status": "Task started"}

@router.post("/block-range")
async def start_block_range_analysis(request: BlockRangeAnalysisRequest):
    if request.start_block > request.end_block:
        return {"error": "start_block must be less than or equal to end_block"}
    task = analyze_block_range.delay(start_block=request.start_block, end_block=request.end_block)
    return {"task_id": task.id, "status": "Task started"}