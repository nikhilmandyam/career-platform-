import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import build_engine
from app.models import Base, Project


def initialize_database(database_url: str, seed_file: Path) -> None:
    projects = json.loads(seed_file.read_text(encoding="utf-8"))
    if not isinstance(projects, list):
        raise ValueError("Project seed data must be a JSON list")

    engine = build_engine(database_url)
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session, session.begin():
            for values in projects:
                project = session.get(Project, values["id"])
                if project is None:
                    session.add(Project(**values))
                else:
                    for field, value in values.items():
                        setattr(project, field, value)
    finally:
        engine.dispose()
