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


def test_stylesheet_link_is_root_relative_and_cache_busted():
    from app.main import app

    response = TestClient(app).get("/")

    assert (
        '<link rel="stylesheet" href="/static/style.css?v=3">'
        in response.text
    )


def test_small_secondary_text_meets_wcag_aa_contrast():
    import re
    from pathlib import Path

    stylesheet = (Path(__file__).resolve().parents[1] / "app/static/style.css").read_text()

    def foreground(selector):
        match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", stylesheet)
        assert match is not None
        color = re.search(r"color:\s*(#[0-9a-fA-F]{6})", match.group(1))
        assert color is not None
        return color.group(1)

    def luminance(color):
        channels = [
            int(color[index : index + 2], 16) / 255
            for index in (1, 3, 5)
        ]
        linear = [
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            for value in channels
        ]
        return sum(weight * value for weight, value in zip((0.2126, 0.7152, 0.0722), linear))

    def contrast_ratio(foreground_color, background_color):
        high, low = sorted(
            (luminance(foreground_color), luminance(background_color)),
            reverse=True,
        )
        return (high + 0.05) / (low + 0.05)

    year_color = foreground(".tag--credential span")
    footer_color = foreground("footer")

    assert contrast_ratio(year_color, "#f7f9fb") >= 4.5
    assert contrast_ratio(footer_color, "#f2f5f7") >= 4.5


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
    for section in (
        "profile",
        "summary",
        "experience",
        "education",
        "skills",
        "certifications",
        "leadership",
        "contact",
    ):
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


def test_home_displays_approved_resume_details():
    from app.main import app

    response = TestClient(app).get("/")

    assert response.status_code == 200
    for detail in (
        "Nikhil Mandyam",
        "Information Systems and Business Analytics student at Loyola Marymount University",
        "GPA: 3.3/4.0",
        "Programming for Business Applications",
        "Financial Accounting",
        "Data Structures and Applications",
        "Analytics in Operations and Supply Chain Management",
        "Database Management Systems",
        "Served as the primary contact responding to up to 10 daily phone and email inquiries from prospective students and families while guiding 23+ students through the registration process for summer programs.",
        "Supported an LMU summer program serving 1,000+ global applicants and operating with a $1.5M+ program budget.",
        "Managed CRM data and coordinated scheduling and communication across a 12-person staff of directors, faculty, TAs, and RAs, helping reduce interdepartmental response times by an average of 2 business days.",
        "Processed weekly payroll for 150+ student employees, ensuring accurate payments with zero compliance discrepancies.",
        "Verified timesheets and resolved errors with department supervisors, improving on-time approvals by 1 business day.",
        "Maintained secure digital and physical payroll records under strict confidentiality protocols.",
        "Managed front-desk operations and assisted 10+ visitors daily.",
        "Created and edited short-form content for Instagram, TikTok, and Google Blogs covering clinic services and wellness offerings.",
        "Managed weekly content calendars and drafted captions, newsletter copy, and campaign materials.",
        "Researched local partnership opportunities with apartments, coworking spaces, and fitness studios.",
        "Tracked website, Google, email, and social media metrics to identify engagement trends and support digital marketing improvements.",
        "Bloomberg Spreadsheet Analysis",
        "Bloomberg Environmental Social Governance",
        "Bloomberg Market Concepts",
        "Google Analytics 4 Certified",
        "Information Systems and Business Analytics Society",
    ):
        assert detail in response.text
    for section in ("certifications", "leadership"):
        assert f'id="{section}"' in response.text


def test_contact_links_use_approved_email_and_keep_missing_profiles_as_text():
    from app.main import app

    response = TestClient(app).get("/")
    contact_section = response.text.split('<section id="contact"', 1)[1].split(
        "</section>", 1
    )[0]

    assert (
        '<a href="mailto:nikhilmandyam@gmail.com">'
        "Email: nikhilmandyam@gmail.com</a>"
    ) in contact_section
    assert "LinkedIn" in contact_section
    assert "[Add LinkedIn URL]" in contact_section
    assert "[Add GitHub URL]" in contact_section
    assert 'href="[Add LinkedIn URL]"' not in contact_section
    assert 'href="[Add GitHub URL]"' not in contact_section
    assert contact_section.count("<a ") == 1
    assert "Phone:" not in contact_section
    assert "Address:" not in contact_section


def test_seeded_project_placeholder_is_displayed_without_link(database_url):
    from pathlib import Path

    from app.main import app
    from app.seed import initialize_database

    seed_file = Path(__file__).resolve().parents[1] / "data" / "projects.json"
    initialize_database(database_url, seed_file)

    response = TestClient(app).get("/")
    projects_section = response.text.split('<section id="projects"', 1)[1].split(
        "</section>", 1
    )[0]

    assert "Project descriptions coming soon" in projects_section
    assert "Project details will be added here once finalized." in projects_section
    assert "<a " not in projects_section
