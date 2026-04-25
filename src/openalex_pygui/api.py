"""API layer: OpenAlex search and BibTeX retrieval."""

import httpx
from openalexpy import WorksSync, config
from openalexpy.entities import Work


class OpenAlexSearcher:
    """Searches OpenAlex and converts results to plain dicts ready for the DB."""

    def __init__(self, api_key: str | None = None, email: str | None = None):
        if api_key:
            config.api_key = api_key
        self._email = email

    def search(
        self,
        query: str,
        *,
        limit: int = 25,
        sort: str = "relevance_score:desc",
    ) -> list[dict]:
        """Return a list of work dicts matching *query*."""
        works = WorksSync()
        results: list[Work] = works.search(query).sort(sort).get(per_page=limit)

        out: list[dict] = []
        for w in results:
            authors = []
            if hasattr(w, "authorships") and w.authorships:
                for i, a in enumerate(w.authorships):
                    author_info = a.get("author", {})
                    authors.append(
                        {
                            "id": author_info.get("id", ""),
                            "name": author_info.get("display_name", ""),
                            "orcid": author_info.get("orcid"),
                            "position": i,
                        }
                    )

            keywords = []
            if hasattr(w, "keywords") and w.keywords:
                keywords = [kw.get("keyword", "") for kw in w.keywords if kw.get("keyword")]

            relationships = []
            if hasattr(w, "related_works") and w.related_works:
                relationships = [
                    {"id": rid, "type": "related"} for rid in w.related_works
                ]
            if hasattr(w, "referenced_works") and w.referenced_works:
                relationships.extend(
                    {"id": rid, "type": "references"} for rid in w.referenced_works
                )

            abstract = ""
            if hasattr(w, "abstract"):
                abstract = w.abstract or ""

            out.append(
                {
                    "id": w.id if hasattr(w, "id") else "",
                    "doi": w.doi if hasattr(w, "doi") else None,
                    "title": w.title if hasattr(w, "title") else "",
                    "publication_year": w.publication_year if hasattr(w, "publication_year") else None,
                    "type": w.type if hasattr(w, "type") else None,
                    "cited_by_count": w.cited_by_count if hasattr(w, "cited_by_count") else 0,
                    "abstract": abstract,
                    "authors": authors,
                    "keywords": keywords,
                    "relationships": relationships,
                }
            )
        return out

    def fetch_bibtex(self, doi: str) -> str | None:
        """Fetch BibTeX for a DOI via content negotiation, Crossref as fallback."""
        headers: dict[str, str] = {"Accept": "application/x-bibtex"}
        if self._email:
            headers["User-Agent"] = (
                f"OpenAlex-PyGUI/0.1 (mailto:{self._email})"
            )

        # Primary: doi.org content negotiation
        try:
            r = httpx.get(
                f"https://doi.org/{doi}",
                headers=headers,
                follow_redirects=True,
                timeout=15,
            )
            if r.status_code == 200 and "@" in r.text:
                return r.text.strip()
        except httpx.HTTPError:
            pass

        # Fallback: Crossref transform API
        try:
            r = httpx.get(
                f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex",
                headers=headers,
                timeout=15,
            )
            if r.status_code == 200 and "@" in r.text:
                return r.text.strip()
        except httpx.HTTPError:
            pass

        return None
