# Realtimex Frappe

A **uvx**-compatible CLI tool to streamline Frappe/ERPNext site setup with PostgreSQL (including Supabase-hosted) support, external Redis, and bundled binaries.

**Target platforms:** macOS, Linux

## Features

- 🚀 Single command to create and start a Frappe site with ERPNext
- 🔧 Configure bundled Node.js binaries
- 🗄️ PostgreSQL support (including Supabase-hosted databases)
- 📦 Support for forked/custom app repositories
- 🔴 External Redis configuration
- ✅ Automatic prerequisite validation
- 📁 Persistent bench storage in `~/.realtimex.ai/storage/local-apps/frappe-bench`

## System Prerequisites

Before running, ensure these are installed on your system:

### macOS

```bash
# Install Xcode command line tools (provides git, pkg-config)
xcode-select --install

# Install wkhtmltopdf (choose one method)
# Method 1: Using Homebrew
brew install wkhtmltopdf

# Method 2: Download from GitHub releases
# https://github.com/wkhtmltopdf/packaging/releases
```

### Linux (Debian/Ubuntu)

```bash
# Install git and pkg-config
sudo apt install git pkg-config

# Install wkhtmltopdf dependencies
sudo apt install xvfb libfontconfig

# Download and install wkhtmltopdf
# Get the .deb file from: https://wkhtmltopdf.org/downloads.html
sudo dpkg -i wkhtmltox_*.deb
```

### Prerequisites Summary

| Prerequisite | Description | macOS | Linux |
|--------------|-------------|-------|-------|
| `git` | Version control | `xcode-select --install` | `sudo apt install git` |
| `pkg-config` | Build tool | `xcode-select --install` | `sudo apt install pkg-config` |
| `wkhtmltopdf` | PDF generation | `brew install wkhtmltopdf` | Download from wkhtmltopdf.org |

## Quick Start (Production)

Set environment variables and run:

```bash
REALTIMEX_SITE_NAME=mysite.localhost \
REALTIMEX_ADMIN_PASSWORD=secret \
REALTIMEX_DB_NAME=mysite \
REALTIMEX_DB_USER=postgres \
REALTIMEX_DB_PASSWORD=postgres \
uvx realtimex-frappe run
```

This single command will:
1. ✅ Validate system prerequisites (git, pkg-config, wkhtmltopdf)
2. ✅ Validate bundled binaries (node, npm)
3. ✅ Initialize bench at `~/.realtimex.ai/storage/local-apps/frappe-bench` (if needed)
4. ✅ Create the site (if needed)
5. ✅ Install ERPNext
6. ✅ Start the server

## Environment Variables

Run `realtimex-frappe env-help` for full list.

**Required:**
- `REALTIMEX_SITE_NAME` - Site name (e.g., `mysite.localhost`)
- `REALTIMEX_ADMIN_PASSWORD` - Administrator password
- `REALTIMEX_DB_NAME` - PostgreSQL database name
- `REALTIMEX_DB_USER` - PostgreSQL username
- `REALTIMEX_DB_PASSWORD` - PostgreSQL password

**Optional:**
- `REALTIMEX_NODE_BIN_DIR` - Path to bundled Node.js bin directory
- `REALTIMEX_DB_HOST` - PostgreSQL host (default: `localhost`)
- `REALTIMEX_REDIS_HOST` - Redis host (default: `127.0.0.1`)
- `REALTIMEX_BENCH_PATH` - Bench installation path (default: `~/.realtimex.ai/storage/local-apps/frappe-bench`)

## ⚠️ Database Name Configuration

> [!CAUTION]
> **Danger: The `REALTIMEX_DB_NAME` setting directly controls which database Frappe will CREATE and use.**

### Important Recommendations:

1. **Always use a dedicated database** - Do not use shared database names like `postgres` or your production databases.

2. **Auto-generated names recommended** - For automated deployments, consider generating unique database names (e.g., `frappe_mysite_abc123`) to avoid conflicts.

3. **Never reuse database names** - Reinitializing with an existing database name may cause data loss if `--force` is used.

4. **PostgreSQL root credentials** - The `REALTIMEX_DB_USER` and `REALTIMEX_DB_PASSWORD` are used as **root credentials** to create the database and application user. Ensure they have sufficient privileges.

### Example: Safe Database Naming

```bash
# Good: Unique, dedicated database name
REALTIMEX_DB_NAME="frappe_mysite_$(date +%s)"

# Bad: Generic names that may conflict
REALTIMEX_DB_NAME="postgres"      # Don't use!
REALTIMEX_DB_NAME="production"    # Too generic!
```

## Commands

| Command | Mode | Description |
|---------|------|-------------|
| `run` | **Production** | Setup + start in one command |
| `env-help` | Helper | Show all environment variables |
| `new-site` | Developer | Interactive site creation |
| `init-config` | Developer | Generate default config JSON |
| `validate` | Developer | Check config and binaries |

## Developer Mode

For development, use config files and interactive prompts:

```bash
# Generate config
realtimex-frappe init-config -o ./my-config.json

# Validate
realtimex-frappe validate --config ./my-config.json

# Create site
realtimex-frappe new-site --config ./my-config.json
```

## Storage Location

By default, all bench data is stored in a persistent location:

```
~/.realtimex.ai/
└── storage/
    └── local-apps/              # Parent for multiple local applications
        └── frappe-bench/        # The Frappe bench lives here
            ├── apps/
            ├── sites/
            └── ...
```

This ensures your bench persists across terminal sessions and is not affected by the current working directory.

## Requirements

- Python 3.11+
- Node.js 18+ (can be bundled via `REALTIMEX_NODE_BIN_DIR`)
- Redis (external, running on port 6379)
- PostgreSQL

## License

MIT
