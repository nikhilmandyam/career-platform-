import json

import pytest
from fastapi.testclient import TestClient


def _initialize_projects(database_url, tmp_path, projects):
    from app.seed import initialize_database

    seed_file = tmp_path / "projects.json"
    seed_file.write_text(json.dumps(projects), encoding="utf-8")
    initialize_database(database_url, seed_file)


def test_home_includes_bundled_resume_sections(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    try:
        from app.main import app
    except ModuleNotFoundError as error:
        pytest.fail(f"resume application is not available yet: {error}")

    response = TestClient(app).get("/")

    assert response.status_code == 200
    for section, heading in (
        ("profile", "Profile"),
        ("summary", "Summary"),
        ("experience", "Experience"),
        ("education", "Education"),
        ("skills", "Skills"),
        ("projects", "Projects"),
        ("contact", "Contact"),
    ):
        assert f'id="{section}"' in response.text
        assert heading in response.text


def test_static_stylesheet_is_served():
    from app.main import app

    response = TestClient(app).get("/static/style.css")

    assert response.status_code == 200
    assert "font-family" in response.text


def test_home_renders_database_projects(database_url, tmp_path):
    from app.main import app

    _initialize_projects(
        database_url,
        tmp_path,
        [
            {
                "id": "later",
                "title": "Later project",
                "description": "Second in display order",
                "url": "https://example.com/later",
                "display_order": 2,
            },
            {
                "id": "first",
                "title": "First project",
                "description": "First in display order",
                "url": "https://example.com/first",
                "display_order": 1,
            },
        ],
    )

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert response.text.index("First project") < response.text.index("Later project")
    assert 'href="https://example.com/first"' in response.text


def test_home_keeps_resume_visible_when_database_unavailable(monkeypatch):
    import app.main as main

    monkeypatch.setattr(main, "load_projects", lambda: None, raising=False)

    response = TestClient(main.app).get("/")

    assert response.status_code == 200
    for section in ("profile", "summary", "experience", "education", "skills", "contact"):
        assert f'id="{section}"' in response.text
    assert "Projects temporarily unavailable" in response.text


def test_home_shows_empty_projects_state(database_url):
    from app.main import app

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "No projects listed yet" in response.text
    assert "Projects temporarily unavailable" not in response.text


def test_project_without_url_has_no_link(database_url, tmp_path):
    from app.main import app

    _initialize_projects(
        database_url,
        tmp_path,
        [
            {
                "id": "offline-demo",
                "title": "Offline demo",
                "description": "No public link",
                "url": None,
                "display_order": 1,
            }
        ],
    )

    response = TestClient(app).get("/")
    projects_section = response.text.split('<section id="projects"', 1)[1].split(
        "</section>", 1
    )[0]

    assert "Offline demo" in projects_section
    assert "<a " not in projects_section
