"""Desktop integration helpers."""

import sys
from pathlib import Path

from pyshortcuts import make_shortcut


def create_desktop_shortcut(name: str = "OpenAlex Research Manager") -> Path | None:
    """Create a desktop / start-menu shortcut. Returns the shortcut path or None."""
    try:
        entry_point = str(Path(sys.executable).parent / "openalex-pygui")
        make_shortcut(entry_point, name=name)
        return Path(entry_point)
    except Exception:
        return None
