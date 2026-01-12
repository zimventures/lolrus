"""
Tests for app utility functions.

These tests cover non-GUI utility methods that can be tested in isolation.
"""

from datetime import datetime
from unittest.mock import patch

from lolrus.s3_client import S3Object


class TestGetPreviewType:
    """Tests for preview type detection from file extensions."""

    def _create_mock_app(self):
        """Create a minimal mock app instance with _get_preview_type method."""
        # Import here to avoid DearPyGui initialization issues
        # We're testing the logic, not the GUI
        from lolrus.app import LolrusApp

        # Create a mock that has the _get_preview_type method
        # We patch out the __init__ to avoid GUI initialization
        with patch.object(LolrusApp, '__init__', lambda self: None):
            app = LolrusApp()
            return app

    def _create_obj(self, key: str) -> S3Object:
        """Create a test S3Object with the given key."""
        return S3Object(
            key=key,
            size=100,
            last_modified=datetime.now(),
            etag="test",
        )

    def test_text_files_python(self):
        """Test Python files are detected as text."""
        app = self._create_mock_app()
        obj = self._create_obj("scripts/main.py")
        assert app._get_preview_type(obj) == "text"

    def test_text_files_json(self):
        """Test JSON files are detected as text."""
        app = self._create_mock_app()
        obj = self._create_obj("config/settings.json")
        assert app._get_preview_type(obj) == "text"

    def test_text_files_markdown(self):
        """Test Markdown files are detected as text."""
        app = self._create_mock_app()
        obj = self._create_obj("docs/README.md")
        assert app._get_preview_type(obj) == "text"

    def test_text_files_yaml(self):
        """Test YAML files are detected as text."""
        app = self._create_mock_app()
        for ext in [".yaml", ".yml"]:
            obj = self._create_obj(f"config/app{ext}")
            assert app._get_preview_type(obj) == "text"

    def test_text_files_web(self):
        """Test web files are detected as text."""
        app = self._create_mock_app()
        for ext in [".html", ".css", ".js", ".ts", ".tsx", ".jsx"]:
            obj = self._create_obj(f"src/app{ext}")
            assert app._get_preview_type(obj) == "text", f"Failed for {ext}"

    def test_text_files_config(self):
        """Test config files are detected as text."""
        app = self._create_mock_app()
        for ext in [".ini", ".cfg", ".toml"]:
            obj = self._create_obj(f"config/settings{ext}")
            assert app._get_preview_type(obj) == "text", f"Failed for {ext}"

    def test_text_files_case_insensitive(self):
        """Test text file detection is case insensitive."""
        app = self._create_mock_app()
        for ext in [".TXT", ".Py", ".JSON", ".MD"]:
            obj = self._create_obj(f"file{ext}")
            assert app._get_preview_type(obj) == "text", f"Failed for {ext}"

    def test_image_files_common(self):
        """Test common image formats are detected."""
        app = self._create_mock_app()
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
            obj = self._create_obj(f"images/photo{ext}")
            assert app._get_preview_type(obj) == "image", f"Failed for {ext}"

    def test_image_files_case_insensitive(self):
        """Test image detection is case insensitive."""
        app = self._create_mock_app()
        for ext in [".JPG", ".PNG", ".Gif"]:
            obj = self._create_obj(f"image{ext}")
            assert app._get_preview_type(obj) == "image", f"Failed for {ext}"

    def test_archive_files_zip(self):
        """Test ZIP files are detected as archives."""
        app = self._create_mock_app()
        obj = self._create_obj("backups/data.zip")
        assert app._get_preview_type(obj) == "archive"

    def test_archive_files_tar(self):
        """Test TAR files are detected as archives."""
        app = self._create_mock_app()
        obj = self._create_obj("backups/data.tar")
        assert app._get_preview_type(obj) == "archive"

    def test_archive_files_tar_gz(self):
        """Test TAR.GZ files are detected as archives."""
        app = self._create_mock_app()
        for ext in [".tar.gz", ".tgz"]:
            obj = self._create_obj(f"backups/data{ext}")
            assert app._get_preview_type(obj) == "archive", f"Failed for {ext}"

    def test_archive_files_gzip(self):
        """Test GZ files are detected as archives."""
        app = self._create_mock_app()
        obj = self._create_obj("logs/app.log.gz")
        assert app._get_preview_type(obj) == "archive"

    def test_unsupported_binary(self):
        """Test binary files return None."""
        app = self._create_mock_app()
        obj = self._create_obj("program.exe")
        assert app._get_preview_type(obj) is None

    def test_unsupported_unknown(self):
        """Test unknown extensions return None."""
        app = self._create_mock_app()
        obj = self._create_obj("data.xyz")
        assert app._get_preview_type(obj) is None

    def test_unsupported_no_extension(self):
        """Test files without extension return None."""
        app = self._create_mock_app()
        obj = self._create_obj("Dockerfile")
        assert app._get_preview_type(obj) is None

    def test_nested_path_detection(self):
        """Test preview type works with deeply nested paths."""
        app = self._create_mock_app()
        obj = self._create_obj("a/b/c/d/e/f/document.txt")
        assert app._get_preview_type(obj) == "text"


class TestMakeSelectableTag:
    """Tests for selectable tag generation."""

    def _create_mock_app(self):
        """Create a minimal mock app instance."""
        from lolrus.app import LolrusApp

        with patch.object(LolrusApp, '__init__', lambda self: None):
            app = LolrusApp()
            return app

    def test_tag_consistency(self):
        """Test same key always produces same tag."""
        app = self._create_mock_app()
        key = "folder/file.txt"
        tag1 = app._make_selectable_tag(key)
        tag2 = app._make_selectable_tag(key)
        assert tag1 == tag2

    def test_tag_uniqueness(self):
        """Test different keys produce different tags."""
        app = self._create_mock_app()
        tag1 = app._make_selectable_tag("file1.txt")
        tag2 = app._make_selectable_tag("file2.txt")
        assert tag1 != tag2

    def test_tag_format(self):
        """Test tag has expected format (obj_ prefix)."""
        app = self._create_mock_app()
        tag = app._make_selectable_tag("any/key.txt")
        assert tag.startswith("obj_")
        assert len(tag) == 16  # "obj_" + 12 hex chars

    def test_tag_special_characters(self):
        """Test tag handles special characters in key."""
        app = self._create_mock_app()
        # Should not raise and should produce valid tag
        tag = app._make_selectable_tag("folder/file with spaces & symbols!.txt")
        assert tag.startswith("obj_")
        assert len(tag) == 16

    def test_tag_unicode(self):
        """Test tag handles unicode characters."""
        app = self._create_mock_app()
        tag = app._make_selectable_tag("folder/файл.txt")  # Russian word for "file"
        assert tag.startswith("obj_")
        assert len(tag) == 16

    def test_tag_empty_key(self):
        """Test tag handles empty key."""
        app = self._create_mock_app()
        tag = app._make_selectable_tag("")
        assert tag.startswith("obj_")

    def test_tag_long_key(self):
        """Test tag handles very long keys."""
        app = self._create_mock_app()
        long_key = "a" * 1000 + "/file.txt"
        tag = app._make_selectable_tag(long_key)
        assert tag.startswith("obj_")
        assert len(tag) == 16  # Still fixed length


class TestPreviewTypeExtensions:
    """Comprehensive tests for all supported extensions."""

    def _create_mock_app(self):
        from lolrus.app import LolrusApp
        with patch.object(LolrusApp, '__init__', lambda self: None):
            return LolrusApp()

    def _create_obj(self, key: str) -> S3Object:
        return S3Object(key=key, size=100, last_modified=datetime.now(), etag="test")

    def test_all_text_extensions(self):
        """Test all documented text extensions."""
        app = self._create_mock_app()
        text_extensions = [
            ".txt", ".md", ".json", ".xml", ".csv", ".log", ".py",
            ".js", ".html", ".css", ".yaml", ".yml", ".toml", ".ini", ".cfg",
            ".sh", ".bat", ".ps1", ".sql", ".java", ".c", ".cpp", ".h", ".hpp",
            ".rs", ".go", ".rb", ".php", ".ts", ".tsx", ".jsx", ".vue", ".svelte",
        ]
        for ext in text_extensions:
            obj = self._create_obj(f"test{ext}")
            result = app._get_preview_type(obj)
            assert result == "text", f"Expected 'text' for {ext}, got {result}"

    def test_all_image_extensions(self):
        """Test all documented image extensions."""
        app = self._create_mock_app()
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
        for ext in image_extensions:
            obj = self._create_obj(f"test{ext}")
            result = app._get_preview_type(obj)
            assert result == "image", f"Expected 'image' for {ext}, got {result}"

    def test_all_archive_extensions(self):
        """Test all documented archive extensions."""
        app = self._create_mock_app()
        archive_extensions = [".zip", ".tar", ".tar.gz", ".tgz", ".gz"]
        for ext in archive_extensions:
            obj = self._create_obj(f"test{ext}")
            result = app._get_preview_type(obj)
            assert result == "archive", f"Expected 'archive' for {ext}, got {result}"
