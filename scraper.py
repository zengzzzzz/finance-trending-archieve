"""Archive finance repositories discovered on GitHub Trending. Python 3.12+, no dependencies."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SHANGHAI = timezone(timedelta(hours=8))
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def clean(text):
    return " ".join(text.split())


def number(text):
    match = re.search(r"([\d,.]+)\s*([kKmM]?)", text)
    if not match:
        return 0
    return int(float(match[1].replace(",", "")) * {"": 1, "k": 1000, "m": 1000000}[match[2].lower()])


class TrendingParser(HTMLParser):
    """Read only repository cards, ignoring navigation, avatars, and sponsor links."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.card = None
        self.repositories = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and "Box-row" in attrs.get("class", "").split():
            self.card = {"name": "", "description": [], "language": [], "text": [], "stars": [], "forks": []}
            self.stack = []
        if self.card is None:
            return
        if tag == "a" and any(t == "h2" for t, _ in self.stack):
            href = attrs.get("href", "")
            if re.fullmatch(r"/[\w.-]+/[\w.-]+/?", href):
                self.card["name"] = href.strip("/")
        if tag not in VOID_TAGS:
            self.stack.append((tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self.card is None:
            return
        self.card["text"].append(data)
        if any(t == "p" for t, _ in self.stack):
            self.card["description"].append(data)
        if any(a.get("itemprop") == "programmingLanguage" for _, a in self.stack):
            self.card["language"].append(data)
        for tag, attrs in self.stack:
            if tag == "a":
                href = attrs.get("href", "")
                for field, suffix in (("stars", "/stargazers"), ("forks", "/forks")):
                    if href.endswith(suffix):
                        self.card[field].append(data)

    def handle_endtag(self, tag):
        if self.card is None:
            return
        if tag == "article":
            card = self.card
            if card["name"]:
                growth = re.search(r"([\d,]+)\s+stars?\s+(today|this week|this month)", clean(" ".join(card["text"])))
                self.repositories.append({
                    "name": card["name"], "url": "https://github.com/" + card["name"],
                    "description": clean(" ".join(card["description"])),
                    "language": clean(" ".join(card["language"])) or "Unknown",
                    "stars": number("".join(card["stars"])), "forks": number("".join(card["forks"])),
                    "period_stars": number(growth[1]) if growth else None,
                })
            self.card = None
            self.stack = []
            return
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break


def parse_trending(html):
    parser = TrendingParser()
    parser.feed(html)
    if not parser.repositories:
        raise ValueError("No repository cards found; page may be blocked or GitHub HTML changed. Archive was not updated.")
    return parser.repositories


def fetch_html(url):
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "finance-trending-archieve/1.0 (+https://github.com/zengzzzzz/finance-trending-archieve)", "Accept": "text/html", "Accept-Language": "en-US,en;q=0.9"})
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError, OSError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def trending_url(language, period):
    return "https://github.com/trending" + ("/" + quote(language, safe="") if language else "") + "?" + urlencode({"since": period})


def classify(repo, config):
    key = repo["name"].casefold()
    if key in {name.casefold() for name in config.get("exclude_repositories", [])}:
        return []
    text = repo["name"] + " " + repo["description"] + " " + repo.get("language", "")
    focus = config.get("focus_filter", {})
    crypto_only = any(re.search(pattern, text, re.IGNORECASE) for pattern in focus.get("exclude_patterns", []))
    broader_finance = any(re.search(pattern, text, re.IGNORECASE) for pattern in focus.get("keep_patterns", []))
    if crypto_only and not broader_finance and key not in {name.casefold() for name in config.get("include_repositories", [])}:
        return []
    categories = [name for name, patterns in config["categories"].items() if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)]
    if not categories and key in {name.casefold() for name in config.get("include_repositories", [])}:
        categories = ["Manually Included"]
    return categories


def collect(config):
    sources = [(language, period) for period in config["periods"] for language in config["languages"]]
    def scrape(source):
        language, period = source
        url = trending_url(language, period)
        repos = parse_trending(fetch_html(url))
        print(f"{language or 'all'}/{period}: {len(repos)} repositories", flush=True)
        return source, url, repos

    matches = {}
    scanned = set()
    source_urls = []
    # Finish every request before touching archive files. Any failed source aborts the run.
    with ThreadPoolExecutor(max_workers=3) as pool:
        for (language, period), url, repos in pool.map(scrape, sources):
            source_urls.append(url)
            for rank, repo in enumerate(repos, 1):
                key = repo["name"].casefold()
                scanned.add(key)
                categories = classify(repo, config)
                if not categories:
                    continue
                if key not in matches:
                    matches[key] = {**repo, "categories": categories, "sources": []}
                matches[key]["sources"].append({"language": language or "all", "period": period, "rank": rank, "period_stars": repo["period_stars"]})
    return list(matches.values()), source_urls, len(scanned)


def read_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def md(text):
    return re.sub(r"([\\`*_{}\[\]<>|])", r"\\\1", clean(text))


def entries_markdown(records):
    lines = []
    for record in sorted(records, key=lambda item: (item["first_seen"], item["name"].casefold()), reverse=True):
        lines.append(f"* 【{record['first_seen']}】[{record['name']}](https://github.com/{record['name']}) - {md(record['description'])}  \n  `{md(record['language'])}` · {', '.join(record['categories'])} · ![Stars](https://img.shields.io/github/stars/{record['name']}?style=social)")
    return "\n\n".join(lines) or "No new projects this month."


def write_archive_index(root):
    months = sorted(
        (path.stem for path in (root / "archived").glob("????-??.md")
         if re.fullmatch(r"\d{4}-\d{2}", path.stem)), reverse=True
    )
    write_text(root / "archived" / "README.md", "# Monthly Archives\n\n" +
               ("\n".join(f"- [{month}]({month}.md)" for month in months) or "No archives yet.") + "\n")


def write_monthly_archives(root, records, current_month):
    months = sorted({r["first_seen"][:7] for r in records.values()
                     if r["first_seen"][:7] < current_month}, reverse=True)
    for month in months:
        monthly_records = [r for r in records.values() if r["first_seen"].startswith(month)]
        write_text(root / "archived" / f"{month}.md",
                   f"# Finance Trending Archive · {month}\n\n"
                   "Projects are listed once, by their first-seen date.\n\n" +
                   entries_markdown(monthly_records) + "\n")
    write_archive_index(root)
    return months


def update_archive(root, today, repos, sources, scanned):
    state_path = root / "data" / "repositories.json"
    state = read_json(state_path, {"schema_version": 1, "repositories": {}})
    records = state["repositories"]
    additions = 0
    for repo in repos:
        key = repo["name"].casefold()
        previous = records.get(key)
        if previous is None:
            additions += 1
        records[key] = {**repo, "first_seen": previous["first_seen"] if previous else today, "last_seen": today}
    snapshot_path = root / "data" / "daily" / f"{today}.json"
    # A repeat on the same day merges sources/periods and never discards earlier sightings.
    snapshot = read_json(snapshot_path, {"date": today, "repositories": [], "sources": []})
    daily = {item["name"].casefold(): item for item in snapshot["repositories"]}
    for repo in repos:
        key = repo["name"].casefold()
        merged_sources = {(s["language"], s["period"]): s for s in daily.get(key, {}).get("sources", [])}
        merged_sources.update({(s["language"], s["period"]): s for s in repo["sources"]})
        daily[key] = {**repo, "sources": list(merged_sources.values())}
    snapshot.update({"schema_version": 1, "sources": sorted(set(snapshot["sources"]) | set(sources)), "repositories": sorted(daily.values(), key=lambda r: r["name"].casefold())})
    snapshot["scanned_repositories"] = max(scanned, snapshot.get("scanned_repositories", 0))
    write_archive_index(root)
    write_text(state_path, json_text(state))
    write_text(snapshot_path, json_text(snapshot))
    render_readme(root, today, records, snapshot, additions)
    return additions


def render_readme(root, today, records, snapshot, additions):
    template = (root / "README.template.md").read_text(encoding="utf-8")
    current = [r for r in records.values() if r["first_seen"].startswith(today[:7])]
    snapshot_day = snapshot.get("date")
    found_today = len(snapshot.get("repositories", [])) if snapshot_day == today else 0
    snapshot_link = f"[Daily Snapshot](data/daily/{snapshot_day}.json)" if snapshot_day else "No daily snapshot yet"
    summary = f"Updated: **{today} (UTC+8)** · **{len(records)}** projects archived · **{len(current)}** new this month · **{found_today}** found today\n\n{snapshot_link} · [Project Index](data/repositories.json) · [Monthly Archives](archived/README.md)"
    write_text(root / "README.md", template.replace("<!-- SUMMARY -->", summary).replace("<!-- ENTRIES -->", entries_markdown(current)))


def load_config(path):
    config = read_json(path, None)
    if not config or not config.get("languages") or not config.get("periods") or not config.get("categories"):
        raise ValueError("Config must contain non-empty languages, periods, and categories")
    if not set(config["periods"]) <= {"daily", "weekly", "monthly"}:
        raise ValueError("Periods must be daily, weekly, or monthly")
    for patterns in config["categories"].values():
        for pattern in patterns:
            re.compile(pattern, re.IGNORECASE)
    for patterns in config.get("focus_filter", {}).values():
        for pattern in patterns:
            re.compile(pattern, re.IGNORECASE)
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    parser.add_argument("--since", choices=["daily", "weekly", "monthly"], help="Override configured Trending period")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.since:
        config["periods"] = [args.since]
    today = datetime.now(SHANGHAI).date().isoformat()
    repos, sources, scanned = collect(config)
    additions = update_archive(ROOT, today, repos, sources, scanned)
    print(f"Scanned {scanned} unique projects; matched {len(repos)} finance projects; added {additions} new projects.")


if __name__ == "__main__":
    main()
