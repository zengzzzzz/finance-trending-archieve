from pathlib import Path
import tempfile
import unittest

from arcived_month import archive_completed_months
from scraper import ROOT, read_json, update_archive


class MonthlyArchiveTests(unittest.TestCase):
    def setup_root(self, path):
        root = Path(path)
        (root / "README.template.md").write_text(
            (ROOT / "README.template.md").read_text(encoding="utf-8"), encoding="utf-8"
        )
        return root

    def repo(self, name):
        return {"name": name, "description": "Test project", "language": "Python",
                "categories": [], "sources": [], "url": "https://github.com/" + name}

    def files(self, root):
        return {p.relative_to(root).as_posix(): p.read_bytes()
                for p in root.rglob("*") if p.is_file()}

    def test_daily_only_updates_the_current_readme_and_snapshots(self):
        with tempfile.TemporaryDirectory() as path:
            root = self.setup_root(path)
            update_archive(root, "2026-11-30", [self.repo("demo/old")], [], 1)
            self.assertFalse((root / "archived/2026-11.md").exists())
            self.assertTrue((root / "data/daily/2026-11-30.json").exists())
            self.assertIn("[demo/old]", (root / "README.md").read_text(encoding="utf-8"))

    def test_midmonth_manual_run_preserves_current_entries_and_source_data(self):
        with tempfile.TemporaryDirectory() as path:
            root = self.setup_root(path)
            update_archive(root, "2026-10-31", [self.repo("demo/old")], [], 1)
            update_archive(root, "2026-11-15", [self.repo("demo/current")], [], 1)
            before = {k: v for k, v in self.files(root).items() if k.startswith("data/")}
            self.assertEqual(archive_completed_months(root, "2026-11-20"), ["2026-10"])
            archived = (root / "archived/2026-10.md").read_text(encoding="utf-8")
            self.assertIn("[demo/old]", archived)
            self.assertNotIn("[demo/current]", archived)
            self.assertFalse((root / "archived/2026-11.md").exists())
            readme = (root / "README.md").read_text(encoding="utf-8")
            self.assertIn("[demo/current]", readme)
            self.assertNotIn("[demo/old]", readme)
            self.assertNotIn("[Daily Snapshot]", readme)
            self.assertNotIn("[Project Index]", readme)
            self.assertIn("**0** found today", readme)
            self.assertEqual(before, {k: v for k, v in self.files(root).items() if k.startswith("data/")})

    def test_year_rollover_and_repeat_run_are_safe(self):
        with tempfile.TemporaryDirectory() as path:
            root = self.setup_root(path)
            update_archive(root, "2026-12-31", [self.repo("demo/old")], [], 1)
            self.assertEqual(archive_completed_months(root, "2027-01-01"), ["2026-12"])
            before = self.files(root)
            archive_completed_months(root, "2027-01-01")
            self.assertEqual(before, self.files(root))
            self.assertEqual(update_archive(root, "2027-01-01", [self.repo("demo/old")], [], 1), 0)
            self.assertNotIn("[demo/old]", (root / "README.md").read_text(encoding="utf-8"))

    def test_delayed_run_catches_up_multiple_completed_months(self):
        with tempfile.TemporaryDirectory() as path:
            root = self.setup_root(path)
            for day in ["2026-09-30", "2026-10-31", "2026-11-30"]:
                update_archive(root, day, [self.repo("demo/" + day)], [], 1)
            self.assertEqual(archive_completed_months(root, "2026-12-01"),
                             ["2026-11", "2026-10", "2026-09"])
            for month in ["2026-09", "2026-10", "2026-11"]:
                self.assertTrue((root / "archived" / (month + ".md")).exists())

    def test_missing_records_do_not_erase_readme(self):
        with tempfile.TemporaryDirectory() as path:
            root = self.setup_root(path)
            (root / "README.md").write_text("Existing content", encoding="utf-8")
            self.assertEqual(archive_completed_months(root, "2027-01-01"), [])
            self.assertEqual((root / "README.md").read_text(encoding="utf-8"), "Existing content")

    def test_legacy_current_month_archive_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as path:
            root = self.setup_root(path)
            update_archive(root, "2026-11-15", [self.repo("demo/current")], [], 1)
            archive = root / "archived/2026-11.md"
            archive.write_text("Preserved legacy archive", encoding="utf-8")
            archive_completed_months(root, "2026-11-20")
            self.assertEqual(archive.read_text(encoding="utf-8"), "Preserved legacy archive")


if __name__ == "__main__":
    unittest.main()
