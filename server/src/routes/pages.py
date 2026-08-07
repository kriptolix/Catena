# routes/pages.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from templates.templates import templates

router = APIRouter(tags=["pages"])

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        { }
    )

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {}
    )

@router.get("/equipamentos/{tombo}", response_class=HTMLResponse)
async def equipamento_detail(request: Request, tombo: str):
    return templates.TemplateResponse(
        request,
        "equipamento.html", 
        {"tombo": tombo}
    )


@router.get("/adicionar", response_class=HTMLResponse)
async def adicionar_equipamento(request: Request):
    return templates.TemplateResponse(
        request,
        "adicionar_equipamento.html", 
        {}
    )