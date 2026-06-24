"""Unit tests for file_cleaner module.

Every OS-level side effect (os.listdir, os.remove) is mocked so that
the test suite is safe to run on any machine.
"""

import os
import unittest
from unittest.mock import MagicMock, call, patch

from file_cleaner import clean, filter_non_py, list_files, main, remove_file


# ── list_files ──────────────────────────────────────────────


class TestListFiles(unittest.TestCase):
    """Tests for list_files()."""

    @patch("file_cleaner.os.listdir")
    def test_returns_directory_contents(self, mock_listdir: MagicMock) -> None:
        mock_listdir.return_value = ["a.txt", "b.py", "c.log"]
        result = list_files("/some/dir")
        mock_listdir.assert_called_once_with("/some/dir")
        self.assertEqual(result, ["a.txt", "b.py", "c.log"])

    @patch("file_cleaner.os.listdir")
    def test_defaults_to_current_directory(self, mock_listdir: MagicMock) -> None:
        mock_listdir.return_value = []
        list_files()
        mock_listdir.assert_called_once_with(".")

    @patch("file_cleaner.os.listdir")
    def test_empty_directory(self, mock_listdir: MagicMock) -> None:
        mock_listdir.return_value = []
        self.assertEqual(list_files("/empty"), [])


# ── filter_non_py ───────────────────────────────────────────


class TestFilterNonPy(unittest.TestCase):
    """Tests for filter_non_py()."""

    def test_filters_out_py_files(self) -> None:
        files = ["script.py", "data.csv", "readme.md", "test.py"]
        self.assertEqual(filter_non_py(files), ["data.csv", "readme.md"])

    def test_all_py_files_returns_empty(self) -> None:
        files = ["a.py", "b.py"]
        self.assertEqual(filter_non_py(files), [])

    def test_no_py_files_returns_all(self) -> None:
        files = ["a.txt", "b.log", "c.dat"]
        self.assertEqual(filter_non_py(files), ["a.txt", "b.log", "c.dat"])

    def test_empty_list(self) -> None:
        self.assertEqual(filter_non_py([]), [])

    def test_dotpy_must_be_suffix(self) -> None:
        files = ["py", ".py", "file.pyc", "file.py.bak", "file.PY"]
        # Only ".py" exactly at the end matches
        expected = ["py", "file.pyc", "file.py.bak", "file.PY"]
        self.assertEqual(filter_non_py(files), expected)

    def test_hidden_py_file(self) -> None:
        files = [".hidden.py", ".hidden.txt"]
        self.assertEqual(filter_non_py(files), [".hidden.txt"])


# ── remove_file ─────────────────────────────────────────────


class TestRemoveFile(unittest.TestCase):
    """Tests for remove_file()."""

    @patch("file_cleaner.os.remove")
    def test_successful_removal(self, mock_remove: MagicMock) -> None:
        success, msg = remove_file("data.csv")
        mock_remove.assert_called_once_with("data.csv")
        self.assertTrue(success)
        self.assertIn("silindi", msg)

    @patch("file_cleaner.os.remove", side_effect=IsADirectoryError)
    def test_directory_error(self, mock_remove: MagicMock) -> None:
        success, msg = remove_file("somedir")
        self.assertFalse(success)
        self.assertIn("klasor", msg)

    @patch("file_cleaner.os.remove", side_effect=PermissionError)
    def test_permission_error(self, mock_remove: MagicMock) -> None:
        success, msg = remove_file("locked.dat")
        self.assertFalse(success)
        self.assertIn("izin hatasi", msg)

    @patch("file_cleaner.os.remove", side_effect=OSError("disk full"))
    def test_generic_exception(self, mock_remove: MagicMock) -> None:
        success, msg = remove_file("broken.bin")
        self.assertFalse(success)
        self.assertIn("silinemedi", msg)
        self.assertIn("disk full", msg)

    @patch("file_cleaner.os.remove")
    def test_message_contains_filename(self, mock_remove: MagicMock) -> None:
        _, msg = remove_file("report.pdf")
        self.assertIn("report.pdf", msg)


# ── clean ───────────────────────────────────────────────────


class TestClean(unittest.TestCase):
    """Tests for the high-level clean() orchestrator."""

    @patch("file_cleaner.os.remove")
    @patch("file_cleaner.os.listdir")
    def test_removes_non_py_files(
        self, mock_listdir: MagicMock, mock_remove: MagicMock
    ) -> None:
        mock_listdir.return_value = ["keep.py", "delete.txt", "delete.log"]
        results = clean(".")
        self.assertEqual(mock_remove.call_count, 2)
        mock_remove.assert_any_call("delete.txt")
        mock_remove.assert_any_call("delete.log")
        self.assertEqual(len(results), 2)
        self.assertTrue(all(success for _, success, _ in results))

    @patch("file_cleaner.os.remove")
    @patch("file_cleaner.os.listdir")
    def test_keeps_all_py_files(
        self, mock_listdir: MagicMock, mock_remove: MagicMock
    ) -> None:
        mock_listdir.return_value = ["a.py", "b.py", "c.py"]
        results = clean(".")
        mock_remove.assert_not_called()
        self.assertEqual(results, [])

    @patch("file_cleaner.os.remove")
    @patch("file_cleaner.os.listdir")
    def test_empty_directory(
        self, mock_listdir: MagicMock, mock_remove: MagicMock
    ) -> None:
        mock_listdir.return_value = []
        results = clean(".")
        mock_remove.assert_not_called()
        self.assertEqual(results, [])

    @patch("file_cleaner.os.remove", side_effect=PermissionError)
    @patch("file_cleaner.os.listdir")
    def test_partial_failure(
        self, mock_listdir: MagicMock, mock_remove: MagicMock
    ) -> None:
        mock_listdir.return_value = ["locked.dat"]
        results = clean(".")
        self.assertEqual(len(results), 1)
        name, success, msg = results[0]
        self.assertEqual(name, "locked.dat")
        self.assertFalse(success)

    @patch("file_cleaner.os.remove")
    @patch("file_cleaner.os.listdir")
    def test_mixed_results(
        self, mock_listdir: MagicMock, mock_remove: MagicMock
    ) -> None:
        def side_effect(path: str) -> None:
            if path == "locked.dat":
                raise PermissionError
        mock_remove.side_effect = side_effect
        mock_listdir.return_value = ["ok.txt", "locked.dat", "keep.py"]
        results = clean(".")
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0][1])   # ok.txt succeeded
        self.assertFalse(results[1][1])  # locked.dat failed

    @patch("file_cleaner.os.remove")
    @patch("file_cleaner.os.listdir")
    def test_uses_join_for_non_dot_directory(
        self, mock_listdir: MagicMock, mock_remove: MagicMock
    ) -> None:
        mock_listdir.return_value = ["file.txt"]
        clean("/tmp/test")
        mock_remove.assert_called_once_with(os.path.join("/tmp/test", "file.txt"))

    @patch("file_cleaner.os.remove")
    @patch("file_cleaner.os.listdir")
    def test_prints_completion_message(
        self, mock_listdir: MagicMock, mock_remove: MagicMock
    ) -> None:
        mock_listdir.return_value = []
        with patch("builtins.print") as mock_print:
            clean(".")
            mock_print.assert_called_with("Islem tamamlandi!")

    @patch("file_cleaner.os.remove")
    @patch("file_cleaner.os.listdir")
    def test_prints_per_file_message(
        self, mock_listdir: MagicMock, mock_remove: MagicMock
    ) -> None:
        mock_listdir.return_value = ["data.csv"]
        with patch("builtins.print") as mock_print:
            clean(".")
            calls = mock_print.call_args_list
            self.assertTrue(any("silindi" in str(c) for c in calls))

    @patch("file_cleaner.os.remove", side_effect=IsADirectoryError)
    @patch("file_cleaner.os.listdir")
    def test_directory_in_listing_is_skipped(
        self, mock_listdir: MagicMock, mock_remove: MagicMock
    ) -> None:
        mock_listdir.return_value = ["subdir"]
        results = clean(".")
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][1])
        self.assertIn("klasor", results[0][2])


# ── main ────────────────────────────────────────────────────


class TestMain(unittest.TestCase):
    """Tests for the main() entry-point."""

    @patch("file_cleaner.clean")
    def test_main_calls_clean_with_dot(self, mock_clean: MagicMock) -> None:
        mock_clean.return_value = []
        main()
        mock_clean.assert_called_once_with(".")


if __name__ == "__main__":
    unittest.main()
