# Realtimex Frappe

A **uvx**-compatible CLI tool to streamline Frappe/ERPNext site setup with PostgreSQL (including Supabase-hosted) support, external Redis, custom Node.js/wkhtmltopdf binaries, and configurable app sources.

**Target platforms:** macOS, Linux

## Features

- 🚀 Single command to create a fully configured Frappe site with ERPNext
- 🔧 Configure bundled Node.js and wkhtmltopdf binaries (for desktop app integration)
- 🗄️ PostgreSQL support (including Supabase-hosted databases)
- 📦 Support for forked/custom app repositories
- 🔴 External Redis configuration
- 📋 JSON-based configuration for reproducible setups

## Installation

```bash
# Using uvx (recommended)
uvx realtimex-frappe --help

# Or install with pip
pip install realtimex-frappe
```

## Quick Start

### 1. Generate a configuration file

```bash
realtimex-frappe init-config -o ./my-config.json
```

### 2. Edit the configuration

```json
{
  "frappe": {
    "branch": "version-15",
    "repo": "https://github.com/frappe/frappe.git"
  },
  "apps": [
    {
      "name": "erpnext",
      "url": "https://github.com/frappe/erpnext.git",
      "branch": "version-15",
      "install": true
    }
  ],
  "binaries": {
    "node": {
      "bin_dir": "/path/to/bundled/node/bin"
    },
    "wkhtmltopdf": {
      "bin_dir": "/path/to/bundled/wkhtmltopdf/bin"
    }
  },
  "redis": {
    "host": "127.0.0.1",
    "port": 6379
  },
  "database": {
    "type": "postgres",
    "host": "localhost",
    "port": 5432
  }
}
```

### 3. Validate your setup

```bash
realtimex-frappe validate --config ./my-config.json
```

### 4. Create a new site

```bash
realtimex-frappe new-site --config ./my-config.json
```

## Commands

| Command | Description |
|---------|-------------|
| `init-config` | Generate a default configuration file |
| `validate` | Validate configuration and check for required binaries |
| `new-site` | Create a new Frappe site with ERPNext |

## Configuration Reference

See [config/default.json](./config/default.json) for the full configuration schema.

## Requirements

- Python 3.11+
- Node.js 18+ (can be bundled)
- Redis (external, running on port 6379)
- PostgreSQL or Supabase
- wkhtmltopdf (can be bundled)

## License

MIT
