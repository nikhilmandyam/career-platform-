# AWS Career Platform Migration Implementation Plan

> **For agentic workers:** This is an ordered infrastructure runbook, not authorization to execute it. Do not begin provisioning until the owner explicitly approves execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stage the existing Career Platform app on one EC2 instance in `us-east-1` with a private Single-AZ RDS PostgreSQL 18 database, verify it at `aws.dueyy.me`, then cut over the production domain only after approval.

**Architecture:** Ubuntu on EC2 serves Nginx publicly on ports 80/443 and Uvicorn/FastAPI only on loopback port 8000. RDS PostgreSQL is private in the same default VPC; its security group accepts port 5432 only from the EC2 security group. Restore the verified Railway backup into a new RDS database before starting the app. Railway remains live and unchanged through staging and initial production verification.

**Tech Stack:** Ubuntu Server 26.04 LTS (Canonical, x86_64), EC2 `t3.micro` On-Demand with Standard CPU credits, Nginx, Uvicorn, FastAPI, SQLAlchemy, psycopg 3, RDS PostgreSQL 18, Cloudflare DNS-only staging record, Let's Encrypt Certbot.

**Spec:** User-provided Section 6 constraints and the completed blind-spot interview in this conversation; no separate spec file.

## Plan status

Not executed. No AWS resources have been created; Railway and Cloudflare DNS have not been changed. No application source files are planned to change. The app deployment baseline is repository commit `7b79828` (the inspected `aws-migration` HEAD, matching `origin/main` at plan time); the currently deployed Railway revision is unknown, so this is not claimed to be an exact copy of production.

## Global Constraints

- Region: `us-east-1` (Northern Virginia); use the default VPC.
- Keep Railway live and unchanged until AWS passes staging verification.
- EC2: Ubuntu Server 26.04 LTS from Canonical, x86_64, `t3.micro`, On-Demand, Standard CPU credits, 20 GB encrypted gp3, IMDSv2 required, public subnet, one public IPv4/Elastic IP.
- RDS: PostgreSQL 18, Single-AZ, private/not publicly accessible, 20 GB encrypted gp3, storage autoscaling off, automated backups retained for 7 days; use `db.t3.micro` or `db.t4g.micro` only after confirming the account's applicable eligibility.
- Keep the generated database password and `DATABASE_URL` outside Git. Do not install the PostgreSQL server on EC2; install only client utilities needed for restore/verification.
- Expose only SSH (port 22 restricted to the owner's current public IP), HTTP (80), and HTTPS (443) on EC2. Never allow public access to Uvicorn port 8000.
- Allow RDS port 5432 only from the EC2 security group.
- Serve staging on `aws.dueyy.me` through Nginx and Certbot; the Cloudflare record is DNS-only and points to the EC2 Elastic IP.
- Do not change the production/root or `www` DNS records until staging passes and the owner explicitly approves cutover.
- Do not run `scripts/init_db.py` or seed `data/projects.json` on AWS. Restore the verified Railway backup into a new, empty RDS database.
- Do not modify Railway, commit, or push as part of this plan.
- AWS Budgets notifications are alerts, not a hard spend cap. Verify projected and actual charges before and after provisioning.

## Review Focus

- **Wrong destination or destructive restore:** restore only into a new, verified-empty RDS database; never use `--clean`, `DROP`, or a restore command against Railway.
- **Unintended public exposure:** check the EC2 and RDS security-group rules and confirm port 8000 is not internet-reachable.
- **Stale or mismatched code/data:** pin the staged application revision and compare all restored project fields with the verified backup; the Railway SHA is unknown.
- **False-positive health checks:** the app has no dedicated health endpoint, the home page returns 503 when projects are unavailable, and `HEAD /` is unsupported; verify with `GET /` and inspect the rendered project data.
- **DNS/TLS/cost surprises:** preserve the existing production DNS records during staging; verify certificate renewal and costs, including public IPv4/EIP charges and backup/storage usage.

---

## Exact files and configuration

### Repository

No tracked application files are expected to change:

- Deploy the app from commit `7b79828`; do not run the seed script.
- `app/main.py` creates the SQLAlchemy schema at startup when `DATABASE_URL` is set. Therefore, restore the `projects` table before starting the service.
- `app/projects.py` reads project rows; the app has no project-editing UI or background jobs.
- `requirements.txt` includes `psycopg[binary]`; use a `postgresql+psycopg://` URL in the service environment.
- `app/templates/resume.html` contains the GA4 tag `G-W4BCV8GMQY`; browser-based staging visits may add events to the existing GA4 property. Prefer HTTP/curl checks or account for/filter test traffic.

If staging reveals a source-code defect, stop and request approval before changing application files or the selected revision.

### EC2 filesystem

| Path | Purpose |
|---|---|
| `/opt/career-platform/` | Application checkout at the selected commit; create a virtual environment at `/opt/career-platform/.venv`. |
| `/etc/career-platform.env` | Root-owned, service-group-readable environment file containing `DATABASE_URL`; mode `0640`. |
| `/etc/systemd/system/career-platform.service` | systemd unit; run Uvicorn as a dedicated non-login `career-platform` user, one worker, bound to `127.0.0.1:8000`. |
| `/etc/nginx/sites-available/career-platform` | Nginx virtual host for `aws.dueyy.me`; enable using `/etc/nginx/sites-enabled/career-platform`. Certbot may update this file for TLS and redirects. |
| `/etc/letsencrypt/live/aws.dueyy.me/` | Certbot-managed certificate and private key; do not hand-edit. Confirm the renewal configuration and timer after issuance. |
| `/etc/letsencrypt/live/dueyy.me/` | Separate Certbot-managed production certificate, obtained only after staging passes and the owner approves the production TLS step. |
| `/etc/letsencrypt/cloudflare.ini` | Optional-to-staging, required-for-pre-cutover DNS-01 credential file for a zone-scoped Cloudflare API token; root-owned, mode `0600`, never committed. |
| `/etc/ssl/certs/rds-ca-bundle.pem` | Current AWS RDS CA bundle for verified TLS from the app to RDS. |
| `/home/ubuntu/career-platform-migration/railway-backup` | Temporary, mode-`0600` copy of the verified backup used for restore; remove only this temporary copy after successful verification. Keep the independent original backup. |
| `/home/ubuntu/.pgpass` | Temporary mode-`0600` libpq password file for the RDS administrator during restore; remove after database verification. |

No PostgreSQL server is installed on EC2. Install Nginx, Python/venv support, Git, Certbot with its Nginx plugin, and PostgreSQL client utilities only.

### AWS resources/configuration

- `career-platform-ec2-sg`: inbound TCP 22 from the owner's current public IPv4 `/32`; TCP 80 and 443 from the public internet; no rule for 8000.
- `career-platform-rds-sg`: inbound TCP 5432 with source set to `career-platform-ec2-sg`, not a CIDR range.
- EC2: default VPC, public subnet with internet route, selected SSH key pair, public IPv4/Elastic IP, required IMDSv2, encrypted 20 GB gp3 root volume, `t3.micro`, Standard CPU credits.
- RDS: default VPC, not publicly accessible, Single-AZ, PostgreSQL 18, 20 GB encrypted gp3, storage autoscaling disabled, 7-day automated backups, and `career-platform-rds-sg`. Use the default DB subnet group if valid; otherwise create one spanning at least two AZs while keeping the DB instance itself Single-AZ.
- RDS database: `career_platform`; application login: `career_app`; generated master and application passwords are stored outside Git. Restore as the RDS administrator, then grant the app login `CONNECT`, schema `USAGE`, and `SELECT` on `public.projects`. Do not grant the app login superuser or table-write privileges.
- Cloudflare staging only: DNS-only A record `aws` → EC2 Elastic IP. Do not change the existing apex/root or `www` records in the staging phase.

## Ordered migration tasks

### Task 1: Complete read-only preflight

**Files/configuration:** None. No resource creation or provider changes in this task.

- [ ] **Step 1: Pin the application artifact.** Confirm the intended source is commit `7b79828` and record that the Railway deployed SHA remains unknown. Review Railway deployment metadata read-only if accessible; do not change its service or variables.
- [ ] **Step 2: Run the app's existing tests on the selected source.** Run `pytest -q`; expected result is all tests pass. If not, stop and resolve the source/test issue before provisioning.
- [ ] **Step 3: Verify account and network prerequisites read-only.** Confirm effective IAM permissions cover EC2, EIP, security groups, RDS, DB subnet groups, and required VPC reads. Confirm the default VPC, public subnet routing, and suitable RDS subnets exist in `us-east-1`. Do not alter the IAM policy or VPC.
- [ ] **Step 4: Confirm cost and RDS eligibility.** Check the account's Free Tier/credits eligibility for PostgreSQL 18 and the selected DB class, public IPv4/EIP pricing, RDS storage/backups, and expected data transfer. Record the chosen class (`db.t3.micro` or `db.t4g.micro`) and expected charges. Stop if the professor's constraints cannot be met without unapproved spend.
- [ ] **Step 5: Inspect the independent backup without modifying it.** Record its format, size, and checksum; confirm it is the backup already restore-tested. Do not print or expose credentials.
- [ ] **Step 6: Record the current production DNS values and TTL read-only.** Confirm `aws.dueyy.me` remains unused. Save the exact existing apex/root and `www` values for rollback; do not edit DNS.

**Gate:** No AWS creation until these checks pass and the owner authorizes provisioning.

### Task 2: Create network controls and the EC2 host

**Files/configuration:** AWS security groups, EC2 instance, EIP, key-pair selection. No repository files.

- [ ] **Step 1: Create `career-platform-ec2-sg`.** Add only TCP 22 from the owner's current public IPv4 `/32`, and TCP 80/443 from the internet. Verify no inbound 8000 rule exists.
- [ ] **Step 2: Create `career-platform-rds-sg`.** Add TCP 5432 whose source is `career-platform-ec2-sg`; do not allow public or laptop CIDRs.
- [ ] **Step 3: Launch one EC2 instance in `us-east-1`.** Use the specified Canonical Ubuntu 26.04 LTS x86_64 AMI, `t3.micro`, On-Demand, Standard CPU credits, 20 GB encrypted gp3, IMDSv2 required, default VPC public subnet, selected SSH key, and `career-platform-ec2-sg`.
- [ ] **Step 4: Allocate and associate one Elastic IP.** Record the EIP and confirm the instance has only the intended public IPv4 exposure.
- [ ] **Step 5: Verify the host before installing the app.** Confirm AMI, architecture, instance type, volume encryption/size, IMDSv2, subnet/route, security-group rules, SSH restriction, and public reachability on only the intended ports.

**Rollback:** If the host is misconfigured, stop and correct it before installing the app. Do not remove the independent database backup or change production DNS. Any eventual instance/EIP deletion requires explicit owner approval and a cost/evidence check.

### Task 3: Create private RDS and restore the verified backup

**Files/configuration:** RDS instance, DB subnet group if needed, RDS security group, temporary backup copy on EC2. Do not modify Railway.

- [ ] **Step 1: Create the RDS database.** Use PostgreSQL 18, the preselected eligible micro class, Single-AZ, default VPC, not publicly accessible, 20 GB encrypted gp3, storage autoscaling off, 7-day automated backups, and `career-platform-rds-sg`. Confirm the DB subnet group has subnets in at least two AZs even though the DB deployment is Single-AZ.
- [ ] **Step 2: Create the database and application login.** Create `career_platform` and `career_app` using the RDS administrator. Generate passwords and keep them outside Git and shell history.
- [ ] **Step 3: Transfer the verified backup to EC2.** Create `/home/ubuntu/career-platform-migration/` with mode `0700`; copy the independent backup there with mode `0600`. Verify the copied checksum matches the recorded checksum.
- [ ] **Step 4: Restore into a verified-empty target.** First confirm `career_platform` contains no application tables or rows. For a custom archive use `pg_restore`; for plain SQL use `psql`. Use the format-appropriate restore command with ownership/ACL handling appropriate for RDS. Do not use `--clean`, `DROP`, or any command targeting Railway. If the target is not empty or the format is ambiguous, stop before restoring.
- [ ] **Step 4a: Use the tested format-specific command.** Put the RDS administrator password in `/home/ubuntu/.pgpass` (mode `0600`), not in command arguments. For a custom archive, restore with `pg_restore --host=<RDS-ENDPOINT> --port=5432 --username=<RDS-ADMIN> --dbname=career_platform --no-owner --no-acl --exit-on-error /home/ubuntu/career-platform-migration/railway-backup`. For plain SQL, use `psql --host=<RDS-ENDPOINT> --port=5432 --username=<RDS-ADMIN> --dbname=career_platform --set ON_ERROR_STOP=on --file=/home/ubuntu/career-platform-migration/railway-backup`. Before using the plain-SQL form, inspect the dump header and restore-test notes; if it contains `DROP`, `CREATE DATABASE`, or a `\connect` to a source database, stop and prepare a reviewed target-safe copy rather than executing it as-is.
- [ ] **Step 5: Grant least-privilege app access.** Grant `career_app` database `CONNECT`, `public` schema `USAGE`, and `SELECT` on `public.projects`. Keep the RDS administrator credential out of the app environment.
- [ ] **Step 6: Verify the restored rows before starting the app.** Compare row count and every field (`id`, `title`, `description`, `url`, `display_order`) with the independent backup. Expected result is an exact match. Save non-secret verification evidence.
- [ ] **Step 7: Remove only the temporary EC2 copy after verification.** Keep the independent original backup. Do not remove the RDS automated backups.

**Data-overwrite warning:** The restore can overwrite or conflict with data if pointed at a non-empty/wrong database. Restore only to the new, verified-empty `career_platform` database; no destructive restore flags. The Railway source is never a restore target.

**Rollback:** On any mismatch, stop before starting the app or cutting over DNS. Preserve the independent source backup and evidence; do not overwrite Railway or retry with destructive flags. Diagnose the target and use a newly created empty target database only after owner review.

### Task 4: Install and configure the application service

**Files/configuration:** `/opt/career-platform/`, `/etc/career-platform.env`, `/etc/systemd/system/career-platform.service`, `/etc/nginx/sites-available/career-platform`, enabled symlink.

- [ ] **Step 1: Install runtime packages.** On EC2 install Python/venv support, Git, Nginx, Certbot with its Nginx plugin, and PostgreSQL client tools. Do not install PostgreSQL server.
- [ ] **Step 2: Deploy the pinned source.** Check out commit `7b79828` under `/opt/career-platform`; create a virtual environment and install `requirements.txt`. Keep the source readable by the service account; run the app as a dedicated non-login `career-platform` user.
- [ ] **Step 3: Install the RDS CA bundle.** Place the current AWS RDS CA bundle at `/etc/ssl/certs/rds-ca-bundle.pem` and ensure it is readable by the service.
- [ ] **Step 4: Configure `/etc/career-platform.env`.** Create as `root:career-platform`, mode `0640`, containing only the app's `DATABASE_URL`:

  ```text
  DATABASE_URL=postgresql+psycopg://career_app:<URL-ENCODED-PASSWORD>@<PRIVATE-RDS-ENDPOINT>:5432/career_platform?sslmode=verify-full&sslrootcert=/etc/ssl/certs/rds-ca-bundle.pem
  ```

  Edit with `sudoedit`; do not put credentials in Git, command arguments, or logs.

- [ ] **Step 5: Create `/etc/systemd/system/career-platform.service`.** Use this service configuration:

  ```ini
  [Unit]
  Description=Career Platform FastAPI application
  Wants=network-online.target
  After=network-online.target

  [Service]
  Type=simple
  User=career-platform
  Group=career-platform
  WorkingDirectory=/opt/career-platform
  EnvironmentFile=/etc/career-platform.env
  ExecStart=/opt/career-platform/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --proxy-headers --forwarded-allow-ips=127.0.0.1
  Restart=on-failure
  RestartSec=5

  [Install]
  WantedBy=multi-user.target
  ```

- [ ] **Step 6: Create the initial HTTP Nginx site.** Configure `/etc/nginx/sites-available/career-platform` with this staging server block and enable it using `/etc/nginx/sites-enabled/career-platform`. Disable the default site only after recording its prior state.

  ```nginx
  server {
      listen 80;
      server_name aws.dueyy.me;

      location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  ```
- [ ] **Step 7: Start and verify the app locally.** Run `systemctl daemon-reload`, enable/start `career-platform` and Nginx, and check `systemctl is-active`, `nginx -t`, and `ss -ltnp`. Verify Uvicorn listens only on `127.0.0.1:8000`; `curl -f http://127.0.0.1:8000/` must return 200 and show the expected project. If it returns 503 or lacks the row, inspect logs and DB connectivity; do not proceed to DNS.

**Rollback:** Disable/stop the new systemd service and Nginx site, preserving the RDS and original backup. No Railway or production DNS changes are involved.

### Task 5: Configure staging DNS/TLS and verify externally

**Files/configuration:** Cloudflare DNS-only `aws` A record; Certbot-managed certificate; Nginx site file.

- [ ] **Step 1: Add only the staging record after the local app passes.** In Cloudflare create `aws` A → EC2 Elastic IP with proxy status **DNS only**. Do not change the apex/root or `www` records.
- [ ] **Step 2: Verify DNS and HTTP reachability.** Confirm `aws.dueyy.me` resolves to the EIP and external GET on port 80 reaches Nginx. Do not test with `HEAD`.
- [ ] **Step 3: Issue the staging certificate.** Run Certbot's Nginx plugin for `aws.dueyy.me`, request HTTP-to-HTTPS redirection, and verify the certificate's hostname, validity, and automatic renewal timer/configuration.
- [ ] **Step 4: Run external staging checks.** Confirm:
  - `GET https://aws.dueyy.me/` returns 200, includes the expected profile and restored project, and does not show “Projects temporarily unavailable.”
  - `GET https://aws.dueyy.me/privacy` and `/static/style.css` return 200.
  - HTTP redirects to HTTPS and the TLS certificate validates for `aws.dueyy.me`.
  - Port 8000 is unreachable from outside; RDS is not publicly reachable; the RDS SG allows 5432 only from the EC2 SG.
  - The app, Nginx, and RDS logs show no configuration or connection errors; after a controlled EC2 reboot, the app and Nginx return and the local GET succeeds.
- [ ] **Step 5: Record the verification gate.** Record tested code SHA, RDS row comparison, HTTP/TLS results, security-group boundaries, and reboot result. If any check fails, leave production DNS untouched and correct staging first.

**Rollback:** Remove only the `aws` staging A record if staging is abandoned; leave apex/root and `www` records unchanged. Keep or stop AWS resources only with owner approval and after cost/data review.

### Task 6: Cut over production only after explicit approval

**Files/configuration:** `/etc/letsencrypt/cloudflare.ini`, `/etc/letsencrypt/live/dueyy.me/`, `/etc/nginx/sites-available/career-platform`, and the existing Cloudflare apex/root record, using the exact prior value captured in Task 1. Do not alter the `www` redirect unless separately approved.

- [ ] **Step 1: Reconfirm source data.** Immediately before cutover, compare live Railway project data read-only with the restored RDS row. If it differs, stop; take and verify a fresh independent backup and reconcile into RDS before cutover. Do not modify Railway.
- [ ] **Step 2: Obtain owner approval.** Proceed only after the staging gate passes and the owner explicitly approves changing production DNS.
- [ ] **Step 3: Prepare production TLS without routing production traffic.** Install the Certbot Cloudflare DNS plugin. Create a least-privilege Cloudflare API token scoped to DNS edit/read for `dueyy.me`; store it in `/etc/letsencrypt/cloudflare.ini` with mode `0600` and the plugin's `dns_cloudflare_api_token = <TOKEN>` setting. After staging passes and approval is granted, use DNS-01 to issue `/etc/letsencrypt/live/dueyy.me/` before changing the apex/root record. This adds only the ACME challenge TXT record, not a production routing change; confirm Certbot renewal uses the protected token.
- [ ] **Step 4: Add the production Nginx virtual host.** Extend `/etc/nginx/sites-available/career-platform` with this HTTPS/redirect configuration and the same proxy headers as the staging block. Run `nginx -t`, reload Nginx, and verify the certificate and virtual host while the root record still points to Railway, using `curl --resolve dueyy.me:443:<EC2-EIP> https://dueyy.me/`; do not proceed if this cannot be verified without changing production routing.

  ```nginx
  server {
      listen 80;
      server_name dueyy.me;
      return 301 https://$host$request_uri;
  }

  server {
      listen 443 ssl;
      server_name dueyy.me;
      ssl_certificate /etc/letsencrypt/live/dueyy.me/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/dueyy.me/privkey.pem;

      location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  ```
- [ ] **Step 5: Change only the apex/root routing.** Update the current Cloudflare apex/root record to route `dueyy.me` to the EC2 Elastic IP using a record type supported by the current zone. Preserve the existing `www` redirect and the `aws` staging record.
- [ ] **Step 6: Verify production externally.** Confirm HTTPS and HTTP-to-HTTPS behavior, page content, project data, `/privacy`, static CSS, and Nginx/Uvicorn/RDS logs at `https://dueyy.me`. Keep Railway live during propagation and initial AWS verification.
- [ ] **Step 7: Retain rollback state.** Record the prior DNS value and change time. Do not delete Railway, the independent backup, RDS backups, or the staging host as part of cutover.

### Rollback after production cutover

- If AWS fails staging checks before cutover, make no production DNS change; correct or stop AWS staging.
- If production fails after cutover, restore the exact prior apex/root Cloudflare value captured in Task 1. Keep the Railway app and database online and unchanged; verify `dueyy.me` returns to Railway after DNS propagation.
- Leave AWS EC2/RDS and the restored data intact while diagnosing. Do not restore an older backup over either database or assume DNS rollback reverses database changes. Although the current app has no project-write UI, reconcile any manual/external writes before another cutover.
- Remove the `aws` staging record or AWS resources only after explicit approval, evidence retention, and a final data/cost review.

## Data-overwrite steps at a glance

1. **RDS restore (Task 3, Step 4):** the only planned data import. It is safe only when `career_platform` is verified empty and the restore target is confirmed as the new RDS endpoint. Never use `--clean` or point it at Railway.
2. **Final source comparison (Task 6, Step 1):** read-only. If data changed after the verified backup, stop and refresh/reconcile the backup before cutover.
3. **Seed script:** explicitly prohibited on AWS; it would upsert the tracked placeholder over production project content.
4. **Rollback:** DNS rollback changes traffic only; it does not restore or reconcile database contents.

## Completion criteria

- Staging and production use the recorded application revision and the restored project data matches the verified backup field-by-field.
- EC2 serves Nginx on 80/443; Uvicorn binds only to loopback 8000.
- RDS is PostgreSQL 18, private, Single-AZ, encrypted, backed up for 7 days, and accepts connections only from the EC2 security group.
- `aws.dueyy.me` passes all external checks before any production DNS change.
- Railway remains live and unchanged through staging and cutover verification; the independent backup is retained.
