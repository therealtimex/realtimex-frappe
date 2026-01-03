# Realtimex Frappe

Run Frappe/ERPNext with PostgreSQL, schema-based isolation, and external Redis.

---

## Quick Start

You have a PostgreSQL database ready. Here's what to do:

### Step 1: Admin Setup (Once)

Run this **once** on any machine to initialize the database and install apps:

**RealTimeX Local App JSON:**
```json
{
  "command": "uvx",
  "args": ["realtimex-frappe", "setup"],
  "env": {
    "REALTIMEX_MODE": "admin",
    "REALTIMEX_SITE_NAME": "mysite.localhost",
    "REALTIMEX_SITE_PASSWORD": "admin",
    "REALTIMEX_DB_HOST": "db.xxxx.supabase.co",
    "REALTIMEX_DB_PORT": "5432",
    "REALTIMEX_DB_NAME": "postgres",
    "REALTIMEX_DB_SCHEMA": "mysite_schema",
    "REALTIMEX_DB_USER": "mysite_schema",
    "REALTIMEX_DB_PASSWORD": "your_site_password",
    "REALTIMEX_ADMIN_DB_USER": "postgres",
    "REALTIMEX_ADMIN_DB_PASSWORD": "your_admin_password"
  },
  "port": 8000
}
```

**Or via command line:**
```bash
export REALTIMEX_MODE=admin
export REALTIMEX_SITE_NAME=mysite.localhost
export REALTIMEX_SITE_PASSWORD=admin
export REALTIMEX_DB_HOST=db.xxxx.supabase.co
export REALTIMEX_DB_PORT=5432
export REALTIMEX_DB_NAME=postgres
export REALTIMEX_DB_SCHEMA=mysite_schema
export REALTIMEX_DB_USER=mysite_schema
export REALTIMEX_DB_PASSWORD=your_site_password
export REALTIMEX_ADMIN_DB_USER=postgres
export REALTIMEX_ADMIN_DB_PASSWORD=your_admin_password

realtimex-frappe setup
```

**What happens:**
1. Creates the schema `mysite_schema` in your PostgreSQL database
2. Creates a database user `mysite_schema` (same name as schema)
3. Installs Frappe and ERPNext
4. **Outputs credentials to share with your team**

### Step 2: User Mode (Run Anywhere)

Use the credentials output from admin setup to run on any machine:

**RealTimeX Local App JSON** (use values from admin setup output):
```json
{
  "command": "uvx",
  "args": ["realtimex-frappe", "run"],
  "env": {
    "REALTIMEX_MODE": "user",
    "REALTIMEX_SITE_NAME": "mysite.localhost",
    "REALTIMEX_DB_HOST": "db.xxxx.supabase.co",
    "REALTIMEX_DB_PORT": "5432",
    "REALTIMEX_DB_NAME": "postgres",
    "REALTIMEX_DB_SCHEMA": "mysite_schema",
    "REALTIMEX_DB_USER": "mysite_schema",
    "REALTIMEX_DB_PASSWORD": "your_site_password"
  },
  "port": 8000
}
```

**Or via command line** (use values from admin setup output):
```bash
export REALTIMEX_MODE=user
export REALTIMEX_SITE_NAME=mysite.localhost
export REALTIMEX_DB_HOST=db.xxxx.supabase.co
export REALTIMEX_DB_PORT=5432
export REALTIMEX_DB_NAME=postgres
export REALTIMEX_DB_SCHEMA=mysite_schema
export REALTIMEX_DB_USER=mysite_schema
export REALTIMEX_DB_PASSWORD=your_site_password

realtimex-frappe run
```

**What happens:**
1. Downloads apps locally (if not already present)
2. Creates local site configuration pointing to remote database
3. Starts the Frappe server

**Result:** Your site is available at **http://mysite.localhost:8000**

---

## Understanding the Two Modes

| | Admin Mode | User Mode |
|---|---|---|
| **Purpose** | Initialize database and install apps | Run the server |
| **Command** | `realtimex-frappe setup` | `realtimex-frappe run` |
| **When** | Once, by the project admin | Anytime, by any team member |
| **Requires** | Admin database credentials | Shared credentials from admin |
| **Creates** | Schema, tables, initial data | Local config only |

**Workflow:**
1. Admin runs `setup` once → creates database schema and installs apps
2. Admin shares the output credentials with team
3. Team members copy those credentials and run `run`

---

## Environment Variables

### Required for Both Modes

| Variable | Description |
|----------|-------------|
| `REALTIMEX_MODE` | `admin` or `user` |
| `REALTIMEX_SITE_NAME` | Site name (e.g., `mysite.localhost`) |
| `REALTIMEX_DB_HOST` | PostgreSQL host |
| `REALTIMEX_DB_PORT` | PostgreSQL port (default: `5432`) |
| `REALTIMEX_DB_NAME` | Database name (e.g., `postgres` for Supabase) |
| `REALTIMEX_DB_SCHEMA` | Schema name (e.g., `mysite_schema`) |
| `REALTIMEX_DB_USER` | Site database user (created by admin setup) |
| `REALTIMEX_DB_PASSWORD` | Site database password |

### Required for Admin Mode Only

| Variable | Description |
|----------|-------------|
| `REALTIMEX_SITE_PASSWORD` | Frappe administrator password |
| `REALTIMEX_ADMIN_DB_USER` | Root database user (e.g., `postgres`) |
| `REALTIMEX_ADMIN_DB_PASSWORD` | Root database password |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `REALTIMEX_PORT` | `8000` | Webserver port |
| `REALTIMEX_REDIS_HOST` | `127.0.0.1` | Redis host |
| `REALTIMEX_REDIS_CACHE_PORT` | `13001` | Redis cache port |
| `REALTIMEX_REDIS_QUEUE_PORT` | `11001` | Redis queue port |
| `REALTIMEX_BENCH_PATH` | `~/.realtimex.ai/storage/local-apps/frappe-bench` | Installation path |
| `REALTIMEX_FORCE_REINSTALL` | `false` | Delete and reinstall (for recovery) |

Run `realtimex-frappe env-help` for the complete list.

---

## Commands

| Command | Description |
|---------|-------------|
| `setup` | Admin mode: create database, install apps, output credentials |
| `run` | User mode: start the server (auto-setup local config if needed) |
| `env-help` | Show all environment variables |
| `validate` | Check if prerequisites are installed |

---

## Prerequisites

### macOS

| Prerequisite | Check | Install |
|--------------|-------|---------|
| Git | `git --version` | `brew install git` |
| Node.js 18+ | `node --version` | `brew install node@18` |
| npm | `npm --version` | (included with Node.js) |
| pkg-config | `which pkg-config` | `brew install pkg-config` |
| Redis | `which redis-server` | `brew install redis && brew services start redis` |

**wkhtmltopdf (macOS):**
```bash
curl -L https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-2/wkhtmltox-0.12.6-2.macos-cocoa.pkg -O
sudo installer -pkg wkhtmltox-0.12.6-2.macos-cocoa.pkg -target /
```

### Linux

```bash
# System dependencies
sudo apt update && sudo apt install git pkg-config curl

# Redis
sudo apt install redis-server && sudo systemctl enable --now redis-server

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# wkhtmltopdf and dependencies
sudo apt install xvfb libfontconfig wkhtmltopdf
```

---

## Storage

All data is stored at:
```
~/.realtimex.ai/storage/local-apps/frappe-bench/
```

This persists across restarts and is independent of your working directory.

---

## Security Model

Schema-based isolation provides security boundaries:

| What the site user CAN do | What the site user CANNOT do |
|---------------------------|------------------------------|
| All operations within their schema | Access other schemas |
| CREATE/ALTER/DROP tables in schema | DROP the schema itself |
| Run migrations, install apps | Create new schemas |

The admin user (`postgres`) owns the schema; the site user operates within it.

---

## License

MIT
