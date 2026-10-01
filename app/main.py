from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.content import RESUME_CONTENT
from app.projects import load_projects

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app = FastAPI()
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
