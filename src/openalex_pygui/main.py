"""OpenAlex Research Manager — Flet desktop application."""

import flet as ft

from openalex_pygui.api import OpenAlexSearcher
from openalex_pygui.db import Database


class App:
    """Main application class encapsulating all UI and logic."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.db = Database()
        self.searcher = OpenAlexSearcher(
            api_key=self.db.get_setting("api_key"),
            email=self.db.get_setting("email"),
        )
        self._search_results: list[dict] = []

        page.title = "OpenAlex Research Manager"
        page.theme_mode = ft.ThemeMode.SYSTEM
        page.padding = 20
        page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────

    def _build_ui(self):
        self.page.appbar = ft.AppBar(
            title=ft.Text("OpenAlex Research Manager"),
            bgcolor=ft.Colors.SURFACE_VARIANT,
        )
        self.page.add(
            ft.Tabs(
                selected_index=0,
                animation_duration=200,
                tabs=[
                    ft.Tab(text="Search", icon=ft.Icons.SEARCH, content=self._search_tab()),
                    ft.Tab(text="Library", icon=ft.Icons.LIBRARY_BOOKS, content=self._library_tab()),
                    ft.Tab(text="Settings", icon=ft.Icons.SETTINGS, content=self._settings_tab()),
                ],
                expand=True,
            )
        )

    # ── Search tab ─────────────────────────────────────────────────────

    def _search_tab(self) -> ft.Control:
        self._search_field = ft.TextField(
            hint_text="Search works...",
            autofocus=True,
            expand=True,
            on_submit=lambda _: self._do_search(),
        )
        self._results_list = ft.ListView(expand=True, spacing=4)
        self._status = ft.Text()

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self._search_field,
                        ft.FilledButton("Search", on_click=lambda _: self._do_search()),
                    ]
                ),
                self._status,
                ft.Divider(),
                self._results_list,
            ],
            expand=True,
        )

    def _do_search(self):
        query = self._search_field.value
        if not query:
            return
        self._status.value = "Searching..."
        self.page.update()

        try:
            self._search_results = self.searcher.search(query)
            self._status.value = f"{len(self._search_results)} results"
        except Exception as exc:
            self._status.value = f"Error: {exc}"
            self._search_results = []

        self._render_search_results()
        self.page.update()

    def _render_search_results(self):
        self._results_list.controls.clear()
        for work in self._search_results:
            saved = self.db.work_exists(work["id"])
            title_line = ft.Text(
                work["title"],
                weight=ft.FontWeight.BOLD,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
            meta_parts = []
            if work.get("publication_year"):
                meta_parts.append(str(work["publication_year"]))
            if work.get("cited_by_count"):
                meta_parts.append(f"Cited: {work['cited_by_count']}")
            if work.get("doi"):
                meta_parts.append(work["doi"])
            meta = ft.Text(" | ".join(meta_parts), size=12, color=ft.Colors.ON_SURFACE_VARIANT)

            abstract = work.get("abstract") or ""
            abstract_text = ft.Text(
                abstract[:300] + "..." if len(abstract) > 300 else abstract,
                size=12,
                max_lines=3,
                overflow=ft.TextOverflow.ELLIPSIS,
                italic=True,
            )

            btn_text = "Saved" if saved else "Save"
            btn = ft.FilledButton(
                btn_text,
                disabled=saved,
                on_click=lambda _, w=work: self._save_work(w),
            )

            card_content = [title_line, meta]
            if abstract:
                card_content.append(abstract_text)
            card_content.append(btn)

            self._results_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(card_content, spacing=4),
                        padding=12,
                    )
                )
            )

    def _save_work(self, work: dict):
        self.db.add_work(
            openalex_id=work["id"],
            title=work["title"],
            doi=work.get("doi"),
            publication_year=work.get("publication_year"),
            work_type=work.get("type"),
            cited_by_count=work.get("cited_by_count", 0),
            abstract=work.get("abstract"),
            authors=work.get("authors"),
            keywords=work.get("keywords"),
            relationships=work.get("relationships"),
        )
        self._render_search_results()
        self.page.update()

    # ── Library tab ────────────────────────────────────────────────────

    def _library_tab(self) -> ft.Control:
        self._lib_search = ft.TextField(
            hint_text="Filter library...",
            on_submit=lambda _: self._refresh_library(),
        )
        self._lib_list = ft.ListView(expand=True, spacing=4)
        self._lib_status = ft.Text()

        refresh_btn = ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: self._refresh_library())
        export_btn = ft.FilledButton("Export BibTeX", on_click=self._export_bibtex)

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[self._lib_search, refresh_btn, export_btn],
                    alignment=ft.MainAxisAlignment.START,
                ),
                self._lib_status,
                ft.Divider(),
                self._lib_list,
            ],
            expand=True,
        )

    def _refresh_library(self):
        search = self._lib_search.value or None
        works = self.db.list_works(search=search)
        self._lib_status.value = f"{len(works)} works in library"
        self._lib_list.controls.clear()

        for w in works:
            authors = self.db.get_authors_for_work(w["id"])
            author_str = ", ".join(a["name"] for a in authors[:4])
            if len(authors) > 4:
                author_str += " et al."

            meta_parts = []
            if w.get("publication_year"):
                meta_parts.append(str(w["publication_year"]))
            if w.get("cited_by_count"):
                meta_parts.append(f"Cited: {w['cited_by_count']}")
            if author_str:
                meta_parts.append(author_str)
            meta = ft.Text(" | ".join(meta_parts), size=12, color=ft.Colors.ON_SURFACE_VARIANT)

            remove_btn = ft.IconButton(
                ft.Icons.DELETE_OUTLINE,
                tooltip="Remove",
                on_click=lambda _, wid=w["id"]: self._remove_work(wid),
            )

            bibtex_btn = ft.IconButton(
                ft.Icons.DESCRIPTION_OUTLINED,
                tooltip="Fetch BibTeX",
                on_click=lambda _, wid=w["id"]: self._fetch_bibtex(wid),
            )

            self._lib_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Column(
                                    [
                                        ft.Text(
                                            w["title"],
                                            weight=ft.FontWeight.BOLD,
                                            max_lines=2,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        meta,
                                    ],
                                    spacing=4,
                                    expand=True,
                                ),
                                bibtex_btn,
                                remove_btn,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=12,
                    )
                )
            )

        self.page.update()

    def _remove_work(self, work_id: str):
        self.db.remove_work(work_id)
        self._refresh_library()

    def _fetch_bibtex(self, work_id: str):
        work = self.db.get_work(work_id)
        if not work or not work.get("doi"):
            self._lib_status.value = "No DOI available for this work."
            self.page.update()
            return

        bibtex = self.searcher.fetch_bibtex(work["doi"])
        if bibtex:
            self.db.set_bibtex(work_id, bibtex)
            self._lib_status.value = "BibTeX fetched and cached."
        else:
            self._lib_status.value = "Could not retrieve BibTeX."
        self.page.update()

    def _export_bibtex(self):
        bib = self.db.export_bibtex()
        if not bib:
            self._lib_status.value = "No BibTeX entries to export. Fetch BibTeX for individual works first."
            self.page.update()
            return

        path = self.page.get_save_path(
            file_name="library.bib",
            allowed_extensions=["bib"],
        )
        if path:
            with open(path, "w") as f:
                f.write(bib)
            self._lib_status.value = f"Exported to {path}"
            self.page.update()

    # ── Settings tab ───────────────────────────────────────────────────

    def _settings_tab(self) -> ft.Control:
        api_key_field = ft.TextField(
            label="OpenAlex API Key",
            value=self.db.get_setting("api_key") or "",
            password=True,
            can_reveal_password=True,
        )
        email_field = ft.TextField(
            label="Polite Pool Email",
            value=self.db.get_setting("email") or "",
            hint_text="Used for Crossref/doi.org BibTeX retrieval",
        )

        def save_settings(_):
            if api_key_field.value:
                self.db.set_setting("api_key", api_key_field.value)
                self.searcher = OpenAlexSearcher(
                    api_key=api_key_field.value,
                    email=email_field.value or None,
                )
            else:
                self.searcher = OpenAlexSearcher(email=email_field.value or None)
            if email_field.value:
                self.db.set_setting("email", email_field.value)
                self.searcher._email = email_field.value
            self._settings_status.value = "Settings saved."
            self.page.update()

        self._settings_status = ft.Text()

        from openalex_pygui.utils import create_desktop_shortcut

        return ft.Column(
            controls=[
                api_key_field,
                email_field,
                ft.Row(
                    controls=[
                        ft.FilledButton("Save Settings", on_click=save_settings),
                        ft.OutlinedButton(
                            "Create Desktop Shortcut",
                            on_click=lambda _: (
                                setattr(
                                    self._settings_status,
                                    "value",
                                    "Shortcut created." if create_desktop_shortcut() else "Failed to create shortcut.",
                                ),
                                self.page.update(),
                            ),
                        ),
                    ]
                ),
                self._settings_status,
            ],
            spacing=16,
            width=500,
        )

    # ── Cleanup ────────────────────────────────────────────────────────

    def teardown(self):
        self.db.close()


def main():
    def app_entry(page: ft.Page):
        app = App(page)
        page.on_disconnect = lambda _: app.teardown()

    ft.app(target=app_entry)


if __name__ == "__main__":
    main()
