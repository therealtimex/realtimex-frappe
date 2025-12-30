"""Tests for configuration schema and loader."""

import json
import tempfile
from pathlib import Path

import pytest

from realtimex_frappe.config.loader import (
    get_default_config,
    load_config,
    merge_config_with_cli,
    write_default_config,
)
from realtimex_frappe.config.schema import (
    AppConfig,
    DatabaseConfig,
    RealtimexConfig,
    RedisConfig,
)


class TestRealtimexConfig:
    """Tests for RealtimexConfig model."""

    def test_default_config(self):
        """Test that default config is valid."""
        config = RealtimexConfig()

        assert config.version == "1.0.0"
        assert config.frappe.branch == "realtimex/v15.93.0"
        assert config.database.type == "postgres"
        assert config.redis.port == 6379

    def test_redis_url_property(self):
        """Test Redis URL generation."""
        redis = RedisConfig(host="localhost", port=6379)
        assert redis.url == "redis://localhost:6379"

        redis = RedisConfig(host="192.168.1.100", port=6380)
        assert redis.url == "redis://192.168.1.100:6380"

    def test_database_validation(self):
        """Test database port validation."""
        # Valid port
        db = DatabaseConfig(port=5432)
        assert db.port == 5432

        # Invalid port
        with pytest.raises(ValueError):
            DatabaseConfig(port=0)

        with pytest.raises(ValueError):
            DatabaseConfig(port=70000)

    def test_supabase_host(self):
        """Test that Supabase hosts are accepted."""
        db = DatabaseConfig(host="db.abcdef.supabase.co")
        assert db.host == "db.abcdef.supabase.co"

    def test_with_overrides(self):
        """Test configuration override."""
        config = RealtimexConfig()

        overridden = config.with_overrides(
            site_name="mysite.localhost",
            admin_password="secret123",
            db_host="db.supabase.co",
            db_port=6543,
        )

        assert overridden.site.name == "mysite.localhost"
        assert overridden.site.admin_password == "secret123"
        assert overridden.database.host == "db.supabase.co"
        assert overridden.database.port == 6543

        # Original should be unchanged
        assert config.site.name is None


class TestConfigLoader:
    """Tests for configuration loading and saving."""

    def test_write_and_load_config(self):
        """Test writing and loading a config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test-config.json"

            # Write default config
            write_default_config(config_path)

            # Verify file exists
            assert config_path.exists()

            # Load it back
            loaded = load_config(config_path)

            # Should use RealTimeX repos from bundled config
            assert "realtimex" in loaded.frappe.branch
            assert len(loaded.apps) == 1
            assert loaded.apps[0].name == "erpnext"

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.json")

    def test_get_default_config(self):
        """Test getting default config."""
        config = get_default_config()

        # Should use RealTimeX repos from bundled config
        assert "realtimex" in config.frappe.branch
        assert len(config.apps) == 1
        assert config.apps[0].name == "erpnext"

    def test_merge_config_with_cli(self):
        """Test merging config file with CLI options."""
        base = RealtimexConfig()

        merged = merge_config_with_cli(
            base,
            site_name="test.localhost",
            db_name="testdb",
        )

        assert merged.site.name == "test.localhost"
        assert merged.database.name == "testdb"

        # Other values should be defaults
        assert merged.frappe.branch == "realtimex/v15.93.0"

    def test_merge_with_none_config(self):
        """Test merging when no config file is provided."""
        merged = merge_config_with_cli(
            None,
            site_name="test.localhost",
        )

        assert merged.site.name == "test.localhost"
        # Should use default config as base
        assert len(merged.apps) == 1
        assert merged.apps[0].name == "erpnext"


class TestAppConfig:
    """Tests for AppConfig model."""

    def test_app_config_defaults(self):
        """Test app config default values."""
        app = AppConfig(
            name="erpnext",
            url="https://github.com/frappe/erpnext.git",
        )

        assert app.branch == "version-15"
        assert app.install is True

    def test_forked_app(self):
        """Test configuration for a forked app."""
        app = AppConfig(
            name="erpnext",
            url="https://github.com/myorg/erpnext-fork.git",
            branch="custom-branch",
            install=True,
        )

        assert app.url == "https://github.com/myorg/erpnext-fork.git"
        assert app.branch == "custom-branch"


class TestBundledConfigLoading:
    """Tests for bundled config loading (uvx/pip installation support)."""

    def test_get_default_config_uses_realtimex_repos(self):
        """Verify bundled config uses RealTimeX forks, not upstream."""
        config = get_default_config()

        # Frappe should use RealTimeX fork
        assert "therealtimex" in config.frappe.repo
        assert config.frappe.repo == "https://github.com/therealtimex/frappe.git"
        assert "realtimex" in config.frappe.branch

        # ERPNext should use RealTimeX fork
        assert len(config.apps) >= 1
        erpnext_app = next(app for app in config.apps if app.name == "erpnext")
        assert "therealtimex" in erpnext_app.url
        assert erpnext_app.url == "https://github.com/therealtimex/erpnext.git"

    def test_get_default_config_works_from_any_directory(self):
        """Ensure config loading works regardless of current working directory.

        This reproduces the uvx failure where running from an arbitrary
        directory caused the config file to not be found.
        """
        import os
        import tempfile

        original_cwd = os.getcwd()

        try:
            # Change to a completely unrelated directory
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)

                # This should still work and return RealTimeX repos
                config = get_default_config()

                assert "therealtimex" in config.frappe.repo
                assert len(config.apps) >= 1
        finally:
            os.chdir(original_cwd)

    def test_bundled_config_not_using_upstream_fallback(self):
        """Ensure we're not hitting hardcoded upstream fallback."""
        config = get_default_config()

        # These would indicate we're using the old fallback
        assert config.frappe.repo != "https://github.com/frappe/frappe.git"
        for app in config.apps:
            if app.name == "erpnext":
                assert app.url != "https://github.com/frappe/erpnext.git"
                assert app.branch != "version-15"

