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
| **wkhtmltopdf** | `wkhtmltopdf --version` | `brew install wkhtmltopdf` |
| **Redis** | `redis-cli ping` | `brew install redis && brew services start redis` |

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
    "REALTIMEX_DB_PASSWORD": "postgres",
    "REALTIMEX_NODE_BIN_DIR": "/path/to/node/bin"
  },
  "working_dir": "",
  "port": 8000
}
```

**For remote database (e.g., Supabase):**
```json
{
  "command": "uvx",
  "args": ["realtimex-frappe", "run"],
  "env": {
    "REALTIMEX_SITE_NAME": "mysite.localhost",
    "REALTIMEX_ADMIN_PASSWORD": "admin",
    "REALTIMEX_DB_NAME": "frappe_prod",
    "REALTIMEX_DB_USER": "postgres.xxxx",
    "REALTIMEX_DB_PASSWORD": "your-password",
    "REALTIMEX_DB_HOST": "db.xxxx.supabase.co",
    "REALTIMEX_DB_PORT": "5432",
    "REALTIMEX_NODE_BIN_DIR": "/path/to/node/bin"
  },
  "working_dir": "",
  "port": 8000
}
```

### Step 3: Run

Start the app through RealTimeX, or run directly:

```bash
uvx realtimex-frappe run
```

Your site will be available at **http://mysite.localhost:8000**

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REALTIMEX_SITE_NAME` | ✅ | - | Site name (e.g., `mysite.localhost`) |
| `REALTIMEX_ADMIN_PASSWORD` | ✅ | - | Admin password |
| `REALTIMEX_DB_NAME` | ✅ | - | Database name |
| `REALTIMEX_DB_USER` | ✅ | - | PostgreSQL username (root credentials) |
| `REALTIMEX_DB_PASSWORD` | ✅ | - | PostgreSQL password |
| `REALTIMEX_NODE_BIN_DIR` | ⚠️ | - | Path to Node.js bin directory |
| `REALTIMEX_DB_HOST` | - | `localhost` | PostgreSQL host |
| `REALTIMEX_DB_PORT` | - | `5432` | PostgreSQL port |
| `REALTIMEX_REDIS_HOST` | - | `127.0.0.1` | Redis host |
| `REALTIMEX_BENCH_PATH` | - | `~/.realtimex.ai/.../frappe-bench` | Bench installation path |

Run `realtimex-frappe env-help` for the complete list.

---

## ⚠️ Database Configuration

> [!CAUTION]
> **`REALTIMEX_DB_NAME` controls which database Frappe will CREATE.** Use unique, dedicated names.

```bash
# ✅ Good: Unique database name
REALTIMEX_DB_NAME="frappe_mysite_001"

# ❌ Bad: Generic or shared names
REALTIMEX_DB_NAME="postgres"
```

**Notes:**
- `REALTIMEX_DB_USER` and `REALTIMEX_DB_PASSWORD` are used as **root credentials** to create the database
- For remote databases, ensure the user has `CREATE DATABASE` privileges

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

# wkhtmltopdf
sudo apt install xvfb libfontconfig
# Download from https://wkhtmltopdf.org/downloads.html
sudo dpkg -i wkhtmltox_*.deb

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
