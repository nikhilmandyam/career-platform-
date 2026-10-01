# Personal Resume Website

A small FastAPI site that renders resume content from `app/content.py` and
loads project cards from a local MySQL database. The resume page still renders
when MySQL is unavailable; only the Projects section shows a temporary
unavailable message.

## Run in GitHub Codespaces

### 1. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. Start local MySQL

If MySQL is not already installed in the Codespace:

```bash
sudo apt-get update
sudo apt-get install -y mysql-server
sudo service mysql start
```

Create a database and a local-only application account. Replace the example
password with a value of your choice:

```bash
sudo mysql
```

```sql
CREATE DATABASE resume;
CREATE USER 'resume_app'@'127.0.0.1' IDENTIFIED BY 'replace-this-password';
GRANT ALL PRIVILEGES ON resume.* TO 'resume_app'@'127.0.0.1';
FLUSH PRIVILEGES;
EXIT;
```

Configure the local connection string in the current terminal. Replace the
password; URL-encode any reserved characters in it.

```bash
export DATABASE_URL='mysql+pymysql://resume_app:replace-this-password@127.0.0.1:3306/resume'
```

Initialize the schema and import the projects from `data/projects.json`:

```bash
python scripts/init_db.py
```

Edit `app/content.py` to update your profile, summary, experience, education,
skills, certifications, leadership, and contact links. Add projects to
`data/projects.json` and rerun the initializer to upsert those stable IDs.

### 3. Run and test

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open forwarded port **8000** in Codespaces. Run the test suite with:

```bash
pytest -q
```

## Later move to an Azure Ubuntu VM

The app uses the same `DATABASE_URL` on both hosts. Install Python, MySQL, and
Nginx on the VM, then clone the repository and install dependencies in a
virtual environment:

```bash
sudo apt-get update
sudo apt-get install -y git python3-venv python3-pip mysql-server nginx
sudo adduser --system --group --home /opt/resume resume
sudo -u resume git clone <repository-url> /opt/resume/app
sudo -u resume python3 -m venv /opt/resume/app/.venv
sudo -u resume /opt/resume/app/.venv/bin/pip install -r /opt/resume/app/requirements.txt
```

Create a database and application account in MySQL as above, using a new
deployment password. Keep MySQL bound to localhost, do not allow inbound port
3306 through the VM firewall, and do not put credentials in the repository.
Store the connection string in a root-owned environment file:

```bash
sudo install -o root -g resume -m 640 /dev/null /etc/resume-site.env
sudoedit /etc/resume-site.env
```

Add this line to `/etc/resume-site.env`, replacing the password:

```text
DATABASE_URL=mysql+pymysql://resume_app:replace-this-password@127.0.0.1:3306/resume
```

Initialize the database with the protected environment file:

```bash
sudo -u resume /bin/bash -c 'set -a; . /etc/resume-site.env; set +a; cd /opt/resume/app; .venv/bin/python scripts/init_db.py'
```

Create `/etc/systemd/system/resume.service`:

```ini
[Unit]
Description=Personal resume website
After=network.target mysql.service

[Service]
User=resume
Group=resume
WorkingDirectory=/opt/resume/app
EnvironmentFile=/etc/resume-site.env
ExecStart=/opt/resume/app/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Start the app service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now resume
sudo systemctl status resume
```

Create `/etc/nginx/sites-available/resume`, replacing the server name:

```nginx
server {
    listen 80;
    server_name your-domain-or-vm-ip;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/resume /etc/nginx/sites-enabled/resume
sudo nginx -t
sudo systemctl reload nginx
```

For a public site, configure HTTPS and allow only the required web ports in the
VM firewall; keep MySQL private.
