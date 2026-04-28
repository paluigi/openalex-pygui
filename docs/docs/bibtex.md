# BibTeX Export

The app can fetch, cache, and export BibTeX entries for saved works.

## Fetching BibTeX

### Per-Work Fetch

Click the **document** icon on a library card to fetch BibTeX for that work. The app uses two sources with automatic fallback:

1. **doi.org content negotiation** — requests `application/x-bibtex` from `https://doi.org/{doi}`
2. **Crossref API** — fallback via `https://api.crossref.org/works/{doi}/transform/application/x-bibtex`

If a Polite Pool email is configured (Settings tab), it's included in the `User-Agent` header for better rate limits.

### Bulk Fetch

Click **Fetch All BibTeX** to fetch BibTeX for every work in the library that has a DOI but no cached BibTeX entry. This processes works sequentially and shows the count when done.

## Exporting

### Selective Export

1. Check works in the library using individual checkboxes or **Select all**
2. Click **Export Selected BibTeX**
3. Choose a save location (defaults to `library.bib`)

### Full Export

If no works are selected, clicking **Export Selected BibTeX** exports all works that have cached BibTeX entries.

## Caching

BibTeX is cached in the local SQLite database. Once fetched, it's stored in the `works.bibtex` column and reused on future exports without re-fetching. The "BibTeX" label appears in a card's metadata line when cached.
