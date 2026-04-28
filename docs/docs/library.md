# Library

The Library tab displays all saved works and provides filtering, editing, and navigation features.

## Viewing Works

Works are listed as cards showing title, metadata (year, citations, authors, journal, BibTeX status), links, custom tags, and OpenAlex keywords. Works are sorted by date added (newest first) by default.

## Filtering

Three filter options are available:

### Text Search

Type in the **Filter library** field and press Enter to filter by title or abstract text.

### Keyword Filter

The **Keyword** dropdown is populated from all OpenAlex keywords attached to saved works. Select a keyword to show only works tagged with it.

### Tag Filter

The **Tag** dropdown is populated from all user-created custom tags. Select a tag to show only works with that tag.

Filters can be combined — e.g., search for "transformer" while filtering by the "important" tag.

## Custom Tags

Tags are user-defined labels you can assign to any work:

1. Click the **edit** (pencil) icon on a work card
2. In the **Tags** field, enter comma-separated tags (e.g., `important, to-read, methods`)
3. Existing tags from other works appear as clickable suggestion chips
4. Click **Save** to apply

Tags are displayed as chips on library cards and can be filtered via the Tag dropdown.

## Editing Notes & Abstract

Click the **edit** icon to open the edit dialog:

- **Notes** — free-text field for your annotations
- **Abstract** — editable abstract (pre-populated from OpenAlex)
- **Tags** — comma-separated custom tags

## Related & Referenced Works

Two buttons on each work card:

- **Related works** (hub icon) — shows works that OpenAlex considers related
- **Referenced works** (quote icon) — shows the bibliography / references cited by the work

Clicking either opens a dialog that fetches each work individually with retry (exponential backoff + jitter). Works can be saved directly from the popup.

## Removing Works

Click the **delete** (trash) icon on a work card to remove it from your library. This also removes associated authors, keywords, tags, and relationships.
