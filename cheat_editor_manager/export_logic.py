from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

SWITCH_TID_LINE_RE = re.compile(r"(?:\bTID\b|\bTITLEID\b)\s*[:=]\s*([^\r\n]+)", re.IGNORECASE)
SWITCH_BID_LINE_RE = re.compile(r"(?:\bBIDS?\b|\bBUILDIDS?\b)\s*[:=]\s*([^\r\n]+)", re.IGNORECASE)
SWITCH_TID_VALUE_RE = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])")
SWITCH_BID_VALUE_RE = re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{32}|[0-9a-f]{16})(?![0-9a-f])")
ATMOSPHERE_SECTION_RE = re.compile(r"^\s*[\[{].+[\]}]\s*$")
ATMOSPHERE_CODE_RE = re.compile(r"^\s*[0-9A-Fa-f]{8}(?:\s+[0-9A-Fa-f]{8}){1,4}\s*$")
ATMOSPHERE_SUBDIR_MARKER = "atmosphere/contents/"


def clean_hex(s: str) -> str:
    """Return uppercase hex chars only."""
    return "".join(ch for ch in (s or "").strip() if ch.lower() in "0123456789abcdef").upper()


def split_bids(bids: str) -> List[str]:
    parts: List[str] = []
    for raw in (bids or "").replace("\n", ",").replace(" ", ",").split(","):
        value = raw.strip()
        if value:
            parts.append(value)
    return parts


def normalize_bids(bid_text: str, *, allow_invalid: bool = False) -> List[str]:
    bids: List[str] = []
    seen = set()
    for raw in split_bids(bid_text):
        cleaned = clean_hex(raw)
        if not cleaned:
            continue
        if not allow_invalid and len(cleaned) not in (16, 32):
            continue
        if cleaned in seen:
            continue
        seen.add(cleaned)
        bids.append(cleaned)
    return bids


def extract_switch_metadata(text: str, *, max_lines: int = 50) -> dict:
    head = "\n".join((text or "").splitlines()[:max_lines])
    tid = ""
    bids: List[str] = []

    for match in SWITCH_TID_LINE_RE.finditer(head):
        value = match.group(1)
        tid_match = SWITCH_TID_VALUE_RE.search(value)
        if tid_match:
            tid = clean_hex(tid_match.group(0))
            break

    seen = set()
    for match in SWITCH_BID_LINE_RE.finditer(head):
        for bid_match in SWITCH_BID_VALUE_RE.finditer(match.group(1)):
            bid = clean_hex(bid_match.group(0))
            if bid in seen:
                continue
            seen.add(bid)
            bids.append(bid)

    return {"tid": tid, "bids": bids}


def validate_atmosphere_text(text: str) -> Optional[str]:
    meaningful_lines = []
    for line in (text or "").splitlines():
        stripped = (line or "").strip()
        if not stripped:
            continue
        if stripped.startswith(("#", ";", "//")):
            continue
        meaningful_lines.append(stripped)

    if not meaningful_lines:
        return "Atmosphere Quick Export requires cheat text in the editor."

    if any(ATMOSPHERE_SECTION_RE.match(line) or ATMOSPHERE_CODE_RE.match(line) for line in meaningful_lines):
        return None

    return "Atmosphere cheat text must include at least one [Cheat Name] section or code line."


def derive_cheat_name(text: str) -> str:
    """Derive a safe label from editor content for folders/filenames."""
    label = ""
    for line in (text or "").splitlines():
        stripped = (line or "").strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            label = stripped.lstrip("#").strip()
            if label:
                break
        label = stripped
        break
    if not label:
        label = "Cheats"
    label = re.sub(r'[\/:*?\"<>|]+', "_", label)
    label = re.sub(r"\s+", " ", label).strip()
    return label[:64] if len(label) > 64 else label


def normalize_ext(ext: str) -> str:
    ext = (ext or "").strip()
    if not ext:
        return ".txt"
    if not ext.startswith("."):
        ext = "." + ext
    return ext


def sanitize_path_fragment(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    value = re.sub(r'[\/:*?"<>|]+', "_", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_profile_id(info: dict, value: str, *, placeholder: str = "") -> str:
    normalized = value or ""
    if (info.get("id_normalization") or "").strip().casefold() == "hex":
        normalized = clean_hex(normalized)
    else:
        normalized = sanitize_path_fragment(normalized)
        if info.get("id_uppercase"):
            normalized = normalized.upper()
    return normalized or placeholder


def profile_id_label(info: dict) -> str:
    label = (info.get("id_label") or info.get("titleid_label") or "ID").strip()
    return label[:-1] if label.endswith(":") else label


def profile_id_placeholders(info: dict) -> List[str]:
    placeholders = info.get("id_placeholders")
    if placeholders:
        return [str(token) for token in placeholders if str(token).strip()]
    placeholder = str(info.get("id_placeholder") or "").strip()
    return [placeholder] if placeholder else []


def _has_meaningful_cheat_text(text: str, *, ignore_lines: Optional[set[str]] = None) -> bool:
    ignored = {line.casefold() for line in (ignore_lines or set())}
    for line in (text or "").splitlines():
        stripped = (line or "").strip()
        if not stripped:
            continue
        if stripped.startswith(("#", ";", "//")):
            continue
        if stripped.casefold() in ignored:
            continue
        return True
    return False


def validate_export_inputs(info: dict, tid: str, bid_text: str, editor_text: str = "") -> Optional[str]:
    kind = info.get("kind", "generic")
    if kind == "switch":
        cleaned_tid = clean_hex(tid)
        if len(cleaned_tid) != 16:
            return "Switch Quick Export requires a 16-character TitleID (TID)."

        bids = normalize_bids(bid_text, allow_invalid=True)
        if not bids:
            return "Switch Quick Export requires at least one BuildID (BID)."
        if any(len(bid) not in (16, 32) for bid in bids):
            return "Each BuildID must be 16 or 32 hex characters."

        subdir = (info.get("subdir", "") or "").strip().casefold()
        if subdir.startswith(ATMOSPHERE_SUBDIR_MARKER):
            return validate_atmosphere_text(editor_text)
        return None

    if kind == "titleid":
        cleaned_tid = clean_hex(tid)
        if len(cleaned_tid) != 16:
            return "This Quick Export requires a 16-character TitleID / Game ID."
        if info.get("citra_enabled") and not _has_meaningful_cheat_text(editor_text, ignore_lines={"*citra_enabled"}):
            return "This 3DS Quick Export requires cheat text in the editor."

    if kind == "idfile":
        normalized_id = normalize_profile_id(info, tid)
        id_regex = str(info.get("id_regex") or "").strip()
        if not normalized_id or (id_regex and not re.fullmatch(id_regex, normalized_id)):
            return str(info.get("id_error") or f"This Quick Export requires a valid {profile_id_label(info)}.")

    return None


def prepare_export_text(info: dict, editor_text: str) -> str:
    text = editor_text or ""
    if info.get("kind") == "titleid" and info.get("citra_enabled"):
        has_marker = any((line or "").strip().casefold() == "*citra_enabled" for line in text.splitlines())
        if not has_marker:
            stripped = text.lstrip("\ufeff")
            if stripped and not stripped.startswith("\n"):
                return f"*citra_enabled\n\n{text}"
            return f"*citra_enabled\n{text}"
    return text


def build_export_plan(
    *,
    prof: str,
    info: dict,
    root: Path,
    tid: str,
    bid_text: str,
    core: str,
    editor_text: str,
) -> dict:
    kind = info.get("kind", "generic")
    subdir = (info.get("subdir", "") or "").strip()
    filename_hint = (info.get("filename_hint", "cheats") or "cheats").strip()
    exts = info.get("extensions", [".txt"]) or [".txt"]
    ext = normalize_ext(exts[0] if exts else ".txt")

    cleaned_tid = clean_hex(tid) or "<TID>"
    normalized_profile_id = normalize_profile_id(
        info,
        tid,
        placeholder=str(info.get("id_placeholder") or "<ID>"),
    )
    bids = normalize_bids(bid_text) or ["<BID>"]
    safe_core = sanitize_path_fragment(core) or "<Core Name>"
    cheat_name = sanitize_path_fragment(derive_cheat_name(editor_text)) or "Cheats"
    id_placeholders = profile_id_placeholders(info)

    def apply_placeholders(value: str, bid_value: str | None = None) -> str:
        out = (value or "")
        out = out.replace("<TID>", cleaned_tid).replace("<TitleID>", cleaned_tid)
        for token in id_placeholders:
            out = out.replace(token, normalized_profile_id)
        out = out.replace("<Core Name>", safe_core)
        out = out.replace("<Cheat Name>", cheat_name)
        out = out.replace("<Pack Name>", cheat_name)
        out = out.replace("<Game>", cheat_name).replace("<GameID>", cheat_name)
        out = out.replace("<CRC>", cheat_name).replace("<SERIAL>", cheat_name)
        if bid_value is not None:
            out = out.replace("<BID>", bid_value)
        return out

    export_sub = apply_placeholders(subdir).replace("<", "_").replace(">", "_")
    out_dir = root / export_sub
    fixed_filename = info.get("fixed_filename")
    files = []

    if kind == "switch":
        for bid in bids:
            name = apply_placeholders(filename_hint, bid.strip() or "<BID>")
            name = name.replace("<", "_").replace(">", "_")
            files.append(out_dir / f"{name}{ext}")
    elif kind in {"titleid", "idfile"}:
        if fixed_filename:
            files.append(out_dir / fixed_filename)
        else:
            name = apply_placeholders(filename_hint).replace("<", "_").replace(">", "_")
            files.append(out_dir / f"{name}{ext}")
    elif kind == "singlefile" and fixed_filename:
        files.append(out_dir / fixed_filename)
    else:
        name = apply_placeholders(filename_hint).replace("<", "_").replace(">", "_")
        files.append(out_dir / f"{name}{ext}")

    return {
        "profile": prof,
        "kind": kind,
        "root": root,
        "out_dir": out_dir,
        "files": files,
        "ext": ext,
    }
