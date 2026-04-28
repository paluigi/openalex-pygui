# OpenAlex Research Manager

Desktop app to search [OpenAlex](https://openalex.org), manage a local SQLite library, and export BibTeX.

Built with **Flet 0.84**, **openalex-py**, **httpx**, and **tenacity**.

## Features

- **Classical & Semantic Search** — keyword or vector-based search across the OpenAlex corpus
- **Search Scope** — limit search to title only, title + abstract, or full text
- **Sort & Limit** — sort by relevance, citations, newest, or oldest; 10/25/50 results
- **Rich Result Cards** — title, year, citations, relevance score, authors, journal, keywords, abstract preview, DOI and OpenAlex links
- **Batch Save** — select multiple works and save in bulk
- **Library Management** — filter by keyword or custom tag, text search, edit notes/abstract/tags
- **Related & Referenced Works** — browse related works and bibliography with inline save
- **BibTeX Export** — fetch per work (doi.org + Crossref fallback), bulk fetch, selective or full export
- **Settings** — API key, Polite Pool email, theme toggle (system/light/dark), desktop shortcut

## Quick Start

```bash
# Clone and install
git clone https://github.com/your-username/openalex-pygui.git
cd openalex-pygui
uv sync

# Run
uv run openalex-pygui
```

See [Getting Started](getting-started.md) for detailed setup instructions.
