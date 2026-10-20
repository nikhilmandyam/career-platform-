import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.content import RESUME_CONTENT
from app.database import create_schema
from app.projects import load_projects

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def initialize_database_schema() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        create_schema(database_url)


app = FastAPI(on_startup=[initialize_database_schema])

app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="resume.html",
        context={
            "resume": RESUME_CONTENT,
            "projects": load_projects(),
        },
    )


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="privacy.html",
        context={},
    )
