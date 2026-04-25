"""OpenAlex Research Manager — Flet desktop application."""

import flet as ft

from openalex_pygui.api import OpenAlexSearcher, _SORT_OPTIONS
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
        self._search_selected: set[str] = set()
        self._lib_selected: set[str] = set()

        page.title = "OpenAlex Research Manager"
        saved_theme = self.db.get_setting("theme_mode", "system")
        page.theme_mode = {
            "light": ft.ThemeMode.LIGHT,
            "dark": ft.ThemeMode.DARK,
        }.get(saved_theme, ft.ThemeMode.SYSTEM)
        page.padding = 20
        page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────

    def _build_ui(self):
        self.page.appbar = ft.AppBar(
            title=ft.Text("OpenAlex Research Manager"),
            bgcolor=ft.Colors.SURFACE,
        )
        self.page.add(
            ft.Tabs(
                selected_index=0,
                length=3,
                animation_duration=200,
                content=ft.Column(
                    controls=[
                        ft.TabBar(
                            tabs=[
                                ft.Tab(label="Search", icon=ft.Icons.SEARCH),
                                ft.Tab(label="Library", icon=ft.Icons.LIBRARY_BOOKS),
                                ft.Tab(label="Settings", icon=ft.Icons.SETTINGS),
                            ],
                        ),
                        ft.TabBarView(
                            controls=[
                                self._search_tab(),
                                self._library_tab(),
                                self._settings_tab(),
                            ],
                            expand=True,
                        ),
                    ],
                    expand=True,
                ),
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
        self._sort_dropdown = ft.Dropdown(
            options=[ft.DropdownOption(key=k) for k in _SORT_OPTIONS],
            value="Relevance",
            width=160,
        )
        self._limit_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption(key="10"),
                ft.DropdownOption(key="25"),
                ft.DropdownOption(key="50"),
            ],
            value="25",
            width=90,
            label="Results",
        )
        self._mode_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption(key="Classical"),
                ft.DropdownOption(key="Semantic"),
            ],
            value="Classical",
            width=140,
            label="Mode",
        )
        self._results_list = ft.ListView(expand=True, spacing=4)
        self._status = ft.Text()
        self._select_all_search = ft.Checkbox(label="Select all", on_change=self._toggle_select_all_search)
        self._save_selected_btn = ft.FilledButton(
            "Save Selected", on_click=self._save_selected, disabled=True
        )
        self._search_batch_row = ft.Row(
            controls=[self._select_all_search, self._save_selected_btn],
            visible=False,
        )

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self._search_field,
                        ft.FilledButton("Search", on_click=lambda _: self._do_search()),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Text("Sort:", size=12),
                        self._sort_dropdown,
                        self._limit_dropdown,
                        self._mode_dropdown,
                    ],
                    spacing=8,
                ),
                self._status,
                self._search_batch_row,
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
        self._search_selected.clear()
        self.page.update()

        sort_key = self._sort_dropdown.value or "Relevance"
        sort_value = _SORT_OPTIONS.get(sort_key, "relevance_score:desc")
        limit = int(self._limit_dropdown.value or "25")
        semantic = (self._mode_dropdown.value == "Semantic")

        try:
            self._search_results = self.searcher.search(
                query, sort=sort_value, limit=limit, semantic=semantic
            )
            self._status.value = f"{len(self._search_results)} results"
        except Exception as exc:
            self._status.value = f"Error: {exc}"
            self._search_results = []

        self._search_batch_row.visible = bool(self._search_results)
        self._select_all_search.value = False
        self._save_selected_btn.disabled = True
        self._render_search_results()
        self.page.update()

    def _toggle_select_all_search(self, e):
        checked = e.control.value
        if checked:
            self._search_selected = {w["id"] for w in self._search_results}
        else:
            self._search_selected.clear()
        self._save_selected_btn.disabled = not self._search_selected
        self._render_search_results()
        self.page.update()

    def _toggle_search_item(self, work_id: str, checked: bool):
        if checked:
            self._search_selected.add(work_id)
        else:
            self._search_selected.discard(work_id)
        self._save_selected_btn.disabled = not self._search_selected
        all_selected = len(self._search_selected) == len(self._search_results)
        self._select_all_search.value = all_selected
        self.page.update()

    def _save_selected(self, _):
        for work in self._search_results:
            if work["id"] in self._search_selected and not self.db.work_exists(work["id"]):
                self._save_work_to_db(work)
        self._search_selected.clear()
        self._select_all_search.value = False
        self._save_selected_btn.disabled = True
        self._render_search_results()
        self.page.update()

    def _render_search_results(self):
        self._results_list.controls.clear()
        for work in self._search_results:
            saved = self.db.work_exists(work["id"])
            selected = work["id"] in self._search_selected

            cb = ft.Checkbox(
                value=selected,
                disabled=saved,
                on_change=lambda e, wid=work["id"]: self._toggle_search_item(wid, e.control.value),
            )
            title_line = ft.Text(
                work["title"],
                weight=ft.FontWeight.BOLD,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
                expand=True,
            )

            meta_parts = []
            if work.get("publication_year"):
                meta_parts.append(str(work["publication_year"]))
            if work.get("cited_by_count"):
                meta_parts.append(f"Cited: {work['cited_by_count']}")

            authors = work.get("authors") or []
            if authors:
                author_str = ", ".join(a["name"] for a in authors[:3])
                if len(authors) > 3:
                    author_str += " et al."
                meta_parts.append(author_str)

            journal = work.get("journal") or ""
            if journal:
                meta_parts.append(journal)

            meta = ft.Text(" | ".join(meta_parts), size=12, color=ft.Colors.ON_SURFACE_VARIANT)

            doi = work.get("doi") or ""
            doi_link = ft.Text()
            if doi:
                doi_link = ft.TextButton(
                    content=doi,
                    url=doi,
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(size=11, color=ft.Colors.BLUE),
                        padding=0,
                    ),
                )

            abstract = work.get("abstract") or ""
            abstract_text = ft.Text(
                abstract[:300] + "..." if len(abstract) > 300 else abstract,
                size=12,
                max_lines=3,
                overflow=ft.TextOverflow.ELLIPSIS,
                italic=True,
            )

            btn = ft.FilledButton(
                "Saved" if saved else "Save",
                disabled=saved,
                on_click=lambda _, w=work: self._save_work(w),
            )

            right_col = ft.Column(
                [btn],
                alignment=ft.MainAxisAlignment.START,
                width=80,
            )

            card_body = [title_line, meta]
            if doi:
                card_body.append(doi_link)
            if abstract:
                card_body.append(abstract_text)

            self._results_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            controls=[
                                cb,
                                ft.Column(card_body, spacing=4, expand=True),
                                right_col,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        padding=12,
                    )
                )
            )

    def _save_work_to_db(self, work: dict):
        self.db.add_work(
            openalex_id=work["id"],
            title=work["title"],
            doi=work.get("doi"),
            publication_year=work.get("publication_year"),
            work_type=work.get("type"),
            cited_by_count=work.get("cited_by_count", 0),
            abstract=work.get("abstract"),
            journal=work.get("journal"),
            authors=work.get("authors"),
            keywords=work.get("keywords"),
            relationships=work.get("relationships"),
        )

    def _save_work(self, work: dict):
        self._save_work_to_db(work)
        self._render_search_results()
        self.page.update()

    # ── Library tab ────────────────────────────────────────────────────

    def _library_tab(self) -> ft.Control:
        self._lib_search = ft.TextField(
            hint_text="Filter library...",
            on_submit=lambda _: self._refresh_library(),
            expand=True,
        )
        self._lib_list = ft.ListView(expand=True, spacing=4)
        self._lib_status = ft.Text()

        refresh_btn = ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: self._refresh_library())
        self._lib_select_all = ft.Checkbox(label="Select all", on_change=self._toggle_select_all_lib)
        self._export_selected_btn = ft.FilledButton(
            "Export Selected BibTeX", on_click=self._export_bibtex, disabled=True
        )
        self._fetch_all_bibtex_btn = ft.OutlinedButton(
            "Fetch All BibTeX", on_click=self._fetch_all_bibtex
        )

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[self._lib_search, refresh_btn],
                ),
                ft.Row(
                    controls=[self._lib_select_all, self._export_selected_btn, self._fetch_all_bibtex_btn],
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
        self._lib_selected.clear()
        self._lib_select_all.value = False
        self._export_selected_btn.disabled = True
        self._lib_list.controls.clear()

        for w in works:
            authors = self.db.get_authors_for_work(w["id"])
            author_str = ", ".join(a["name"] for a in authors[:4])
            if len(authors) > 4:
                author_str += " et al."

            cb = ft.Checkbox(
                value=False,
                on_change=lambda e, wid=w["id"]: self._toggle_lib_item(wid, e.control.value),
            )

            meta_parts = []
            if w.get("publication_year"):
                meta_parts.append(str(w["publication_year"]))
            if w.get("cited_by_count"):
                meta_parts.append(f"Cited: {w['cited_by_count']}")
            if author_str:
                meta_parts.append(author_str)
            journal = w.get("journal") or ""
            if journal:
                meta_parts.append(journal)
            has_bib = "BibTeX" if w.get("bibtex") else ""
            if has_bib:
                meta_parts.append(has_bib)
            meta = ft.Text(" | ".join(meta_parts), size=12, color=ft.Colors.ON_SURFACE_VARIANT)

            edit_btn = ft.IconButton(
                ft.Icons.EDIT_OUTLINED,
                tooltip="Edit notes / abstract",
                on_click=lambda _, wid=w["id"]: self._open_edit_dialog(wid),
            )
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
                                cb,
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
                                edit_btn,
                                remove_btn,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        padding=12,
                    )
                )
            )

        self.page.update()

    def _toggle_select_all_lib(self, e):
        checked = e.control.value
        if checked:
            self._lib_selected = {
                w["id"] for w in self.db.list_works()
            }
        else:
            self._lib_selected.clear()
        self._export_selected_btn.disabled = not self._lib_selected
        self._refresh_library()

    def _toggle_lib_item(self, work_id: str, checked: bool):
        if checked:
            self._lib_selected.add(work_id)
        else:
            self._lib_selected.discard(work_id)
        self._export_selected_btn.disabled = not self._lib_selected
        self.page.update()

    def _remove_work(self, work_id: str):
        self.db.remove_work(work_id)
        self._lib_selected.discard(work_id)
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
        self._refresh_library()

    def _fetch_all_bibtex(self, _):
        works = self.db.list_works()
        fetched = 0
        for w in works:
            if not w.get("bibtex") and w.get("doi"):
                bibtex = self.searcher.fetch_bibtex(w["doi"])
                if bibtex:
                    self.db.set_bibtex(w["id"], bibtex)
                    fetched += 1
        self._lib_status.value = f"Fetched {fetched} BibTeX entries."
        self._refresh_library()

    async def _export_bibtex(self, _):
        if self._lib_selected:
            bib = self.db.export_bibtex(ids=list(self._lib_selected))
        else:
            bib = self.db.export_bibtex()

        if not bib:
            self._lib_status.value = "No BibTeX entries to export. Fetch BibTeX for works first."
            self.page.update()
            return

        path = await ft.FilePicker().save_file(
            file_name="library.bib",
            allowed_extensions=["bib"],
        )
        if path:
            with open(path, "w") as f:
                f.write(bib)
            self._lib_status.value = f"Exported to {path}"
            self.page.update()

    def _open_edit_dialog(self, work_id: str):
        work = self.db.get_work(work_id)
        if not work:
            return

        notes_field = ft.TextField(
            label="Notes",
            value=work.get("notes") or "",
            multiline=True,
            min_lines=3,
            max_lines=8,
        )
        abstract_field = ft.TextField(
            label="Abstract",
            value=work.get("abstract") or "",
            multiline=True,
            min_lines=3,
            max_lines=8,
        )

        def save_edit(_):
            self.db.set_notes(work_id, notes_field.value or "")
            self.db.set_abstract(work_id, abstract_field.value or "")
            self.page.pop_dialog()
            self._refresh_library()

        def close_edit(_):
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            title=ft.Text(f"Edit: {work['title'][:60]}"),
            content=ft.Column(
                controls=[notes_field, abstract_field],
                width=500,
                height=400,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_edit),
                ft.FilledButton("Save", on_click=save_edit),
            ],
        )
        self.page.show_dialog(dlg)

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
        self._theme_dropdown = ft.Dropdown(
            label="Theme",
            options=[
                ft.DropdownOption(key="system"),
                ft.DropdownOption(key="light"),
                ft.DropdownOption(key="dark"),
            ],
            value=self.db.get_setting("theme_mode", "system"),
            width=200,
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
            theme = self._theme_dropdown.value or "system"
            self.db.set_setting("theme_mode", theme)
            self.page.theme_mode = {
                "light": ft.ThemeMode.LIGHT,
                "dark": ft.ThemeMode.DARK,
            }.get(theme, ft.ThemeMode.SYSTEM)
            self._settings_status.value = "Settings saved."
            self.page.update()

        self._settings_status = ft.Text()

        from openalex_pygui.utils import create_desktop_shortcut

        return ft.Column(
            controls=[
                api_key_field,
                email_field,
                self._theme_dropdown,
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


def main(page: ft.Page):
    app = App(page)
    page.on_disconnect = lambda _: app.teardown()


def app_entry():
    ft.app(target=main)


if __name__ == "__main__":
    app_entry()
