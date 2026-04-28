# Getting Started

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```bash
git clone https://github.com/your-username/openalex-pygui.git
cd openalex-pygui
uv sync
```

## Running the App

```bash
uv run openalex-pygui
```

This launches the Flet desktop application with three tabs: **Search**, **Library**, and **Settings**.

## Configuring the API Key

OpenAlex works without an API key, but adding one increases your rate limit from 10 to 100 requests per second.

1. Go to the **Settings** tab
2. Enter your OpenAlex API key in the "OpenAlex API Key" field
3. Click **Save Settings**

You can obtain a free API key from [openalex.org](https://openalex.org).

## Polite Pool Email

For BibTeX retrieval via doi.org and Crossref, providing an email address is recommended. This puts you in the "polite pool" for content negotiation.

1. Enter your email in the **Polite Pool Email** field on the Settings tab
2. Click **Save Settings**

## Theme

Switch between system, light, and dark mode from the **Settings** tab using the **Theme** dropdown. The preference is persisted across sessions.

## Desktop Shortcut

Click **Create Desktop Shortcut** on the Settings tab to add a launcher to your desktop.
