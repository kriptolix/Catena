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

@router.get("/equipments/{tag}", response_class=HTMLResponse)
async def Equipment_detail(request: Request, asset_tag: str):
    return templates.TemplateResponse(
        request,
        "Equipment.html", 
        {"tag": asset_tag}
    )


@router.get("/adicionar", response_class=HTMLResponse)
async def adicionar_Equipment(request: Request):
    return templates.TemplateResponse(
        request,
        "adicionar_Equipment.html", 
        {}
    )