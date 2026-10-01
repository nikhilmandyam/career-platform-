# Database-Driven Resume Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a simple, responsive resume site with the user-approved profile content, resilient bundled resume sections, and a MySQL-backed Projects section.

**Architecture:** A single FastAPI application renders a Jinja2 resume page. Static resume content is separate from the SQLAlchemy project query; an unavailable database affects only the Projects section. Project records are initialized from stable-ID seed data.

**Tech Stack:** Python, FastAPI, Jinja2, SQLAlchemy, PyMySQL, MySQL, pytest.

**Spec:** `docs/superpowers/specs/2026-10-01-database-driven-resume-design.md`

## Global Constraints

- “Use one Python FastAPI application to render HTML pages with Jinja2 templates.”
- “Keep resume content other than projects bundled with the application so it can be rendered without a database connection.”
- “Use SQLAlchemy for the MySQL data access boundary; configure its connection using a `DATABASE_URL` environment variable.”
- “If the project query fails, log the failure, render the rest of the page normally, and show a brief unavailable message in the Projects section.”
- “Maintain project content in a small seed-data file as the source of truth and provide a repeatable initializer command to create the initial schema and upsert records by stable ID.”
- “Re-running initialization must not create duplicates.”
- “Do not expose MySQL directly to the public internet.”
- “For the later Azure Ubuntu VM move, document installing the same Python application and a local MySQL service on the VM, configuring the same `DATABASE_URL` interface, and running the application as a systemd service behind Nginx.”
- “Do not include a phone number or home address.”
- Include Certifications and Leadership as bundled resume sections.
- Use clearly labeled plain-text LinkedIn and GitHub placeholders until URLs are supplied.
- Seed the single approved “Project descriptions coming soon” record if finalized project descriptions are unavailable.
- “There is no public API, separate JavaScript frontend, project editing UI, authentication, or career-platform functionality in this version.”

## File Structure

- `requirements.txt` — runtime and test dependencies.
- `pytest.ini` — make the repository root importable when running the `pytest` console script.
- `app/content.py` — editable, bundled resume-content structure; use obvious placeholders where personal copy has not been supplied.
- `app/main.py` — FastAPI application and `GET /` page route.
- `app/database.py` — `DatabaseConfigurationError`, `build_engine(database_url: str) -> Engine`, and lazy cached `get_session_factory() -> sessionmaker[Session]`.
- `app/models.py` — SQLAlchemy base and `Project` model.
- `app/projects.py` — ordered project query and narrow database-failure handling.
- `app/seed.py` — schema creation and stable-ID seed upsert.
- `app/templates/resume.html` — server-rendered page and database/empty states.
- `app/static/style.css` — responsive page styling.
- `data/projects.json` — project seed source; contains the approved clearly labeled placeholder until real project entries are supplied.
- `scripts/init_db.py` — command-line entry point for database initialization.
- `tests/conftest.py` — temporary SQLite database fixture shared by ORM and page tests.
- `tests/test_home.py` — page and project-state behavior.
- `tests/test_projects.py` — project ordering, failure, and seed idempotence.
- `README.md` — Codespaces setup, local MySQL use, run/test instructions, and Azure Ubuntu migration steps.

## Review Focus

- Missing or unreachable MySQL must leave all bundled resume sections, including Certifications and Leadership, visible and log the failure — pin database logging with `test_load_projects_returns_none_and_logs_sqlalchemy_error` in Task 2 and page preservation with `test_home_keeps_resume_visible_when_database_unavailable` in Task 3.
- A reachable but empty project table and the approved placeholder seed must be distinct from a database outage — pin with `test_home_shows_empty_projects_state` in Task 3 and `test_seeded_project_placeholder_is_displayed_without_link` in Task 5.
- Missing LinkedIn/GitHub URLs must remain plain-text labels, and contact must not include a phone or home address — pin with `test_contact_links_use_approved_email_and_keep_missing_profiles_as_text` in Task 5.
- Projects with equal display order need deterministic ordering — pin with `test_projects_order_by_display_order_then_id` in Task 2.
- Re-running initialization with changed seed data must update by stable ID rather than duplicate rows — pin with `test_seed_initialization_is_idempotent_by_stable_id` in Task 2.

---

### Task 1: Create the Static Resume Page

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `app/__init__.py`
- Create: `app/content.py`
- Create: `app/main.py`
- Create: `app/templates/resume.html`
- Create: `app/static/style.css`
- Create: `tests/test_home.py`

**Interfaces:**
- Produces: `app = FastAPI()` and `GET /`, which renders `resume.html` with bundled content from `RESUME_CONTENT`.
- Produces: `RESUME_CONTENT` with `profile.name`, `profile.headline`, `summary`, `experience` entries (`role`, `organization`, `dates`, `description`), `education` entries (`program`, `institution`, `dates`), `skills` as strings, and `contact` entries (`label`, `url`). Keep unspecified personal details as obvious replacement placeholders; do not invent credentials or work history.
- Uses section IDs `profile`, `summary`, `experience`, `education`, `skills`, `projects`, and `contact` for the page and in-page navigation.

- [ ] **Step 1: Add the dependency manifest**

Add the dependencies `fastapi`, `uvicorn`, `jinja2`, `sqlalchemy`, `pymysql`, `pytest`, and `httpx2` to `requirements.txt`; Starlette's current TestClient supports this client without the deprecation warning from `httpx`. Add `pytest.ini` with `[pytest]` and `pythonpath = .` so the documented `pytest` command imports the app from the repository root.

- [ ] **Step 2: Install the declared dependencies**

Run: `python -m pip install -r requirements.txt`

- [ ] **Step 3: Write the failing static-page test**

In `tests/test_home.py`, add `test_home_includes_bundled_resume_sections` and `test_static_stylesheet_is_served`. Assert `GET /` returns 200 and contains all seven section IDs and headings, without setting `DATABASE_URL`; assert `GET /static/style.css` returns 200 with stylesheet content.

- [ ] **Step 4: Run the test and verify it fails**

Run: `pytest -q tests/test_home.py::test_home_includes_bundled_resume_sections`

Expected: FAIL because the app and page do not exist yet.

- [ ] **Step 5: Implement the static page**

Create the app, bundled content mapping, semantic sectioned Jinja template, accessible in-page navigation, and responsive CSS. Mount `app/static` at `/static` as the named `static` route used by the template. The root route must not initialize or connect to MySQL.

- [ ] **Step 6: Run the static-page test**

Run: `pytest -q tests/test_home.py::test_home_includes_bundled_resume_sections`

Expected: PASS with all sections rendered while `DATABASE_URL` is unset.

- [ ] **Step 7: Commit the static page**

```bash
git add requirements.txt pytest.ini app tests/test_home.py docs/superpowers/plans/2026-10-01-database-driven-resume.md
git commit -m "feat: add static resume page"
```

### Task 2: Add the MySQL Project Model and Seed Initializer

**Files:**
- Create: `app/database.py`
- Create: `app/models.py`
- Create: `app/projects.py`
- Create: `app/seed.py`
- Create: `data/projects.json`
- Create: `scripts/init_db.py`
- Create: `tests/conftest.py`
- Create: `tests/test_projects.py`

**Interfaces:**
- Consumes: `Project` fields are `id: str`, `title: str`, `description: str`, `url: str | None`, and `display_order: int`.
- Produces: `load_projects() -> list[Project] | None`; an empty list means a successful query with no projects, and `None` means a configuration or SQLAlchemy database failure that was logged.
- Produces: `initialize_database(database_url: str, seed_file: Path) -> None`; creates the schema and upserts each seed record by `id`.
- Produces: `scripts/init_db.py` as the runnable initializer, reading `DATABASE_URL` and `data/projects.json`.

- [ ] **Step 1: Write the failing storage tests**

In `tests/test_projects.py`, add `test_projects_order_by_display_order_then_id`, `test_seed_initialization_is_idempotent_by_stable_id`, and `test_load_projects_returns_none_and_logs_sqlalchemy_error`. Use a temporary SQLite database for ORM tests; assert deterministic ordering, one row per stable ID after two initializations, updated fields after seed content changes, and a logged failure plus `None` when the session factory raises `OperationalError`. Add `tests/conftest.py` with a `database_url` fixture that creates a temporary SQLite database, sets `DATABASE_URL`, creates the schema, and clears the cached session factory before and after each test.

- [ ] **Step 2: Run the tests and verify they fail**

Run: `pytest -q tests/test_projects.py`

Expected: FAIL because the model, query, and initializer do not exist.

- [ ] **Step 3: Implement the SQLAlchemy model, query, and initializer**

Define the SQLAlchemy `Project` model with the interface fields. Implement `build_engine(database_url: str) -> Engine` and cached `get_session_factory() -> sessionmaker[Session]`; the latter reads `DATABASE_URL` lazily so importing/starting the web app does not require a live database. Query with `ORDER BY display_order, id`. Catch only `DatabaseConfigurationError` and `SQLAlchemyError` in `load_projects`, log with the exception details, and return `None`; let unrelated programming errors surface. In `initialize_database`, create tables with `build_engine` and select each stable ID before inserting or updating it. Begin `data/projects.json` as `[]`; make the script exit with a clear error if `DATABASE_URL` is missing.

- [ ] **Step 4: Run the storage tests**

Run: `pytest -q tests/test_projects.py`

Expected: PASS, including repeat initialization with changed seed data and deterministic tie ordering.

- [ ] **Step 5: Commit the project data layer**

```bash
git add app/database.py app/models.py app/projects.py app/seed.py data/projects.json scripts/init_db.py tests/conftest.py tests/test_projects.py docs/superpowers/plans/2026-10-01-database-driven-resume.md
git commit -m "feat: add MySQL-backed project storage"
```

### Task 3: Render Projects and Preserve the Page During Database Failure

**Files:**
- Modify: `app/main.py`
- Modify: `app/templates/resume.html`
- Modify: `tests/test_home.py`
- Modify: `tests/test_projects.py`

**Interfaces:**
- Consumes: `load_projects() -> list[Project] | None` from Task 2.
- Produces: the home route passes `projects: list[Project] | None` to `resume.html`; `None` means unavailable, while `[]` means available but empty.
- Produces: project cards use the stable project fields and render an external link only when `url` is present.

- [ ] **Step 1: Write the failing page-state tests**

Add `test_home_renders_database_projects`, `test_home_keeps_resume_visible_when_database_unavailable`, `test_home_shows_empty_projects_state`, and `test_project_without_url_has_no_link` to `tests/test_home.py`. Use the shared `database_url` fixture and real SQLite ORM path for successful and empty queries; replace `load_projects` with a `None` result for the route-level outage test. Assert profile and all non-project sections remain present in the outage case.

- [ ] **Step 2: Run the tests and verify they fail**

Run: `pytest -q tests/test_home.py`

Expected: FAIL because the route and template do not yet distinguish project success, empty, and unavailable states.

- [ ] **Step 3: Wire the project query into the rendered page**

Update `GET /` to call `load_projects()` only for the project section and pass its result to the template. Render ordered project cards for a non-empty list, a neutral empty state for `[]`, and a short unavailable message for `None`. Preserve all bundled resume sections in every case and render no anchor when a project URL is absent.

- [ ] **Step 4: Run focused and complete tests**

Run: `pytest -q tests/test_home.py tests/test_projects.py`

Expected: PASS for database-backed cards, database outage, empty projects, optional links, deterministic order, and idempotent seed behavior.

- [ ] **Step 5: Commit the integrated page**

```bash
git add app/main.py app/templates/resume.html tests/test_home.py tests/test_projects.py
git commit -m "feat: render projects without blocking resume"
```

### Task 4: Document Codespaces Setup and Azure Ubuntu Migration

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the dependency list, `DATABASE_URL`, `python scripts/init_db.py`, and `uvicorn app.main:app` defined by earlier tasks.
- Produces: copyable setup and run instructions for Codespaces and a later same-host MySQL/Azure Ubuntu deployment.

- [ ] **Step 1: Document local development and deployment**

Replace the minimal README with prerequisites, Python virtual environment and dependency installation, local MySQL service/database/user setup, an example `DATABASE_URL` using a clearly replaceable local credential, initializer and Uvicorn commands, and `pytest -q`. Document the corresponding Azure Ubuntu MySQL setup, private database access, protected environment file, systemd application service, and Nginx reverse proxy. Do not add real credentials or cloud provisioning.

- [ ] **Step 2: Review the documentation against the implementation interfaces**

Check each command and path against `requirements.txt`, `scripts/init_db.py`, and `app.main:app`. Confirm the Codespaces and VM instructions use the same app and `DATABASE_URL` and do not expose MySQL publicly.

- [ ] **Step 3: Commit the setup documentation**

```bash
git add README.md
git commit -m "docs: describe Codespaces and Azure setup"
```

- [ ] **Step 4: Run the full focused test suite**

Run: `pytest -q`

Expected: PASS for all home-page and project-storage tests.

### Task 5: Populate the Approved Resume Content

**Files:**
- Modify: `app/content.py`
- Modify: `app/templates/resume.html`
- Modify: `data/projects.json`
- Modify: `tests/test_home.py`
- Modify: `README.md`

**Interfaces:**
- Extends: `RESUME_CONTENT` with `experience` entries containing `role`, `organization`, `location`, `dates`, and `highlights: list[str]`; `education` entries containing `program`, `institution`, `location`, `dates`, `gpa`, and `coursework: list[str]`; `certifications` entries containing `name` and `year`; `leadership` entries containing `organization`, `institution`, and `dates`; and `contact` entries containing `label`, `value`, and optional `url`.
- Keeps LinkedIn and GitHub placeholder values as plain text with no `url`; only the email value receives a `mailto:` URL.
- Uses the project model unchanged; the seed record has stable ID `project-details-coming-soon`, no URL, and display order 1.

**User-approved content to enter exactly:**

- Profile name: `Nikhil Mandyam`
- Headline: `Information Systems and Business Analytics student at Loyola Marymount University`
- Summary: `Information Systems and Business Analytics student at Loyola Marymount University with experience supporting university programs, payroll operations, and digital marketing. Skills include SQL, Slate CRM, Bloomberg Terminal, and Microsoft Office Specialist.`
- Education: Loyola Marymount University, College of Business Administration; Bachelor of Science in Information Systems and Business Analytics; Los Angeles, CA; Expected May 2027; GPA: 3.3/4.0.
- Relevant coursework: Programming for Business Applications; Financial Accounting; Data Structures and Applications; Analytics in Operations and Supply Chain Management; Database Management Systems.
- Programs Office Assistant, Summer Programs, Loyola Marymount University; Los Angeles, CA; September 2024 - Present:
  - Served as the primary contact responding to up to 10 daily phone and email inquiries from prospective students and families while guiding 23+ students through the registration process for summer programs.
  - Supported an LMU summer program serving 1,000+ global applicants and operating with a $1.5M+ program budget.
  - Managed CRM data and coordinated scheduling and communication across a 12-person staff of directors, faculty, TAs, and RAs, helping reduce interdepartmental response times by an average of 2 business days.
- Payroll Student Staff, Student Employment Services, Loyola Marymount University; Los Angeles, CA; September 2023 - May 2024:
  - Processed weekly payroll for 150+ student employees, ensuring accurate payments with zero compliance discrepancies.
  - Verified timesheets and resolved errors with department supervisors, improving on-time approvals by 1 business day.
  - Maintained secure digital and physical payroll records under strict confidentiality protocols.
  - Managed front-desk operations and assisted 10+ visitors daily.
- Social Media Coordinator Intern, Health Haus; Beverly Hills, CA; May 2026 - August 2026:
  - Created and edited short-form content for Instagram, TikTok, and Google Blogs covering clinic services and wellness offerings.
  - Managed weekly content calendars and drafted captions, newsletter copy, and campaign materials.
  - Researched local partnership opportunities with apartments, coworking spaces, and fitness studios.
  - Tracked website, Google, email, and social media metrics to identify engagement trends and support digital marketing improvements.
- Skills: SQL; Slate CRM; Bloomberg Terminal; Microsoft Office Specialist.
- Certifications: Bloomberg Spreadsheet Analysis (2025); Bloomberg Environmental Social Governance (2025); Bloomberg Market Concepts (2025); Google Analytics 4 Certified (2025).
- Leadership: Information Systems and Business Analytics Society, Loyola Marymount University; August 2023 - Present.
- Contact: Email `nikhilmandyam@gmail.com` as a `mailto:` link; LinkedIn `[Add LinkedIn URL]` and GitHub `[Add GitHub URL]` as plain-text placeholders. Do not add phone or home address fields.
- Project placeholder: ID `project-details-coming-soon`; title `Project descriptions coming soon`; description `Project details will be added here once finalized.`; URL `null`; display order `1`.

- [ ] **Step 1: Write failing tests for the approved content**

Add `test_home_displays_approved_resume_details`, `test_contact_links_use_approved_email_and_keep_missing_profiles_as_text`, and `test_seeded_project_placeholder_is_displayed_without_link`. Assert the exact name, headline, education/GPA, coursework, experience highlights, certifications, leadership, email link, plain-text profile placeholders, and database-rendered project title/description. Assert no phone or home-address contact fields appear.

- [ ] **Step 2: Run the tests and verify they fail**

Run: `pytest -q tests/test_home.py::test_home_displays_approved_resume_details tests/test_home.py::test_contact_links_use_approved_email_and_keep_missing_profiles_as_text tests/test_home.py::test_seeded_project_placeholder_is_displayed_without_link`

Expected: FAIL because the page still contains generic placeholders, has no Certifications/Leadership sections, and the seed list is empty.

- [ ] **Step 3: Implement the approved content and display**

Populate `app/content.py` with the exact approved values above. Render work highlights, education GPA/coursework, Certifications, Leadership, and the contact values. Render LinkedIn/GitHub labels as plain text without `href`; render only the approved email as a `mailto:` link. Replace `data/projects.json` with the one approved no-link placeholder record, and update the README to identify all editable resume sections and the seeded placeholder.

- [ ] **Step 4: Run the focused and full test suites**

Run: `pytest -q tests/test_home.py tests/test_projects.py`

Expected: PASS with all approved content, no phone/address contact fields, plain-text missing-profile placeholders, project card, outage behavior, and storage cases.

- [ ] **Step 5: Commit the approved profile content**

```bash
git add app/content.py app/templates/resume.html data/projects.json tests/test_home.py README.md
git commit -m "feat: add approved resume content"
```
