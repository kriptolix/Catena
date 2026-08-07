from pathlib import Path
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

print(f"TEMPLATES_DIR: {TEMPLATES_DIR}")

templates = Jinja2Templates(directory=TEMPLATES_DIR)