"""Tests for bench utilities including site health checks."""

import json
import tempfile
from pathlib import Path

import pytest

from realtimex_frappe.config.schema import RealtimexConfig
from realtimex_frappe.utils.bench import site_is_healthy


class TestSiteIsHealthy:
    """Tests for site_is_healthy() function."""

    def test_healthy_site(self):
        """Test detection of a properly configured site."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bench_path = Path(tmpdir)
            site_name = "test.localhost"
            site_path = bench_path / "sites" / site_name
            site_path.mkdir(parents=True)

            # Create valid site_config.json
            config_file = site_path / "site_config.json"
            config_file.write_text(json.dumps({
                "db_name": "test_db",
                "db_password": "secret",
                "db_type": "postgres"
            }))

            config = RealtimexConfig()
            config = config.with_overrides(
                site_name=site_name,
                bench_path=str(bench_path)
            )

            healthy, reason = site_is_healthy(config)
            assert healthy is True
            assert reason == "healthy"

    def test_site_not_found(self):
        """Test detection when site directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RealtimexConfig()
            config = config.with_overrides(
                site_name="nonexistent.localhost",
                bench_path=tmpdir
            )

            healthy, reason = site_is_healthy(config)
            assert healthy is False
            assert reason == "not_found"

    def test_missing_site_config(self):
        """Test detection when site_config.json is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bench_path = Path(tmpdir)
            site_name = "partial.localhost"
            site_path = bench_path / "sites" / site_name
            site_path.mkdir(parents=True)

            # No site_config.json created

            config = RealtimexConfig()
            config = config.with_overrides(
                site_name=site_name,
                bench_path=str(bench_path)
            )

            healthy, reason = site_is_healthy(config)
            assert healthy is False
            assert reason == "missing_config"

    def test_invalid_json_config(self):
        """Test detection when site_config.json is corrupted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bench_path = Path(tmpdir)
            site_name = "corrupt.localhost"
            site_path = bench_path / "sites" / site_name
            site_path.mkdir(parents=True)

            # Create invalid JSON
            config_file = site_path / "site_config.json"
            config_file.write_text("{ this is not valid json }")

            config = RealtimexConfig()
            config = config.with_overrides(
                site_name=site_name,
                bench_path=str(bench_path)
            )

            healthy, reason = site_is_healthy(config)
            assert healthy is False
            assert reason == "invalid_config"

    def test_incomplete_config_missing_db_name(self):
        """Test detection when db_name is missing from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bench_path = Path(tmpdir)
            site_name = "incomplete.localhost"
            site_path = bench_path / "sites" / site_name
            site_path.mkdir(parents=True)

            # Create config without db_name
            config_file = site_path / "site_config.json"
            config_file.write_text(json.dumps({
                "db_type": "postgres"
            }))

            config = RealtimexConfig()
            config = config.with_overrides(
                site_name=site_name,
                bench_path=str(bench_path)
            )

            healthy, reason = site_is_healthy(config)
            assert healthy is False
            assert reason == "incomplete_config"

    def test_no_site_name(self):
        """Test when site name is not configured."""
        config = RealtimexConfig()

        healthy, reason = site_is_healthy(config)
        assert healthy is False
        assert reason == "not_found"
