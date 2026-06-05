from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ..constants import DEFAULT_HELP_LINKS


HelpLink = Mapping[str, Any]


def normalize_link(link: HelpLink | None) -> dict[str, str]:
    """Return a clean help-link dictionary with stable keys."""
    source = link or {}
    return {
        "name": str(source.get("name") or "").strip(),
        "url": str(source.get("url") or "").strip(),
    }


def normalize_links(links: Iterable[HelpLink] | None) -> list[dict[str, str]]:
    """Return clean links, dropping completely empty entries."""
    clean_links: list[dict[str, str]] = []
    for link in links or []:
        clean_link = normalize_link(link)
        if clean_link["name"] or clean_link["url"]:
            clean_links.append(clean_link)
    return clean_links


def display_name(link: HelpLink) -> str:
    clean_link = normalize_link(link)
    return clean_link["name"] or clean_link["url"] or "Link"


def default_links() -> list[dict[str, str]]:
    return normalize_links(DEFAULT_HELP_LINKS)


def merge_default_links(links: Iterable[HelpLink] | None) -> list[dict[str, str]]:
    updated = normalize_links(links)
    seen_urls = {item["url"].casefold() for item in updated if item["url"]}
    for default_link in default_links():
        url_key = default_link["url"].casefold()
        if url_key not in seen_urls:
            updated.append(default_link)
            seen_urls.add(url_key)
    return updated


def add_link(
    links: Iterable[HelpLink] | None, link: HelpLink
) -> list[dict[str, str]]:
    updated = normalize_links(links)
    updated.append(normalize_link(link))
    return updated


def replace_link(
    links: Iterable[HelpLink] | None, index: int, link: HelpLink
) -> list[dict[str, str]]:
    updated = normalize_links(links)
    if 0 <= index < len(updated):
        updated[index] = normalize_link(link)
    return updated


def delete_link(links: Iterable[HelpLink] | None, index: int) -> list[dict[str, str]]:
    updated = normalize_links(links)
    if 0 <= index < len(updated):
        updated.pop(index)
    return updated


def move_link(
    links: Iterable[HelpLink] | None, index: int, delta: int
) -> tuple[list[dict[str, str]], int]:
    updated = normalize_links(links)
    new_index = index + delta
    if 0 <= index < len(updated) and 0 <= new_index < len(updated):
        updated[index], updated[new_index] = updated[new_index], updated[index]
        return updated, new_index
    return updated, index
