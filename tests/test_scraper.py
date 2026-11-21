from pathlib import Path
import tempfile
import unittest

from arcived_month import archive_completed_months
from scraper import ROOT, classify, load_config, parse_trending, read_json, trending_url, update_archive


CARD = '''<html><a href="/login">Sign in</a><article class="Box-row">
<h2><a href="/demo/llm-kit"><svg><path /></svg>demo / llm-kit</a></h2>
<p>A &amp; B <b>LLM</b> toolkit. 中文简介</p>
<span itemprop="programmingLanguage">Python</span>
<a href="/demo/llm-kit/stargazers"><svg></svg>12,345</a>
<a href="/demo/llm-kit/forks">67</a><span>123 stars today</span>
</article></html>'''


class ScraperTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / 'config.json')

    def repo(self, name='demo/llm-kit'):
        repo = parse_trending(CARD)[0]
        repo.update(name=name, categories=['Quantitative Research & Trading'], sources=[{'language': 'all', 'period': 'daily', 'rank': 1, 'period_stars': 123}])
        return repo

    def root(self, temporary):
        root = Path(temporary)
        (root / 'README.template.md').write_text((ROOT / 'README.template.md').read_text(encoding='utf-8'), encoding='utf-8')
        return root

    def test_realistic_card_entities_and_metrics(self):
        repo = parse_trending(CARD)[0]
        self.assertEqual(repo['name'], 'demo/llm-kit')
        self.assertEqual(repo['description'], 'A & B LLM toolkit. 中文简介')
        self.assertEqual((repo['stars'], repo['forks'], repo['period_stars']), (12345, 67, 123))
        self.assertEqual(repo['language'], 'Python')

    def test_blocked_or_changed_html_aborts(self):
        with self.assertRaises(ValueError):
            parse_trending('<html>Please sign in</html>')

    def test_language_url_encodes_cpp(self):
        self.assertEqual(trending_url('c++', 'daily'), 'https://github.com/trending/c%2B%2B?since=daily')

    def test_finance_signals(self):
        for description in ['A quantitative backtesting platform', 'Personal finance and expense tracking', 'Open-source accounting software for businesses', '复式记账与银行支付', '股票行情数据和量化回测']:
            with self.subTest(description=description):
                self.assertTrue(classify({'name': 'demo/tool', 'description': description}, self.config))

    def test_cryptography_and_generic_tools_are_not_financial_signals(self):
        for description in ['A cryptography library for AES encryption', 'An agent framework for AI coding', 'A platform for trading collectible cards', 'A database migration and task scheduling tool', 'Quantitative microscopy for cell biology', 'LLM token budget management and inference', 'An LLM gateway with model routing, usage tracking and cost accounting']:
            with self.subTest(description=description):
                self.assertFalse(classify({'name': 'demo/tool', 'description': description}, self.config))

    def test_crypto_only_projects_are_excluded(self):
        for description in ['An Ethereum smart contract toolkit', 'On-chain analytics for DeFi', 'A crypto trading bot with backtesting', 'Bitcoin payment infrastructure', 'Decentralized finance portfolio management']:
            with self.subTest(description=description):
                self.assertFalse(classify({'name': 'demo/tool', 'description': description}, self.config))
        self.assertFalse(classify({'name': 'demo/utils', 'description': 'Standard library and utilities', 'language': 'Solidity'}, self.config))

    def test_broader_finance_tools_can_support_multiple_asset_classes(self):
        self.assertTrue(classify({'name': 'demo/tool', 'description': 'Stock and crypto portfolio management and market data'}, self.config))

    def test_exclude_overrides_include(self):
        self.config.update(include_repositories=['Demo/Tool'], exclude_repositories=['demo/tool'])
        self.assertFalse(classify({'name': 'DEMO/tool', 'description': 'Bitcoin payment tools'}, self.config))

    def test_deduplication_is_case_insensitive_and_survives_month_rollover(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.root(temporary)
            self.assertEqual(update_archive(root, '2026-12-31', [self.repo()], [], 1), 1)
            self.assertEqual(update_archive(root, '2027-01-01', [self.repo('Demo/LLM-kit')], [], 1), 0)
            archive_completed_months(root, '2027-01-01')
            self.assertTrue((root / 'archived/2026-12.md').exists())
            self.assertNotIn('[Demo/LLM-kit]', (root / 'README.md').read_text(encoding='utf-8'))
            records = read_json(root / 'data/repositories.json', {})['repositories']
            self.assertEqual(len(records), 1)
            self.assertEqual(records['demo/llm-kit']['first_seen'], '2026-12-31')
            self.assertEqual(records['demo/llm-kit']['last_seen'], '2027-01-01')

    def test_same_day_repeat_is_idempotent_and_merges_periods(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.root(temporary)
            update_archive(root, '2026-11-18', [self.repo()], ['daily'], 1)
            initial = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            update_archive(root, '2026-11-18', [self.repo()], ['daily'], 1)
            self.assertEqual(initial, {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()})
            weekly = self.repo()
            weekly['sources'][0]['period'] = 'weekly'
            update_archive(root, '2026-11-18', [weekly], ['weekly'], 1)
            snapshot = read_json(root / 'data/daily/2026-11-18.json', {})
            self.assertEqual(len(snapshot['repositories']), 1)
            self.assertEqual(len(snapshot['repositories'][0]['sources']), 2)

    def test_no_domain_matches_still_saves_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.root(temporary)
            self.assertEqual(update_archive(root, '2026-11-18', [], ['source'], 25), 0)
            self.assertEqual(read_json(root / 'data/daily/2026-11-18.json', {})['repositories'], [])
            self.assertIn('No new projects this month.', (root / 'README.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
