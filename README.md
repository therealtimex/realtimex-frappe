# Realtimex Frappe

A CLI tool to set up Frappe/ERPNext sites with PostgreSQL, external Redis, and bundled binaries.

**Platforms:** macOS, Linux

---

## 🚀 Quick Setup for RealTimeX Local App

> [!IMPORTANT]
> **Follow this section to run Frappe inside the RealTimeX Local App environment.**

### Step 1: Install Prerequisites

| Prerequisite | Check Command | macOS Install |
|--------------|---------------|---------------|
| **Git** | `git --version` | `xcode-select --install` |
| **Node.js 18+** | `node --version` | `brew install node@18` or bundled |
| **pkg-config** | `which pkg-config` | `xcode-select --install` |
| **wkhtmltopdf** | `wkhtmltopdf --version` | See below |
| **Redis** | `redis-cli ping` | `brew install redis && brew services start redis` |

**wkhtmltopdf (macOS):**
```bash
curl -L https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-2/wkhtmltox-0.12.6-2.macos-cocoa.pkg -O
installer -pkg wkhtmltox-0.12.6-2.macos-cocoa.pkg -target ~
# If permission denied, use: sudo installer -pkg wkhtmltox-0.12.6-2.macos-cocoa.pkg -target /
```

> [!TIP]
> **Using a remote database?** Skip PostgreSQL installation and configure `REALTIMEX_DB_HOST` to point to your remote server (e.g., Supabase).

**For local PostgreSQL:**
```bash
brew install postgresql@15 && brew services start postgresql@15
```

### Step 2: Configure RealTimeX App

Add this to your RealTimeX Local App configuration:

```json
{
  "command": "uvx",
  "args": ["realtimex-frappe", "run"],
  "env": {
    "REALTIMEX_SITE_NAME": "mysite.localhost",
    "REALTIMEX_ADMIN_PASSWORD": "admin",
    "REALTIMEX_DB_NAME": "frappe_mysite",
    "REALTIMEX_DB_USER": "postgres",
    "REALTIMEX_DB_PASSWORD": "postgres"
  },
  "working_dir": "",
  "port": 8000
}
```

**For Supabase (schema-based isolation):**
```json
{
  "command": "uvx",
  "args": ["realtimex-frappe", "run"],
  "env": {
    "REALTIMEX_SITE_NAME": "mysite.localhost",
    "REALTIMEX_ADMIN_PASSWORD": "admin",
    "REALTIMEX_DB_NAME": "postgres",
    "REALTIMEX_DB_USER": "postgres.xxxx",
    "REALTIMEX_DB_PASSWORD": "your-password",
    "REALTIMEX_DB_HOST": "db.xxxx.supabase.co",
    "REALTIMEX_DB_PORT": "5432",
    "REALTIMEX_DB_SCHEMA": "frappe_mysite"
  },
  "working_dir": "",
  "port": 8000
}
```

### Step 3: Run

**Option A: Via RealTimeX App**

Simply start the app through the RealTimeX interface. The JSON configuration above handles all environment variables automatically.

**Option B: Direct Command Line**

Set environment variables and run manually:

```bash
export REALTIMEX_SITE_NAME=mysite.localhost
export REALTIMEX_ADMIN_PASSWORD=admin
export REALTIMEX_DB_NAME=frappe_mysite
export REALTIMEX_DB_USER=postgres
export REALTIMEX_DB_PASSWORD=postgres

# For remote database, also set:
# export REALTIMEX_DB_HOST=db.xxxx.supabase.co

uvx realtimex-frappe run
```

---

**Result:** Your site will be available at **http://mysite.localhost:8000**

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REALTIMEX_SITE_NAME` | ✅ | - | Site name (e.g., `mysite.localhost`) |
| `REALTIMEX_ADMIN_PASSWORD` | ✅ | - | Admin password |
| `REALTIMEX_DB_NAME` | ✅ | - | Database name to create or connect to |
| `REALTIMEX_DB_USER` | ✅ | - | PostgreSQL username (root credentials for setup) |
| `REALTIMEX_DB_PASSWORD` | ✅ | - | PostgreSQL password |
| `REALTIMEX_DB_SCHEMA` | - | - | PostgreSQL schema name (enables schema mode) |
| `REALTIMEX_NODE_BIN_DIR` | ⚠️ | - | Path to Node.js bin directory |
| `REALTIMEX_DB_HOST` | - | `localhost` | PostgreSQL host |
| `REALTIMEX_DB_PORT` | - | `5432` | PostgreSQL port |
| `REALTIMEX_REDIS_HOST` | - | `127.0.0.1` | Redis host |
| `REALTIMEX_BENCH_PATH` | - | `~/.realtimex.ai/storage/local-apps/frappe-bench` | Bench installation path |

Run `realtimex-frappe env-help` for the complete list.

---

## ⚠️ Database Configuration

### Traditional Mode (Default)

When `REALTIMEX_DB_SCHEMA` is **not set**, Frappe creates a new database:

```bash
# ✅ Creates database "frappe_mysite" owned by user "frappe_mysite"
REALTIMEX_DB_NAME="frappe_mysite"
REALTIMEX_DB_USER="postgres"        # Root user for setup
REALTIMEX_DB_PASSWORD="postgres"
```

> [!CAUTION]
> **`REALTIMEX_DB_NAME` controls which database Frappe will CREATE.** Use unique names.
> **Never use `REALTIMEX_DB_NAME="postgres"` without `REALTIMEX_DB_SCHEMA` otherwise Frappe will drop the `postgres` database.**

### Schema Mode (For Supabase)

When `REALTIMEX_DB_SCHEMA` is **set**, Frappe creates a schema within an existing database:

```bash
# ✅ Creates schema "frappe_mysite" in the "postgres" database
REALTIMEX_DB_NAME="postgres"        # Existing database (Supabase default)
REALTIMEX_DB_USER="postgres.xxxx"   # Your Supabase user
REALTIMEX_DB_PASSWORD="your-password"
REALTIMEX_DB_SCHEMA="frappe_mysite" # Schema to create
```

**Schema mode behavior:**
- Creates user named after `db_schema` (e.g., `frappe_mysite`)
- Creates schema owned by this user
- Grants Supabase roles (`anon`, `authenticated`, `service_role`) if they exist
- Sets `search_path` automatically on all connections

> [!TIP]
> Schema mode is ideal for Supabase because it uses the existing `postgres` database and enables Supabase features like Realtime and Edge Functions.

---

## Storage Location

Bench data is stored persistently at:

```
~/.realtimex.ai/storage/local-apps/frappe-bench/
```

This location persists across restarts and is independent of the working directory.

---

## Linux Setup

```bash
# System dependencies
sudo apt update && sudo apt install git pkg-config curl

# Redis
sudo apt install redis-server && sudo systemctl enable --now redis-server

# PostgreSQL (skip if using remote database)
sudo apt install postgresql postgresql-contrib && sudo systemctl enable --now postgresql

# wkhtmltopdf dependencies
sudo apt install xvfb libfontconfig

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs
```

---

## Commands

| Command | Description |
|---------|-------------|
| `run` | Setup and start (production) |
| `env-help` | Show environment variables |
| `validate` | Check prerequisites |

---

## Requirements

- Python 3.11+
- Node.js 18+
- Redis 6+
- PostgreSQL 13+ (local or remote)
- Git, pkg-config, wkhtmltopdf

---

## License

MIT
