"""
Generic pager utility.

Some list endpoints accept page/size parameters and return items plus paging metadata.
This helper lets you pass any generated sync function and iterate through results
without repeating boilerplate.

Example usage (pseudo):
    from rest_api_polarion_client.api.documents.get_documents import sync as list_docs

    for page in paged(list_docs, client=client, project_id="X", page_size=100):
        for doc in page.items:
            ...
"""

from __future__ import annotations
from typing import Any, Callable, Dict, Iterator


def paged(
    fn: Callable[..., Any],
    *,
    page_param: str = "page",
    size_param: str = "page_size",
    start: int = 0,
    page_size: int = 100,
    **kwargs: Any,
) -> Iterator[Any]:
    """
    Call `fn` repeatedly with page/size parameters until it returns an empty page.

    We don't assume a specific return shape; the caller can adapt to their models.
    """
    page = start
    while True:
        call_kwargs: Dict[str, Any] = dict(kwargs)
        call_kwargs[page_param] = page
        call_kwargs[size_param] = page_size
        result = fn(**call_kwargs)  # typically returns a parsed model or Response

        # Very generic stop condition; adjust per your actual list model later.
        # If "result" is a dataclass/model with `.items` or `.data`, adapt here.
        if result is None:
            break

        # Yield the whole page so callers can inspect metadata too.
        yield result

        # Try to detect empty page; if unknown, let the caller `break` externally.
        try:
            items = getattr(result, "items", None) or getattr(result, "data", None)
            if items is not None and len(items) == 0:
                break
        except Exception:
            # If we can't introspect items, stop after one page by default.
            break

        page += 1
