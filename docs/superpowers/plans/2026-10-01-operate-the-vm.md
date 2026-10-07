# Operate the Azure VM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve the career-platform resume site at `http://9.205.30.229` through Nginx on port 80, with a two-worker Uvicorn service managed by systemd.

**Architecture:** Nginx accepts public HTTP traffic and proxies it to Uvicorn bound only to `127.0.0.1:8000`. systemd runs Uvicorn as `azureuser`, loads the existing MySQL connection from a protected environment file, starts it at boot, and restarts it after failure.

**Tech Stack:** Ubuntu 24.04, Nginx, systemd, Uvicorn, FastAPI, local MySQL.

**Spec:** User-provided requirements in the task; no separate design document.

## Global Constraints

- VM: `vm-career-platform`, resource group `rg-career-platform`, Ubuntu 24.04, public IP `9.205.30.229`, private IP `172.16.0.4`.
- App: `/home/azureuser/career-platform`; virtual environment: `/home/azureuser/career-platform/.venv`.
- systemd unit name: `career-platform`; service account: `azureuser`.
- Uvicorn must use 2 workers and bind only to `127.0.0.1:8000`.
- Nginx is the public web server on port 80; visitors use `http://9.205.30.229` with no port number.
- The VM owner adds the Azure Allow-HTTP-80 inbound rule at priority 320. Do not make or script Azure changes.
- Never open port 8000 to the Internet. Do not modify application source or add tests.
- MySQL stays local to the VM; do not expose its port.
- Perform the steps later over SSH as `azureuser`, using `sudo` only for system configuration. This plan does not execute any VM changes.

## Review Focus

- An existing manual Uvicorn process may already occupy port 8000; stop it cleanly before starting the service, and verify the service owns the listener.
- `DATABASE_URL` contains credentials; store it in a root-owned, `azureuser`-readable environment file and never print it in verification output.
- The public listener must be `127.0.0.1:8000`, not `0.0.0.0:8000` or `[::]:8000`; verify locally and confirm no Azure rule permits 8000.
- External HTTP success depends on the owner adding the Azure port-80 rule; a failed external request before that is not evidence of an application or Nginx failure.

---

## Files and VM Configuration

- Create `/etc/career-platform.env` for the existing `DATABASE_URL`, mode `0640`, owned by `root:azureuser`.
- Create `/etc/systemd/system/career-platform.service` for the app process.
- Create `/etc/nginx/sites-available/career-platform` and enable it with a symlink in `/etc/nginx/sites-enabled/`.
- Do not change Azure configuration, host firewall rules, or application files.

## Task 1: Configure the systemd Application Service

**Files / VM configuration:**
- Create: `/etc/career-platform.env`
- Create: `/etc/systemd/system/career-platform.service`

- [ ] **Step 1: Check the current VM state.** SSH to the VM. Confirm `/home/azureuser/career-platform` and `/home/azureuser/career-platform/.venv/bin/uvicorn` exist, check `sudo systemctl status mysql --no-pager`, and check whether port 8000 is currently listening with `sudo ss -ltnp 'sport = :8000'`. Check whether `/etc/career-platform.env` and `/etc/systemd/system/career-platform.service` already exist; preserve backups of any existing files before replacing them. Do not run restart/crash tests.
- [ ] **Step 2: Stop the manually launched server cleanly.** In the terminal running Uvicorn, press Ctrl-C. Do not kill unrelated processes. Confirm port 8000 is free with `sudo ss -ltnp 'sport = :8000'`.
- [ ] **Step 3: Store the database setting.** Create `/etc/career-platform.env` with owner `root:azureuser` and mode `0640` using `sudo install -o root -g azureuser -m 0640 /dev/null /etc/career-platform.env`, then edit it with `sudoedit`. Set `DATABASE_URL` to the app's existing local MySQL connection string; do not put the password in shell history or source control.
- [ ] **Step 4: Create the unit.** Write `/etc/systemd/system/career-platform.service`:

  ```ini
  [Unit]
  Description=Career Platform resume website
  Wants=network-online.target
  After=network-online.target mysql.service

  [Service]
  Type=simple
  User=azureuser
  Group=azureuser
  WorkingDirectory=/home/azureuser/career-platform
  EnvironmentFile=/etc/career-platform.env
  ExecStart=/home/azureuser/career-platform/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
  Restart=on-failure
  RestartSec=5

  [Install]
  WantedBy=multi-user.target
  ```

- [ ] **Step 5: Enable and start the service.** Run `sudo systemctl daemon-reload` and `sudo systemctl enable --now career-platform`.
- [ ] **Step 6: Verify the service without restart/crash testing.** Confirm it is active with `sudo systemctl is-active career-platform` and check `sudo systemctl status career-platform --no-pager`. Verify `User=azureuser` and `WorkingDirectory=/home/azureuser/career-platform` with `sudo systemctl show career-platform -p User -p WorkingDirectory`. Confirm `sudo ss -ltnp 'sport = :8000'` shows Uvicorn listening only on `127.0.0.1:8000`. Check the local app response with `curl -fsS http://127.0.0.1:8000/ >/dev/null`. Do not kill the service or run restart/crash tests; those are reserved for the owner later.

**Undo:** Run `sudo systemctl disable --now career-platform`, then `sudo rm /etc/systemd/system/career-platform.service`, `sudo systemctl daemon-reload`, and remove `/etc/career-platform.env` only if this rollout created it and no other service uses it. Restore any backed-up pre-existing files. The app directory and virtual environment remain untouched; the prior manual Uvicorn command can be used again.

**Actual results (reported by VM owner):**
- [x] `career-platform` is enabled and active.
- [x] Uvicorn listens only on `127.0.0.1:8000`.
- [x] The local HTTP check succeeded (`LOCAL SITE OK`).
- [x] MySQL is active.
- [x] No restart/crash tests were run.
- [x] No Azure or firewall changes were made.

## Task 2: Put Nginx on Port 80

**Files / VM configuration:**
- Create: `/etc/nginx/sites-available/career-platform`
- Enable: `/etc/nginx/sites-enabled/career-platform`

- [ ] **Step 1: Install or confirm Nginx.** Check whether Nginx is already installed; if not, run `sudo apt-get update && sudo apt-get install -y nginx`. Check existing enabled sites before configuring the new site.
- [ ] **Step 2: Configure the reverse proxy.** Create `/etc/nginx/sites-available/career-platform` with:

  ```nginx
  server {
      listen 80;
      server_name 9.205.30.229;

      location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  ```

- [ ] **Step 3: Disable the default site if enabled.** Check whether `/etc/nginx/sites-enabled/default` exists or is a symlink. If present, disable it with `sudo rm -f /etc/nginx/sites-enabled/default`. Do this before validating or reloading Nginx, and record whether the default site was enabled so it can be restored if rolling back.
- [ ] **Step 4: Enable and validate the career-platform site.** Create the symlink `sudo ln -s /etc/nginx/sites-available/career-platform /etc/nginx/sites-enabled/career-platform`. Run `sudo nginx -t`; only if it succeeds, run `sudo systemctl enable --now nginx` and `sudo systemctl reload nginx`.
- [ ] **Step 5: Verify locally.** Check `sudo systemctl is-active nginx`, `sudo nginx -t`, `sudo ss -ltnp '( sport = :80 or sport = :8000 )'`, and `curl -i -H 'Host: 9.205.30.229' http://127.0.0.1/`. The app response should arrive through Nginx on port 80; port 8000 must remain bound only to loopback.

**Undo:** Remove only the `career-platform` symlink and its site file. If the default site was enabled before this task, restore its symlink with `sudo ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default`. Then run `sudo nginx -t` and `sudo systemctl reload nginx`. Keep Nginx and any other pre-existing sites/configuration unless they were installed solely for this rollout and are not otherwise used. Do not change firewall rules as part of rollback.

**Actual results (reported by VM owner):**
- [x] `nginx -t` passed and Nginx is active.
- [x] Nginx listens on `0.0.0.0:80`.
- [x] Uvicorn remains bound only to `127.0.0.1:8000`; port 8000 was not opened publicly.
- [x] A normal GET through Nginx returned the resume page and contained `Nikhil Mandyam`.
- [x] `curl -I` returned HTTP 405 because the application allows GET but not HEAD; the successful GET verified the site.
- [x] No Azure or firewall changes were made.

## Task 3: Verify Public Access and Network Boundaries

- [ ] **Step 1: Confirm the owner-managed Azure rule.** In Azure, the VM owner verifies the Allow-HTTP-80 inbound rule is at priority 320. Do not create, edit, or delete Azure resources or rules as part of these steps. Confirm there is no effective inbound allow for TCP 8000.
- [ ] **Step 2: Test from outside the VM.** From a separate network/client, run `curl -fsS http://9.205.30.229/` and confirm the resume page includes the expected resume content without requiring a port number. Use GET (not `curl -I`/HEAD), since the app does not support HEAD requests. If checking a static asset, use `curl -fsS http://9.205.30.229/static/style.css >/dev/null`.
- [ ] **Step 3: Recheck service and port exposure.** On the VM, confirm `career-platform` and Nginx are active, review recent service logs with `sudo journalctl -u career-platform -n 50 --no-pager`, and verify `ss` still shows Uvicorn only on `127.0.0.1:8000`. From outside, confirm TCP 8000 is unreachable; do not treat a public port-8000 success as acceptable.

**Undo:** This section changes no configuration. If public verification fails, use the local curl, `nginx -t`, service status, and journal output to identify which prior section needs rollback. Keep Azure changes with the VM owner; never open port 8000 to troubleshoot.

**Actual results (reported by VM owner):**
- [x] Azure Allow-HTTP-80 exists at priority 320.
- [x] `http://9.205.30.229` loads the Nikhil Mandyam resume publicly; an external GET confirmed the page contains `Nikhil Mandyam`.
- [x] Nginx is serving public traffic on port 80.
- [x] Uvicorn remains private on `127.0.0.1:8000`.
- [x] TCP port 8000 is not publicly reachable; the external connection timed out.

## Instructor Manual Reliability Checks

**Actual results (reported by VM owner):**
- [x] **Azure VM restart test:** PASS. After reboot, MySQL, `career-platform`, and Nginx returned active, and the public resume site loaded.
- [x] **Single Uvicorn worker failure test:** PASS. Worker PID `1000` was killed; the site remained available and Uvicorn created replacement worker PID `1225`.
- [x] **Main Uvicorn process crash test:** PASS. MainPID `995` was terminated with SIGKILL; systemd restarted the service with MainPID `1241`, `NRestarts=1`, and the local site check returned `SITE RECOVERED`.
- [x] **Service stop/recovery test:** PASS. Stopping `career-platform` caused Nginx to return HTTP 502; starting `career-platform` restored HTTP 200, and the service is active again.

## Completion Criteria

- `http://9.205.30.229/` serves the resume site through Nginx on port 80.
- Uvicorn runs as `azureuser` with 2 workers, managed by the enabled `career-platform` systemd service with failure restart enabled.
- Uvicorn listens only on `127.0.0.1:8000`; do not add any inbound rule for port 8000.
- The local MySQL configuration remains private, and no application source files or tests were changed.
