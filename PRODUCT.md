# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are recruiters, hiring managers, and other professional stakeholders evaluating Nikhil Mandyam for internships, student roles, and entry-level opportunities in business analytics, information systems, operations, and digital marketing.

Secondary users include collaborators, alumni, and anyone browsing the site for a short professional overview. The site is intended for browser-based review on desktop and mobile layouts.

## Product Purpose

This product is a personal career website and resume that presents the candidate's profile, experience, education, skills, certifications, leadership activity, and project work. Success means a visitor can quickly understand the candidate's strengths, relevant experience, and how to contact them.

## Positioning

The product is a personal professional portfolio/resume that positions the candidate as a business-minded student with operations, payroll, CRM, and digital marketing experience, grounded in an information systems and business analytics degree. It differs from a generic portfolio by being grounded in actual LMU roles, coursework, and project data rather than a broad personal brand story.

## Operating Context

The site is a small FastAPI application that renders resume content from `app/content.py` and project cards from a local MySQL database. The resume continues to render if MySQL is unavailable; only the Projects section temporarily indicates that content is unavailable. The content is maintained as a personal career profile rather than a broad publishing platform.

The project documentation describes development and preview in GitHub Codespaces and production deployment to an Azure Ubuntu VM. MySQL remains private on the VM, and credentials are managed through environment variables rather than checked into the repository. The current public site is served from Azure through Nginx over HTTPS.

## Capabilities and Constraints

- Renders profile, summary, experience, education, skills, certifications, leadership, and contact information.
- Loads project cards from a local MySQL database and supports a fallback state when the database is unavailable.
- Keeps the personal profile factual and privacy-conscious; the README explicitly warns against adding a phone number or home address.
- The repository currently includes placeholder or incomplete LinkedIn, GitHub, and project values. These states are intentionally supported by the application and existing tests. They should not be replaced with invented information; real values should only be added when verified.
- The product is a personal resume website, not a broad marketplace, SaaS application, or multi-role system.

## Brand Commitments

The repository does not define a separate formal brand guide, but the existing site uses a restrained navy and teal professional resume aesthetic with clear typography, card-based sections, and a recruiter-oriented layout. Design changes should refine that existing direction rather than replace it with an unrelated visual identity.

## Evidence on Hand

- `README.md`: describes the site as a personal resume website and deployment workflow.
- `app/content.py`: contains the candidate's profile, summary, experience, education, skills, certifications, leadership, and placeholder contact links.
- `data/projects.json`: contains seeded project records, including a clearly labeled placeholder project entry.
- `app/database.py` and `app/models.py`: show the local MySQL-backed project data model.
- Documentation indicates the site should avoid adding a phone number or home address, and should replace placeholder URLs only after final URLs are available.

## Product Principles

1. Clarity over decoration: the resume should be easy to scan and understand quickly.
2. Professional credibility: experience and credentials should read as real, verifiable, and relevant.
3. Privacy and accuracy: only appropriate professional contact details and confirmed information should appear.
4. Resilience: the site should remain useful even if the project data source is unavailable.
5. Maintainability: resume content and project data should be easy to update with minimal friction.

## Accessibility & Inclusion

The site should remain easy to read and navigate on both desktop and mobile screens. It should avoid exposing unnecessary personal information, and all public content should be professional, respectful, and accessible to recruiters and hiring managers evaluating the candidate.