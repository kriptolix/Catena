from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class StatusResponse(BaseModel):
    status: str
    versao: str

@router.get("/status", response_model=StatusResponse)
async def get_status():
    return StatusResponse(status="online", versao="1.0")
