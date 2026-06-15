from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import urlsplit

from ..constants import DEFAULT_HELP_LINKS


HelpLink = Mapping[str, Any]


def normalize_link(link: HelpLink | None) -> dict[str, str]:
    """Return a clean help-link dictionary with stable keys."""
    source = link or {}
    return {
        "name": str(source.get("name") or "").strip(),
        "url": normalize_url(str(source.get("url") or "")),
    }


def normalize_url(url: str) -> str:
    clean_url = str(url or "").strip()
    if not clean_url:
        return ""
    parsed = urlsplit(clean_url)
    if not parsed.scheme:
        clean_url = f"https://{clean_url}"
        parsed = urlsplit(clean_url)
    if parsed.scheme not in {"http", "https"}:
        return clean_url
    return clean_url


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


def display_url(link: HelpLink) -> str:
    return normalize_link(link)["url"]


def duplicate_url_index(
    links: Iterable[HelpLink] | None,
    url: str,
    *,
    ignore_index: int | None = None,
) -> int | None:
    target = normalize_url(url).casefold()
    if not target:
        return None
    for index, link in enumerate(normalize_links(links)):
        if ignore_index is not None and index == ignore_index:
            continue
        if link["url"].casefold() == target:
            return index
    return None


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
