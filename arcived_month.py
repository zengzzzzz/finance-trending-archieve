"""Archive completed months without fetching data or changing daily snapshots."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from scraper import ROOT, SHANGHAI, read_json, render_readme, write_monthly_archives


def archive_completed_months(root=ROOT, today=None):
    root = Path(root)
    today = today or datetime.now(SHANGHAI).date().isoformat()
    current_month = date.fromisoformat(today).strftime("%Y-%m")
    state = read_json(root / "data" / "repositories.json", {"repositories": {}})
    records = state["repositories"]
    if not records:
        print("No project records to archive.")
        return []
    months = write_monthly_archives(root, records, current_month)
    snapshots = sorted(
        path for path in (root / "data" / "daily").glob("????-??-??.json")
        if path.stem <= today
    )
    snapshot = read_json(snapshots[-1], {}) if snapshots else {}
    render_readme(root, today, records, snapshot, 0)
    print("Archived completed months: " + (", ".join(months) or "none"))
    return months


if __name__ == "__main__":
    archive_completed_months()
