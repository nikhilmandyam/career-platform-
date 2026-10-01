import pytest
from fastapi.testclient import TestClient


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
