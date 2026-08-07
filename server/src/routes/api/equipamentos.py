from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from templates.templates import templates

router = APIRouter(tags=["frontend"])

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

@router.get("/equipamentos/{tombo}", response_class=HTMLResponse)
async def equipamento_detail(request: Request, tombo: str):
    return templates.TemplateResponse(request, "equipamento.html", {"tombo": tombo})
