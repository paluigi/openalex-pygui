# OpenAlex Research Manager

Desktop app to search [OpenAlex](https://openalex.org), manage a local SQLite library, and export BibTeX.

Built with **Flet**, **openalex-py**, and **httpx**.

## Features

- **Search** — Query OpenAlex works by keyword; view title, year, citation count, and abstract
- **Library** — Save works locally to SQLite; filter, remove, and fetch BibTeX per work
- **BibTeX Export** — Fetch BibTeX via doi.org content negotiation (Crossref fallback) and export the whole library as `.bib`
- **Settings** — Configure OpenAlex API key and Polite Pool email
- **Desktop Shortcut** — One-click shortcut creation

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Quick Start

```bash
# Install dependencies
uv sync

# Run the app
uv run openalex-pygui
```

## Project Structure

```
src/openalex_pygui/
├── __init__.py   # Package marker
├── main.py       # Flet UI — 3-tab app (Search, Library, Settings)
├── db.py         # SQLite database layer (6 normalized tables)
├── api.py        # OpenAlex search + BibTeX retrieval
└── utils.py      # Desktop shortcut helper
```

## Database Schema

| Table | Purpose |
|---|---|
| `works` | Saved works with metadata |
| `authors` | Author records |
| `work_authors` | Work-author join (with position) |
| `work_keywords` | Work keywords |
| `work_relationships` | Related/referenced works |
| `settings` | Key-value app settings |

## Change Log

- **0.1.0** (2026-04-25) — Initial implementation: search, library, BibTeX export, settings, desktop shortcut
