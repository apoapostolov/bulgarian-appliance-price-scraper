from __future__ import annotations

from bs4 import BeautifulSoup

from .config import Category


def discover_categories(html: str, allowed_texts: set[str]) -> list[Category]:
    soup = BeautifulSoup(html, "html.parser")
    categories: list[Category] = []
    seen_paths: set[str] = set()

    for link in soup.select("a[href]"):
        text = link.get_text(" ", strip=True)
        href = link.get("href", "").strip()
        if text not in allowed_texts or not href.startswith("/produkti/"):
            continue
        path = href.split("?", 1)[0]
        if path in seen_paths:
            continue
        seen_paths.add(path)
        categories.append(Category(path=path, name=text))

    return categories
