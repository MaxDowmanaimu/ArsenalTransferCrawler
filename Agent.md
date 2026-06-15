# Agent Guide

## Project purpose

This repository contains a Python command-line tool that collects Arsenal transfer news from configured RSS feeds, ranks the items by source credibility and transfer relevance, and emails a clear HTML digest to `maxdowman1231@outlook.com`.

## Important paths

- `src/arsenal_transfer_crawler/config.py` defines default sources, keywords, and YAML configuration loading.
- `src/arsenal_transfer_crawler/crawler.py` fetches feeds, filters Arsenal transfer stories, deduplicates items, and ranks results.
- `src/arsenal_transfer_crawler/emailer.py` renders the HTML template and sends email through Gmail SMTP environment variables.
- `src/arsenal_transfer_crawler/cli.py` provides the `once` and `schedule` commands.
- `src/arsenal_transfer_crawler/emailer.py` controls the visual email layout through inline HTML/CSS.
- `config.example.yml` shows runtime configuration.
- `.github/workflows/daily-digest.yml` is an optional scheduled runner.

## Development notes

- Do not commit real Gmail addresses, app passwords, or private email passwords.
- Prefer RSS/Atom feeds or official APIs over scraping HTML pages where possible.
- Keep source credibility values explicit in configuration so rankings are easy to audit.
- If adding a source, include keywords when the feed is broad and not Arsenal-specific.
- Use `python -m compileall src` as a quick syntax check.

## Common commands

```bash
pip install -e .
python -m compileall src
arsenal-transfer-crawler --config config.example.yml once --dry-run --output report.html
```
