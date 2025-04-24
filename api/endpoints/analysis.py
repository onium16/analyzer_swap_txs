# api/endpoints/analysis.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from tasks.analyzer_tasks import analyze_blocks, analyze_block_range

router = APIRouter()


class BlockAnalysisRequest(BaseModel):
    """
    Request schema for analyzing a number of blocks backward from the current one.
    """
    depth_blocks: int


class BlockRangeAnalysisRequest(BaseModel):
    """
    Request schema for analyzing a specific range of blocks.
    """
    start_block: int
    end_block: int


@router.post("/blocks")
async def start_block_analysis(request: BlockAnalysisRequest) -> Dict[str, Any]:
    """
    Start a Celery task to analyze the latest N blocks.

    Input:
        - depth_blocks (int): How many blocks back to analyze.

    Output:
        - JSON with task_id and status message, e.g.:
          {
              "task_id": "<uuid>",
              "status": "Task started"
          }
        - If input is invalid:
          {
              "error": "depth_blocks must be positive"
          }
    """
    if request.depth_blocks <= 0:
        return {"error": "depth_blocks must be positive"}

    task = analyze_blocks.delay(depth_blocks=request.depth_blocks)
    return {"task_id": task.id, "status": "Task started"}


@router.post("/block-range")
async def start_block_range_analysis(request: BlockRangeAnalysisRequest) -> Dict[str, Any]:
    """
    Start a Celery task to analyze blocks in a specified range.

    Input:
        - start_block (int): The starting block number.
        - end_block (int): The ending block number.

    Output:
        - JSON with task_id and status message, e.g.:
          {
              "task_id": "<uuid>",
              "status": "Task started"
          }
        - If start_block > end_block:
          {
              "error": "start_block must be less than or equal to end_block"
          }
    """
    if request.start_block > request.end_block:
        return {"error": "start_block must be less than or equal to end_block"}

    task = analyze_block_range.delay(
        start_block=request.start_block,
        end_block=request.end_block
    )
    return {"task_id": task.id, "status": "Task started"}
