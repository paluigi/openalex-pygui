# OpenAlex Research Manager

Desktop app to search [OpenAlex](https://openalex.org), manage a local SQLite library, and export BibTeX.

Built with **Flet 0.84**, **openalex-py**, **httpx**, and **tenacity**.

## Features

### Search Tab
- **Classical & Semantic Search** — Toggle between keyword search and semantic (vector-based) search
- **Search Scope** — Limit search to Title only, Title + Abstract (default), or Full text
- **Sort & Limit** — Sort by Relevance, Most cited, Newest, or Oldest; limit to 10/25/50 results
- **Rich Result Cards** — Title, year, citations, relevance score, authors, journal, keyword chips, abstract preview, clickable DOI and OpenAlex links
- **Batch Save** — Select all / individual works via checkboxes and save in bulk

### Library Tab
- **Filter by Keyword or Custom Tag** — Two dropdowns populated from OpenAlex keywords and user-created tags
- **Text Search** — Filter by title or abstract text
- **Tag System** — Assign comma-separated custom tags to any work via the edit dialog; existing tags appear as clickable suggestion chips
- **Related & Referenced Works** — Dedicated buttons to browse related works and bibliography in a popup (fetched via `get_by_id` with retry)
- **BibTeX** — Fetch per-work BibTeX (doi.org + Crossref fallback), bulk-fetch all, and export selected or all works as `.bib`
- **Edit Dialog** — Edit notes, abstract, and tags for any saved work
- **Clickable Links** — DOI and OpenAlex links on every card
- **Batch Export** — Select works via checkboxes and export BibTeX for the selection

### Settings Tab
- **API Key** — Configure OpenAlex API key for higher rate limits
- **Polite Pool Email** — Set email for Crossref/doi.org content negotiation
- **Theme** — Switch between System, Light, and Dark mode
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
├── db.py         # SQLite database layer (8 normalized tables)
├── api.py        # OpenAlex search + BibTeX retrieval + single-work fetch
└── utils.py      # Desktop shortcut helper
```

## Database Schema

| Table | Purpose |
|---|---|
| `works` | Saved works with metadata, notes, journal |
| `authors` | Author records |
| `work_authors` | Work-author join (with position) |
| `work_keywords` | OpenAlex keywords per work |
| `work_tags` | User-defined custom tags per work |
| `work_relationships` | Related/referenced work IDs |
| `settings` | Key-value app settings |

## Change Log

- **0.2.0** (2026-04-25) — Related/referenced works browser, keyword+tag filtering, search scope selector, clickable DOI+OpenAlex links, custom tags, tenacity retry, background fetch with spinner
- **0.1.0** (2026-04-25) — Initial implementation: search, library, BibTeX export, settings, desktop shortcut
