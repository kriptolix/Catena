from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import init_db
from routes import pages
from routes.api import equipment, status, user, inventory


# Inicializar banco de dados ao iniciar a aplicação
print("Starting application...")
conn = init_db()
conn.close()  # Fechar conexão inicial

# Obter o diretório onde o main.py está localizado
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Catena Server", version="1.0")

# Servir arquivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# CORS (para acesso do frontend, se houver)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(status.router)
app.include_router(inventory.router)
app.include_router(equipment.router)
app.include_router(user.router)
app.include_router(pages.router)
# app.include_router(frontend.router)

@app.get("/")
async def root():
    return {"message": "Catena Server API", "docs": "/docs"}
