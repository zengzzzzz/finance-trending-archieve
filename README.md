# Finance Trending Archive

[![Daily Github Trending](https://github.com/zengzzzzz/finance-trending-archieve/actions/workflows/schedule_daily.yml/badge.svg)](https://github.com/zengzzzzz/finance-trending-archieve/actions/workflows/schedule_daily.yml)

Track and archive finance projects discovered on GitHub Trending.

Updated: **2026-11-23 (UTC+8)** · **6** projects archived · **6** new this month · **0** found today

[Daily Snapshot](data/daily/2026-11-23.json) · [Project Index](data/repositories.json) · [Monthly Archives](archived/README.md)

## Features

- Daily updates at **09:00 (UTC+8)** with GitHub Actions.
- Daily Trending lists for all languages, Go, Python, JavaScript, Java, C, C++, and TypeScript.
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

Run **Actions → Daily Github Trending → Run workflow** for a manual update. Run **Actions → Monthly Github Trending Archive → Run workflow** to archive completed months. Monthly archiving runs at **08:00 (UTC+8) on the first day of each month**; projects are listed once by their first-seen month.

Edit `README.template.md` to change this page. Run `python -m unittest discover -s tests -v` to test locally.

## New This Month

* 【2026-11-20】[wealthfolio/wealthfolio](https://github.com/wealthfolio/wealthfolio) - A beautiful, private, local-first personal finance tracker. Investments, net worth, spending, and simulations.  
  `Rust` · Market Data & Financial Analysis, Personal Finance & Budgeting · ![Stars](https://img.shields.io/github/stars/wealthfolio/wealthfolio?style=social)

* 【2026-11-20】[juspay/hyperswitch](https://github.com/juspay/hyperswitch) - Open source, composable payments platform \| PCI compliant \| SaaS and Self-host options \| Enables connectivity to multiple payment, payout, fraud, vault and tokenization providers \| Uplifts authorization with intelligent routing and revenue recovery \| Reduce payment processing costs with cost observability \| Reduces payment ops with reconciliation  
  `Rust` · Payments, Banking & Accounting · ![Stars](https://img.shields.io/github/stars/juspay/hyperswitch?style=social)

* 【2026-11-19】[ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) - LLM 驱动的多市场股票智能分析系统：多源行情、实时新闻、决策看板与自动推送，支持零成本定时运行。 LLM-powered multi-market stock analysis system with multi-source market data, real-time news, decision dashboard, automated notifications, and cost-free scheduled runs.  
  `Python` · Market Data & Financial Analysis · ![Stars](https://img.shields.io/github/stars/ZhuLinsen/daily_stock_analysis?style=social)

* 【2026-11-19】[we-promise/sure](https://github.com/we-promise/sure) - The personal finance app for everyone (by everyone)  
  `Ruby` · Market Data & Financial Analysis, Personal Finance & Budgeting · ![Stars](https://img.shields.io/github/stars/we-promise/sure?style=social)

* 【2026-11-19】[tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills) - Claude Code skills for equity investors and traders — market analysis, technical charting, economic calendars, screeners, and trading strategy development.  
  `Python` · Quantitative Research & Trading, Market Data & Financial Analysis · ![Stars](https://img.shields.io/github/stars/tradermonty/claude-trading-skills?style=social)

* 【2026-11-19】[TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) - TradingAgents: Multi-Agents LLM Financial Trading Framework  
  `Python` · Market Data & Financial Analysis · ![Stars](https://img.shields.io/github/stars/TauricResearch/TradingAgents?style=social)
