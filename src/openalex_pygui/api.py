"""API layer: OpenAlex search and BibTeX retrieval."""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from openalexpy import WorksSync, config
from openalexpy.entities import Work
from openalexpy.exceptions import NotFoundError

_SORT_OPTIONS = {
    "Relevance": "relevance_score:desc",
    "Most cited": "cited_by_count:desc",
    "Newest first": "publication_year:desc",
    "Oldest first": "publication_year:asc",
}


def _parse_sort(sort_value: str) -> dict:
    field, direction = sort_value.split(":")
    return {field: direction}


def work_to_dict(w: Work) -> dict:
    """Convert a Work entity to a plain dict for the DB and UI."""
    authors = []
    if hasattr(w, "authorships") and w.authorships:
        for i, a in enumerate(w.authorships):
            authors.append(
                {
                    "id": a.author.id or "",
                    "name": a.author.display_name or "",
                    "orcid": a.author.orcid,
                    "position": i,
                }
            )

    keywords = []
    if hasattr(w, "keywords") and w.keywords:
        keywords = [kw.display_name for kw in w.keywords if kw.display_name]

    relationships = []
    if hasattr(w, "related_works") and w.related_works:
        relationships = [{"id": rid, "type": "related"} for rid in w.related_works]
    if hasattr(w, "referenced_works") and w.referenced_works:
        relationships.extend(
            {"id": rid, "type": "references"} for rid in w.referenced_works
        )

    abstract = ""
    if hasattr(w, "abstract"):
        abstract = w.abstract or ""

    journal = ""
    if hasattr(w, "primary_location") and w.primary_location:
        loc = w.primary_location
        if hasattr(loc, "source") and loc.source:
            journal = loc.source.display_name or ""

    return {
        "id": w.id if hasattr(w, "id") else "",
        "doi": w.doi if hasattr(w, "doi") else None,
        "title": w.title if hasattr(w, "title") else "",
        "publication_year": w.publication_year if hasattr(w, "publication_year") else None,
        "type": w.type if hasattr(w, "type") else None,
        "cited_by_count": w.cited_by_count if hasattr(w, "cited_by_count") else 0,
        "relevance_score": w.relevance_score if hasattr(w, "relevance_score") else None,
        "abstract": abstract,
        "journal": journal,
        "authors": authors,
        "keywords": keywords,
        "relationships": relationships,
    }


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
        semantic: bool = False,
        scope: str = "default",
    ) -> list[dict]:
        ws = WorksSync()
        if semantic:
            ws = ws.similar(query)
            if sort != "relevance_score:desc":
                q = ws.sort(**_parse_sort(sort))
                ws._params = q.params
        elif scope == "title":
            q = ws.search_filter(title=query).sort(**_parse_sort(sort))
            ws._params = q.params
        elif scope == "fulltext":
            q = ws.search_filter(fulltext=query).sort(**_parse_sort(sort))
            ws._params = q.params
        else:
            q = ws.search(query).sort(**_parse_sort(sort))
            ws._params = q.params
        results: list[Work] = ws.get(per_page=limit)
        return [work_to_dict(w) for w in results]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=0.5, max=8, jitter=1))
    def _fetch_single_work(self, openalex_id: str) -> dict:
        w = WorksSync().get_by_id(openalex_id)
        return work_to_dict(w)

    def fetch_work_by_id(self, openalex_id: str) -> dict | None:
        try:
            return self._fetch_single_work(openalex_id)
        except NotFoundError:
            return None
        except Exception:
            return None

    def fetch_bibtex(self, doi: str) -> str | None:
        headers: dict[str, str] = {"Accept": "application/x-bibtex"}
        if self._email:
            headers["User-Agent"] = (
                f"OpenAlex-PyGUI/0.1 (mailto:{self._email})"
            )

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
