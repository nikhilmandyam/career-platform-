import json
import logging

from sqlalchemy.exc import OperationalError


def test_projects_order_by_display_order_then_id(database_url, tmp_path):
    from app.projects import load_projects
    from app.seed import initialize_database

    seed_file = tmp_path / "projects.json"
    seed_file.write_text(
        json.dumps(
            [
                {
                    "id": "zebra",
                    "title": "Last alphabetically",
                    "description": "A later ID",
                    "url": None,
                    "display_order": 1,
                },
                {
                    "id": "alpha",
                    "title": "First alphabetically",
                    "description": "An earlier ID",
                    "url": None,
                    "display_order": 1,
                },
                {
                    "id": "featured",
                    "title": "Featured",
                    "description": "Shown first",
                    "url": None,
                    "display_order": 0,
                },
            ]
        ),
        encoding="utf-8",
    )
    initialize_database(database_url, seed_file)

    projects = load_projects()

    assert [project.id for project in projects] == ["featured", "alpha", "zebra"]


def test_seed_initialization_is_idempotent_by_stable_id(database_url, tmp_path):
    from app.database import get_session_factory
    from app.models import Project
    from app.seed import initialize_database

    seed_file = tmp_path / "projects.json"
    first_seed = [
        {
            "id": "portfolio",
            "title": "Portfolio v1",
            "description": "First version",
            "url": "https://example.com/old",
            "display_order": 2,
        }
    ]
    seed_file.write_text(json.dumps(first_seed), encoding="utf-8")
    initialize_database(database_url, seed_file)

    updated_seed = [
        {
            "id": "portfolio",
            "title": "Portfolio",
            "description": "Updated version",
            "url": None,
            "display_order": 1,
        }
    ]
    seed_file.write_text(json.dumps(updated_seed), encoding="utf-8")
    initialize_database(database_url, seed_file)

    with get_session_factory()() as session:
        projects = session.query(Project).all()

    assert len(projects) == 1
    assert projects[0].title == "Portfolio"
    assert projects[0].description == "Updated version"
    assert projects[0].url is None
    assert projects[0].display_order == 1


def test_load_projects_returns_none_and_logs_sqlalchemy_error(monkeypatch, caplog):
    import app.projects as projects

    def fail_to_create_session():
        raise OperationalError("SELECT 1", {}, OSError("database offline"))

    monkeypatch.setattr(projects, "get_session_factory", fail_to_create_session)

    with caplog.at_level(logging.ERROR):
        result = projects.load_projects()

    assert result is None
    assert "Failed to load projects" in caplog.text


def test_load_projects_returns_none_when_database_url_is_missing(monkeypatch, caplog):
    import app.projects as projects
    from app.database import get_session_factory

    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_session_factory.cache_clear()

    with caplog.at_level(logging.ERROR):
        result = projects.load_projects()

    assert result is None
    assert "Failed to load projects" in caplog.text
