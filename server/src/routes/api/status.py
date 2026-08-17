from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class StatusResponse(BaseModel):
    status: str
    version: str

@router.get("/status", response_model=StatusResponse)
async def get_status():
    return StatusResponse(status="online", version="1.0")
