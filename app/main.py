import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError

from app.content import RESUME_CONTENT
from app.database import create_schema
from app.projects import load_projects

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def initialize_database_schema() -> bool:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        app.state.database_schema_initialized = False
        return False

    try:
        create_schema(database_url)
    except SQLAlchemyError:
        app.state.database_schema_initialized = False
        logger.exception(
            "Failed to initialize database schema; will retry on request"
        )
        return False

    app.state.database_schema_initialized = True
    return True


app = FastAPI(on_startup=[initialize_database_schema])
app.state.database_schema_initialized = False

app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    database_url = os.environ.get("DATABASE_URL")
    schema_ready = app.state.database_schema_initialized
    if not schema_ready and database_url:
        schema_ready = initialize_database_schema()

    projects = load_projects() if schema_ready or not database_url else None
    return templates.TemplateResponse(
        request=request,
        name="resume.html",
        context={
            "resume": RESUME_CONTENT,
            "projects": projects,
        },
        status_code=503 if projects is None else 200,
    )


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="privacy.html",
        context={},
    )
