# Database-Driven Resume Website Design

## Goal

Build a simple personal resume website for potential employers that can later
grow into a career platform. The first version should be quick to complete as a
class exercise, work in GitHub Codespaces, and be portable to an Azure Ubuntu
VM.

## Scope

The initial site is a single responsive resume page with:

- Profile basics and professional summary
- Work experience
- Education
- Skills
- Certifications
- Leadership
- Contact details or links
- A Projects section backed by a local MySQL database

There is no public API, separate JavaScript frontend, project editing UI,
authentication, or career-platform functionality in this version. Future
features should be added only when needed.

## Architecture

Use one Python FastAPI application to render HTML pages with Jinja2 templates.
Keep resume content other than projects bundled with the application so it can
be rendered without a database connection. Use SQLAlchemy for the MySQL data
access boundary; configure its connection using a `DATABASE_URL` environment
variable.

The application must not require a successful database connection to render the
resume page. Load projects independently of the static resume content. If the
project query fails, log the failure, render the rest of the page normally, and
show a brief unavailable message in the Projects section.

## Project data and updates

Store each project in MySQL with:

- Stable ID
- Title
- Description
- Optional external link
- Display order

Maintain project content in a small seed-data file as the source of truth and
provide a repeatable initializer command to create the initial schema and
upsert records by stable ID. Re-running initialization must not create
duplicates. There is no in-site editing interface. Do not expose MySQL directly
to the public internet.

If no finalized project descriptions are available, seed one clearly labeled
placeholder project:

- Stable ID: `project-details-coming-soon`
- Title: `Project descriptions coming soon`
- Description: `Project details will be added here once finalized.`
- External link: none
- Display order: 1

## User experience

Render a single responsive page with clear sections and in-page navigation.
Projects appear as simple cards, with links when supplied. When MySQL is
unavailable, the Projects section shows a concise status message; the profile,
summary, experience, education, skills, certifications, leadership, and contact
sections remain visible. Use the user-approved resume content, include the
provided email as a contact method, and use clearly labeled plain-text
placeholders for LinkedIn and GitHub until URLs are supplied. Do not include a
phone number or home address. No client-side framework is required.

## Development and deployment

Document how to install the Python dependencies and start a local MySQL service
in Codespaces, configure `DATABASE_URL`, initialize the database, and run the
app. Keep credentials and local environment settings out of version control.

For the later Azure Ubuntu VM move, document installing the same Python
application and a local MySQL service on the VM, configuring the same
`DATABASE_URL` interface, and running the application as a systemd service
behind Nginx. The initial project does not need automated cloud provisioning or
deployment.

## Verification

Add focused tests for:

- Rendering the resume and database-backed project cards when MySQL is
  available.
- Rendering all bundled resume sections and the Projects unavailable message
  when the project query fails.
- Re-running the database initializer without duplicating seed projects.
- Rendering the approved education, experience, skills, certifications,
  leadership, and contact content without a phone number or home address.
- Rendering the labeled project placeholder from MySQL when no finalized
  project descriptions are available.

## Acceptance criteria

1. The website presents the agreed resume sections for potential employers,
   including certifications and leadership.
2. Projects are read from MySQL, not hardcoded into the page.
3. A MySQL outage does not prevent the profile and other resume content from
   rendering.
4. The Codespaces setup and Azure Ubuntu deployment path use the same
   application and database configuration interface.
5. The first version avoids an admin UI, public API, authentication, and
   unrelated platform features.
6. The public profile includes no phone number or home address, and missing
   LinkedIn/GitHub URLs are clearly labeled placeholders rather than invented
   links.
