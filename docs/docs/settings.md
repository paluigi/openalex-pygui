# Settings

The Settings tab configures API access, BibTeX retrieval, appearance, and desktop integration.

## OpenAlex API Key

An API key increases your rate limit from 10 to 100 requests per second. Get a free key from [openalex.org](https://openalex.org).

Enter the key and click **Save Settings**. The searcher is re-initialized immediately with the new key.

## Polite Pool Email

This email is included in the `User-Agent` header when fetching BibTeX from doi.org and Crossref. It places you in the "polite pool" for content negotiation, improving reliability.

## Theme

Switch between:

- **System** — follows your OS theme (default)
- **Light** — always light mode
- **Dark** — always dark mode

The preference is persisted in the database and restored on next launch.

## Desktop Shortcut

Click **Create Desktop Shortcut** to create a `.desktop` file (Linux) or equivalent launcher. This uses `pyshortcuts` under the hood.
