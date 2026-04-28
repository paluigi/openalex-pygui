# Search

The Search tab lets you query the OpenAlex corpus and save works to your local library.

## Search Modes

### Classical Search

The default mode. Uses OpenAlex keyword search.

- **Title + Abstract** (default) — searches titles and abstracts
- **Title only** — limits search to work titles only
- **Full text** — searches titles, abstracts, and full text content

### Semantic Search

Uses OpenAlex vector-based similarity search (`.similar()`). Semantic search ignores the scope selector since it operates on the full work representation.

## Sorting

| Option | Description |
|---|---|
| Relevance | Sort by relevance score (default) |
| Most cited | Sort by citation count, descending |
| Newest first | Sort by publication year, descending |
| Oldest first | Sort by publication year, ascending |

## Result Limit

Choose 10, 25 (default), or 50 results per search.

## Result Cards

Each result card shows:

- **Title** — bold, with up to 2 lines
- **Metadata** — year, citation count, relevance score, authors (up to 3 + et al.), journal
- **Links** — clickable DOI and OpenAlex URLs
- **Keywords** — up to 6 keyword chips from OpenAlex
- **Abstract** — preview (first 300 characters)
- **Save** button — turns to "Saved" once added to the library

## Batch Save

1. Check **Select all** or individual checkboxes on result cards
2. Click **Save Selected**
3. Already-saved works are shown with a disabled checkbox and "Saved" label
