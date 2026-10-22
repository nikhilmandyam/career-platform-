# Post-cutover migration verification performed October 21, 2026

## Purpose

This verification was performed after the original cutover. It is not presented
as evidence of the historical cutover; it verifies current source-to-target data
preservation.

## Seed baseline

`data/projects.json` remains unchanged and contains the old placeholder values:

- `id`: `project-details-coming-soon`
- `title`: `Project descriptions coming soon`
- `description`: `Project details will be added here once finalized.`
- `url`: `null`
- `display_order`: `1`

## Azure MySQL source before update

- `row_count`: 1
- `id`: `project-details-coming-soon`
- `title`: `Project descriptions coming soon`
- `description`: `Project details will be added here once finalized.`
- `url`: `NULL`
- `display_order`: 1

## Azure source after update

- `rows_changed`: 1
- `row_count`: 1
- `id`: `project-details-coming-soon`
- `title`: `Career Platform Website`
- `description`: `Personal career platform deployed on Railway with PostgreSQL, a custom domain, Zoho Mail, and Google Analytics.`
- `url`: `https://dueyy.me`
- `display_order`: 1

## Railway PostgreSQL preflight

- Connection succeeded.
- `row_count`: 1
- The target row still matched the old placeholder values before the update.

## Railway PostgreSQL after update

- `row_count`: 1
- `id`: `project-details-coming-soon`
- `title`: `Career Platform Website`
- `description`: `Personal career platform deployed on Railway with PostgreSQL, a custom domain, Zoho Mail, and Google Analytics.`
- `url`: `https://dueyy.me`
- `display_order`: 1
- All fields exactly matched the verified Azure source.

## Conclusion

- Source count = target count = 1.
- Content matches field-by-field.
- Current database data now differs from `data/projects.json`.
- Restoring seed data alone would not reproduce the current production row.
