from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from templates.templates import templates

router = APIRouter(tags=["equipment"])

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

@router.get("/Equipments/{tag}", response_class=HTMLResponse)
async def Equipment_detail(request: Request, asset_tag: str):
    return templates.TemplateResponse(request, "Equipment.html", {"tag": asset_tag})
