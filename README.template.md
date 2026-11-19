# Finance Trending Archive

[![Daily Finance Trending](https://github.com/zengzzzzz/finance-trending-archieve/actions/workflows/update.yml/badge.svg)](https://github.com/zengzzzzz/finance-trending-archieve/actions/workflows/update.yml)

Track and archive finance projects discovered on GitHub Trending.

<!-- SUMMARY -->

## Features

- Daily updates at **09:37 (UTC+8)** with GitHub Actions.
- Daily, weekly, and monthly Trending lists across eight sources, including the all-language list, with source periods and ranks recorded.
- Quantitative trading, financial data, portfolio management, payments, accounting, and personal finance tools.
- Deduplicated entries with first-seen dates, monthly archives, and daily JSON snapshots.
- No API keys or third-party dependencies required.

## Getting Started

Requires Python **3.12+**.

```bash
git clone https://github.com/zengzzzzz/finance-trending-archieve.git
cd finance-trending-archieve
python scraper.py
```

Edit `config.json` to customize languages, periods, keyword filters, and repository inclusion or exclusion. Use `--since daily`, `--since weekly`, or `--since monthly` to scan a single period.

Projects are filtered by repository names, descriptions, and programming languages, so results may include false matches or miss relevant projects. Crypto-specific projects are excluded; broader finance tools may support multiple asset classes. Original project descriptions are preserved.

## Automation

Run **Actions → Daily Finance Trending → Run workflow** for a manual update. Monthly archives are generated automatically; projects are listed only once by their first-seen month.

Edit `README.template.md` to change this page. Run `python -m unittest discover -s tests -v` to test locally.

## New This Month

<!-- ENTRIES -->
