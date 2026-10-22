# Retrospective Railway Migration Record

## 1. Retrospective note

This is a retrospective engineering record written after the migration. No
contemporaneous Railway migration plan was committed; this record is reconstructed
from repository history, current code/configuration, and the listed evidence
documents. It is not the original pre-cutover plan.

## 2. What moved through Git

Git history records commits for the FastAPI application, PostgreSQL compatibility,
Railway runtime configuration, and related tests. The Railway compatibility
commit is `e21a99f5d48f7709cf76939d1048875f8952972c`
(`feat: prepare app for Railway and analytics`). Analytics and privacy changes
are also recorded in Git; Exercise 06 documents GA4 events and the privacy page.

## 3. What did not move through Git

- Database contents were persisted in the database, not carried by Git. The
  tracked `data/projects.json` remains the old placeholder seed.
- Secrets and environment values are not part of the repository evidence.
- DNS records and cloud-provider configuration are external to Git. The
  repository does not establish the current DNS records or complete provider
  settings.

## 4. MySQL-to-PostgreSQL compatibility changes

- `requirements.txt` includes both `pymysql` and `psycopg[binary]`.
- The SQLAlchemy engine uses the configured `DATABASE_URL`; current application
  code reads that variable from the environment.
- Application startup calls schema creation when `DATABASE_URL` is configured.
  Schema creation uses SQLAlchemy metadata and does not itself seed project data.
- The Railway `Procfile` starts Uvicorn on `0.0.0.0:$PORT` and enables forwarded
  proxy headers.

## 5. Data preservation verification

See [Post-cutover data verification](railway-data-verification.md). That
verification records one row at the Azure source and one at the Railway target,
with the target fields exactly matching the verified Azure source field by
field. It also records that the database row differs from the unchanged seed
placeholder in `data/projects.json`.

## 6. Cutover

The available evidence supports a post-cutover verification performed October
21, 2026: Railway PostgreSQL had one row matching the old placeholder before
the guarded update, and one row matching the updated Azure source after it.
This verifies the recorded source-to-target data state at that time.

The original cutover's exact time, deployment sequence, DNS switch sequence, and
which application revision first served production are not established by these
artifacts. They should not be inferred from the post-cutover verification.

## 7. Rollback procedure

**Application code:** Git identifies
`e21a99f5d48f7709cf76939d1048875f8952972c` as the Railway compatibility commit.
The available evidence does not prove that this revision was previously deployed
and known-good in production, so it is a candidate baseline, not a verified
production rollback point. Before rollback, identify a previously validated
deployment revision from deployment records, confirm it is compatible with the
current database, then redeploy that revision or revert the relevant code
changes, test, and deploy through the normal release process.

**DNS:** If Azure is still running and its application and TLS endpoint have
been confirmed healthy, DNS could be changed at the currently authoritative
provider to route the domain back to the documented Azure VM address
`9.205.30.229`. The current DNS provider, records, and Azure availability are
not verified here; confirm them before making a change and allow for DNS
propagation.

**Database:** Do not assume application or DNS rollback restores database
contents. Post-cutover writes may exist in Railway PostgreSQL and must be
identified and reconciled with the intended target before directing traffic to
Azure or restoring older data. If the databases have diverged, reconcile and
validate the data explicitly; these records establish no safe automatic
database rollback.

## 8. Azure vs. Railway responsibilities

| Responsibility | Azure evidence | Railway evidence / boundary |
|---|---|---|
| OS | Ubuntu VM is documented. | OS is provider-managed; exact OS is not established here. |
| Runtime | Uvicorn managed by systemd is documented. | Uvicorn is invoked by the `Procfile`; platform process management is external to Git. |
| Web entry point | Nginx receives web traffic and proxies to Uvicorn. | `Procfile` binds Uvicorn to `0.0.0.0:$PORT`; forwarded proxy headers are enabled. |
| TLS | Let's Encrypt on the Azure Nginx endpoint is documented. | Railway TLS configuration/termination is not independently established by these artifacts. |
| Application code | Versioned in Git; the exact Azure production revision is not established here. | Versioned in Git; the exact Railway production revision is not established here. |
| Configuration/secrets | Deployment configuration is external to Git; secret values are not recorded here. | Environment configuration is external to Git; secret values and complete provider settings are not recorded here. |
| Database software | Azure MySQL is the documented source. | Railway PostgreSQL is the verified target. |
| Database data | Source row values are recorded in the verification evidence. | Target row values are recorded and matched field-by-field in that evidence. |
| DNS | Historical evidence documents Cloudflare DNS directing traffic to Azure. | Current DNS provider, records, and Railway routing are not established here. |

## 9. Remaining limitations / unverified historical items

- No contemporaneous Railway migration plan or complete cutover log is in Git.
- The original cutover time, order of operations, and first production commit are
  unverified.
- The exact production revision currently deployed, and a previously deployed
  known-good rollback revision, are not established by the cited repository
  evidence.
- Current Railway TLS, DNS, environment settings, and cloud-provider
  configuration have not been independently verified by this record.
- The data verification documents the compared rows at the time of verification;
  it does not establish whether later writes occurred.
