# Arsenal Transfer Crawler

A small Python tool that collects Arsenal transfer news from trusted football news feeds, ranks stories by source credibility and transfer relevance, and sends a clean HTML digest to `maxdowman1231@outlook.com` every morning at 08:00.

## Features

- Pulls RSS/Atom feeds from Arsenal.com, BBC Sport, Sky Sports, The Guardian, and ESPN.
- Filters for Arsenal-related transfer terms such as signing, deal, loan, medical, bid, and contract.
- Sorts results by a credibility-weighted score.
- Generates a polished HTML email with source, credibility score, publication time, summary, and source link.
- Supports one-off dry runs and a long-running daily scheduler.
- Uses only Python standard-library modules at runtime, so deployment is simple.
- Keeps Gmail app-password credentials in environment variables instead of source code.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp config.example.yml config.yml
```

Edit `config.yml` if you want to adjust sources, the lookback window, or the send time.

## Gmail configuration

The sender uses Gmail SMTP. Create a Gmail app password in your Google Account security settings, then set these environment variables before sending email:

```bash
export GMAIL_ADDRESS="your-gmail-address@gmail.com"
export GMAIL_APP_PASSWORD="your-16-character-app-password"
```

Optional overrides are available if Gmail changes SMTP endpoints, but the defaults are `smtp.gmail.com` and port `587`:

```bash
export GMAIL_SMTP_HOST="smtp.gmail.com"
export GMAIL_SMTP_PORT="587"
```

## Usage

Render a report locally without sending email:

```bash
arsenal-transfer-crawler --config config.yml once --dry-run --output report.html
```

Send one email now:

```bash
arsenal-transfer-crawler --config config.yml once
```

Run continuously and send every day at the configured time, defaulting to 08:00 Europe/London:

```bash
arsenal-transfer-crawler --config config.yml schedule
```

## Daily automation options

### Cron

Run at 08:00 every day on a server:

```cron
0 8 * * * cd /path/to/ArsenalTransferCrawler && . .venv/bin/activate && arsenal-transfer-crawler --config config.yml once
```

### GitHub Actions

The workflow in `.github/workflows/daily-digest.yml` can run the digest at 08:00 UTC. Add `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` as repository secrets before enabling it.

## How ranking works

Each item receives a score from:

1. The source credibility configured in `config.yml`.
2. The number of transfer-related keywords found in the title and summary.
3. Publication recency as a tie-breaker.

Higher scoring items appear first in the email.
