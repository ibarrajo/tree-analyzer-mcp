"""Generate FamilySearch URLs for persons and records."""


def person_url(person_id: str) -> str:
    """Generate FamilySearch person details URL."""
    return f"https://www.familysearch.org/tree/person/details/{person_id}"


def search_url(given_name: str = "", surname: str = "", birth_year: str = "", birth_place: str = "") -> str:
    """Generate FamilySearch search URL with pre-filled parameters."""
    params = []
    if given_name:
        params.append(f"givenName={given_name}")
    if surname:
        params.append(f"surname={surname}")
    if birth_year:
        params.append(f"birthLikeDate={birth_year}")
    if birth_place:
        params.append(f"birthLikePlace={birth_place}")

    if params:
        return f"https://www.familysearch.org/search/tree/results?{'&'.join(params)}"
    return "https://www.familysearch.org/search/tree/results"


def record_search_url(collection_id: str = "", given_name: str = "", surname: str = "") -> str:
    """Generate FamilySearch historical record search URL."""
    params = []
    if given_name:
        params.append(f"givenName={given_name}")
    if surname:
        params.append(f"surname={surname}")
    if collection_id:
        params.append(f"collectionId={collection_id}")

    if params:
        return f"https://www.familysearch.org/search/record/results?{'&'.join(params)}"
    return "https://www.familysearch.org/search/record/results"
