#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pamuk VIP — CloudStream depo üreteci.

Kaynak depoları (config/sources.json) izler, .cs3 eklentilerini `plugins/`
altına aynalar, kaynak JSON'larını `upstream/` altına kopyalar ve Pamuk VIP
başlıkları için `repo.json` / `plugins.json` üretir.

Komutlar
--------
  check            Kaynaklarda güncelleme var mı? (indirme yapmaz, rapor yazar)
  sync             Yeni/değişen eklentileri indirir, upstream kopyalarını ve
                   state/upstream.lock.json dosyasını günceller
  build            builds/*.json + kök repo.json + README.md üretir
  verify           Üretilen linkleri ve dosya bütünlüğünü doğrular
  status           Özet durum (kaynaklar, başlıklar, indirilemeyenler)
  set-repo         GitHub sahip/repo adını değiştirir ve yeniden derler
  all              sync + build + verify

Örnek:
  python tools/pamuk.py check
  python tools/pamuk.py sync
  python tools/pamuk.py build
  python tools/pamuk.py verify
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "pamuk.json"
SOURCES_PATH = ROOT / "config" / "sources.json"
LOCK_PATH = ROOT / "state" / "upstream.lock.json"
BUILD_SUMMARY_PATH = ROOT / "state" / "build-summary.json"
REPORT_PATH = ROOT / "reports" / "last-check.md"
INVENTORY_PATH = ROOT / "docs" / "eklenti-envanteri.md"
PLUGINS_DIR = ROOT / "plugins"
UPSTREAM_DIR = ROOT / "upstream"
BUILDS_DIR = ROOT / "builds"
README_PATH = ROOT / "README.md"

UA = "PamukVipRepo/1.0 (+https://github.com/Nikkoshoptr/PamukVip)"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - eski terminaller
        pass


# --------------------------------------------------------------------------
# Yardımcılar
# --------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def now_human() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def load_config() -> dict:
    cfg = read_json(CONFIG_PATH)
    if not cfg:
        raise SystemExit("config/pamuk.json bulunamadı veya geçersiz.")
    return cfg


def load_sources() -> list[dict]:
    data = read_json(SOURCES_PATH)
    if not data or not data.get("sources"):
        raise SystemExit("config/sources.json bulunamadı veya geçersiz.")
    return data["sources"]


def load_lock() -> dict:
    lock = read_json(LOCK_PATH, None)
    if not lock:
        lock = {"version": 1, "createdAt": now_iso(), "sources": {}}
    lock.setdefault("sources", {})
    return lock


def raw_base(cfg: dict) -> str:
    repo = cfg["repo"]
    return (
        f"https://raw.githubusercontent.com/{repo['owner']}/{repo['slug']}/{repo['branch']}"
    )


def iri_to_uri(url: str) -> str:
    """ASCII dışı karakter içeren adresleri istek için yüzde kodlamasına çevirir."""
    if url.isascii():
        return url
    parts = urlsplit(url)
    path = quote(parts.path, safe="/%:@!$&'()*+,;=~-._")
    query = quote(parts.query, safe="=&%:@!$'()*+,;/?~-._")
    return urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))


def http_get(url: str, timeout: int = 60, retries: int = 3) -> bytes:
    last_error: Exception | None = None
    url = iri_to_uri(url)
    for attempt in range(1, retries + 1):
        try:
            request = Request(
                url,
                headers={"User-Agent": UA, "Cache-Control": "no-cache"},
            )
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except HTTPError as exc:
            last_error = exc
            if exc.code in (400, 401, 403, 404, 410):
                raise
        except (URLError, TimeoutError, OSError) as exc:
            last_error = exc
        if attempt < retries:
            time.sleep(1.2 * attempt)
    assert last_error is not None
    raise last_error


def fetch_json(url: str) -> Any:
    raw = http_get(url)
    try:
        return json.loads(raw.decode("utf-8-sig"))
    except UnicodeDecodeError:
        return json.loads(raw.decode("utf-8", "replace"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 256), b""):
            digest.update(chunk)
    return "sha256-" + digest.hexdigest()


TR_TABLE = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def safe_name(value: str) -> str:
    text = value.translate(TR_TABLE)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in text)
    text = text.strip("-._")
    while "--" in text:
        text = text.replace("--", "-")
    return text or "plugin"


def unique_filename(base: str, used: set[str]) -> str:
    if base.casefold() not in used:
        return base
    stem, dot, ext = base.rpartition(".")
    if not dot:
        stem, ext = base, ""
    index = 2
    while True:
        candidate = f"{stem}-{index}{'.' + ext if ext else ''}"
        if candidate.casefold() not in used:
            return candidate
        index += 1


# --------------------------------------------------------------------------
# Kaynak okuma
# --------------------------------------------------------------------------


def normalize_entry(raw: dict, source: dict) -> dict | None:
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("internalName") or raw.get("name") or "").strip()
    if not name:
        return None
    types = [str(item) for item in (raw.get("tvTypes") or []) if item]
    if not types:
        types = ["Others"]
    try:
        version = int(raw.get("version") or 1)
    except (TypeError, ValueError):
        version = 1
    try:
        upstream_size = int(raw.get("fileSize") or 0)
    except (TypeError, ValueError):
        upstream_size = 0
    authors = [str(item) for item in (raw.get("authors") or []) if item]
    return {
        "internalName": name,
        "name": str(raw.get("name") or name),
        "version": version,
        "url": str(raw.get("url") or ""),
        "upstreamFileHash": str(raw.get("fileHash") or ""),
        "upstreamSize": upstream_size,
        "upstreamStatus": raw.get("status"),
        "apiVersion": raw.get("apiVersion") or 1,
        "language": str(raw.get("language") or "tr"),
        "tvTypes": types,
        "authors": authors or [str(source.get("label") or source["id"])],
        "description": str(raw.get("description") or ""),
        "iconUrl": str(raw.get("iconUrl") or ""),
        "upstreamRepoUrl": str(raw.get("repositoryUrl") or source["repoUrl"]),
    }


def fetch_source(source: dict) -> dict:
    """Kaynağın manifestini ve eklenti listelerini okur, kayıtları birleştirir."""
    errors: list[str] = []
    manifest: dict | None = None
    candidate_urls: list[str] = []

    if source.get("manifestUrl"):
        try:
            data = fetch_json(source["manifestUrl"])
            if isinstance(data, dict):
                manifest = data
                candidate_urls.extend(
                    url for url in (data.get("pluginLists") or []) if isinstance(url, str)
                )
        except Exception as exc:  # noqa: BLE001 - rapora taşınır
            errors.append(f"manifest okunamadı ({source['manifestUrl']}): {exc}")

    fallback = source.get("pluginsJson")
    if fallback and fallback not in candidate_urls:
        candidate_urls.append(fallback)

    merged: dict[str, dict] = {}
    used_lists: list[str] = []
    raw_primary: Any = None
    for url in candidate_urls:
        try:
            data = fetch_json(url)
        except Exception as exc:  # noqa: BLE001 - rapora taşınır
            errors.append(f"liste okunamadı ({url}): {exc}")
            continue
        if isinstance(data, dict):
            data = data.get("plugins") or []
        if not isinstance(data, list):
            errors.append(f"liste biçimi beklenmedik ({url})")
            continue
        used_lists.append(url)
        if raw_primary is None:
            raw_primary = data
        for raw in data:
            entry = normalize_entry(raw, source)
            if entry and entry["internalName"] not in merged:
                merged[entry["internalName"]] = entry

    return {
        "manifest": manifest,
        "listUrls": used_lists,
        "plugins": merged,
        "errors": errors,
        "rawPrimary": raw_primary,
    }


# --------------------------------------------------------------------------
# Karşılaştırma
# --------------------------------------------------------------------------


def diff_plugins(old_map: dict, new_map: dict) -> dict:
    old_map = old_map or {}
    added = [new_map[key]["name"] for key in new_map if key not in old_map]
    removed = [old_map[key].get("name", key) for key in old_map if key not in new_map]
    bumped: list[dict] = []
    changed: list[dict] = []
    for key, new in new_map.items():
        prev = old_map.get(key)
        if not prev:
            continue
        try:
            prev_version = int(prev.get("version") or 0)
        except (TypeError, ValueError):
            prev_version = 0
        if int(new["version"]) != prev_version:
            bumped.append(
                {"name": new["name"], "from": prev_version, "to": int(new["version"])}
            )
        elif (
            new["url"] != prev.get("url")
            or new["upstreamFileHash"] != prev.get("upstreamFileHash")
            or new["upstreamSize"] != prev.get("upstreamSize")
        ):
            changed.append({"name": new["name"], "reason": "adres/boyut/hash değişti"})
    return {
        "added": sorted(added, key=str.casefold),
        "removed": sorted(removed, key=str.casefold),
        "bumped": sorted(bumped, key=lambda item: str(item["name"]).casefold()),
        "changed": sorted(changed, key=lambda item: str(item["name"]).casefold()),
    }


def has_changes(diff: dict) -> bool:
    return any(diff[k] for k in ("added", "removed", "bumped", "changed"))


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------


def cmd_check(_args: argparse.Namespace) -> int:
    cfg = load_config()
    sources = load_sources()
    lock = load_lock()
    base = raw_base(cfg)

    lines: list[str] = []
    lines.append("# Pamuk VIP — Kaynak Güncelleme Kontrolü")
    lines.append("")
    lines.append(f"- Kontrol zamanı: **{now_human()}**")
    lines.append(f"- Depo: `{cfg['repo']['owner']}/{cfg['repo']['slug']}` ({cfg['repo']['branch']})")
    lines.append(f"- Yayın tabanı: <{base}>")
    lines.append("")

    total = {"added": 0, "removed": 0, "bumped": 0, "changed": 0}
    changed_sources: list[str] = []
    failed_sources: list[str] = []
    detail_blocks: list[str] = []

    print(f"Pamuk VIP — kaynak kontrolü ({len(sources)} kaynak)\n")

    for source in sources:
        sid = source["id"]
        label = source.get("label") or sid
        remote = fetch_source(source)
        locked = lock["sources"].get(sid, {})
        old_map = locked.get("plugins") or {}
        diff = diff_plugins(old_map, remote["plugins"])

        if remote["errors"] and not remote["plugins"]:
            failed_sources.append(label)

        print(f"  {label:<9} {len(remote['plugins']):>4} eklenti", end="")
        if has_changes(diff):
            changed_sources.append(label)
            print(
                f"  | +{len(diff['added'])} yeni"
                f"  -{len(diff['removed'])} kaldırılan"
                f"  ^{len(diff['bumped'])} sürüm"
                f"  ~{len(diff['changed'])} değişen"
            )
        else:
            print("  | değişiklik yok")

        for key in total:
            total[key] += len(diff[key])

        block = [f"## {label} — {source.get('title') or ''}".rstrip(), ""]
        block.append(f"- Kaynak depo: <{source['repoUrl']}>")
        if remote["listUrls"]:
            block.append("- Okunan liste: " + ", ".join(f"<{url}>" for url in remote["listUrls"]))
        if remote["errors"]:
            for error in remote["errors"]:
                block.append(f"- ⚠️ {error}")
        block.append(f"- Güncel eklenti sayısı: **{len(remote['plugins'])}**")
        block.append("")

        if not has_changes(diff):
            block.append("Değişiklik yok.")
            block.append("")
        else:
            if diff["added"]:
                block.append(f"### Yeni eklentiler ({len(diff['added'])})")
                block.extend(f"- {name}" for name in diff["added"][:60])
                if len(diff["added"]) > 60:
                    block.append(f"- … ve {len(diff['added']) - 60} tane daha")
                block.append("")
            if diff["bumped"]:
                block.append(f"### Sürüm güncellemeleri ({len(diff['bumped'])})")
                block.extend(
                    f"- {item['name']}: v{item['from']} → v{item['to']}"
                    for item in diff["bumped"][:60]
                )
                if len(diff["bumped"]) > 60:
                    block.append(f"- … ve {len(diff['bumped']) - 60} tane daha")
                block.append("")
            if diff["changed"]:
                block.append(f"### Adres/hash değişimi ({len(diff['changed'])})")
                block.extend(f"- {item['name']}: {item['reason']}" for item in diff["changed"][:60])
                if len(diff["changed"]) > 60:
                    block.append(f"- … ve {len(diff['changed']) - 60} tane daha")
                block.append("")
            if diff["removed"]:
                block.append(f"### Kaynaktan kaldırılanlar ({len(diff['removed'])})")
                block.extend(f"- {name}" for name in diff["removed"][:60])
                if len(diff["removed"]) > 60:
                    block.append(f"- … ve {len(diff['removed']) - 60} tane daha")
                block.append("")
        detail_blocks.append("\n".join(block))

    summary_line = (
        f"Toplam: +{total['added']} yeni, ^{total['bumped']} sürüm, "
        f"~{total['changed']} değişen, -{total['removed']} kaldırılan"
    )
    lines.append(f"## Özet")
    lines.append("")
    lines.append(f"- {summary_line}")
    lines.append(f"- Değişen kaynaklar: {', '.join(changed_sources) or 'yok'}")
    if failed_sources:
        lines.append(f"- Erişilemeyen kaynaklar: {', '.join(failed_sources)}")
    lines.append("")
    lines.append(
        "Onay verilirse: `python tools/pamuk.py sync` ardından "
        "`python tools/pamuk.py build` ve `python tools/pamuk.py verify`."
    )
    lines.append("")
    lines.extend(detail_blocks)

    write_text(REPORT_PATH, "\n".join(lines).rstrip() + "\n")

    print()
    print(summary_line)
    if changed_sources:
        print("Değişen kaynaklar: " + ", ".join(changed_sources))
    else:
        print("Kaynaklarda güncelleme yok.")
    if failed_sources:
        print("Erişilemeyen kaynaklar: " + ", ".join(failed_sources))
    rel = REPORT_PATH.relative_to(ROOT)
    print(f"Rapor: {rel}")
    return 0


# --------------------------------------------------------------------------
# sync
# --------------------------------------------------------------------------


def sync_source(source: dict, remote: dict, locked: dict, force: bool) -> tuple[dict, dict]:
    sid = source["id"]
    srcdir = PLUGINS_DIR / sid
    srcdir.mkdir(parents=True, exist_ok=True)
    old_plugins = locked.get("plugins") or {}
    new_plugins: dict[str, dict] = {}
    used_files: set[str] = set()
    stats = {"downloaded": 0, "reused": 0, "failed": []}

    for name, item in remote["plugins"].items():
        prev = old_plugins.get(name) or {}
        filename = prev.get("file")
        if not filename:
            filename = unique_filename(safe_name(name) + ".cs3", used_files)
        used_files.add(str(filename).casefold())
        path = srcdir / filename

        same_meta = (
            prev.get("version") == item["version"]
            and prev.get("url") == item["url"]
            and prev.get("upstreamFileHash") == item["upstreamFileHash"]
            and prev.get("upstreamSize") == item["upstreamSize"]
        )
        needs_download = force or not path.exists() or not same_meta

        digest: str | None
        if needs_download:
            try:
                payload = http_get(item["url"], timeout=120)
                digest = "sha256-" + hashlib.sha256(payload).hexdigest()
                expected = item["upstreamFileHash"]
                if expected.startswith("sha256-") and expected != digest:
                    item["hashWarning"] = "upstream fileHash ile indirilen dosya eşleşmiyor"
                tmp = path.with_name(path.name + ".tmp")
                tmp.write_bytes(payload)
                tmp.replace(path)
                stats["downloaded"] += 1
            except Exception as exc:  # noqa: BLE001 - rapora taşınır
                stats["failed"].append(
                    {"internalName": name, "url": item["url"], "error": str(exc)}
                )
                digest = sha256_file(path) if path.exists() else None
        else:
            digest = sha256_file(path)
            stats["reused"] += 1

        mirrored = bool(digest) and path.exists()
        size = path.stat().st_size if mirrored else 0
        previous_published = int(prev.get("publishedVersion") or 0)
        base_version = int(item["version"])
        content_changed = bool(prev) and prev.get("sha256") != digest
        if base_version > previous_published:
            published = base_version
        elif content_changed:
            published = max(previous_published + 1, base_version)
        else:
            published = max(previous_published, base_version)

        record = dict(item)
        record.update(
            {
                "file": filename,
                "sha256": digest,
                "size": size,
                "mirrored": mirrored,
                "publishedVersion": published,
                "syncedAt": now_iso(),
            }
        )
        new_plugins[name] = record

    entry = {
        "label": source.get("label") or sid,
        "title": source.get("title") or "",
        "repoUrl": source["repoUrl"],
        "manifestUrl": source.get("manifestUrl"),
        "pluginsJson": source.get("pluginsJson"),
        "listUrls": remote["listUrls"],
        "fetchedAt": now_iso(),
        "errors": remote["errors"],
        "pluginCount": len(new_plugins),
        "plugins": new_plugins,
    }
    return entry, stats


def save_upstream_copy(source: dict, remote: dict, entry: dict) -> None:
    target = UPSTREAM_DIR / source["id"]
    target.mkdir(parents=True, exist_ok=True)
    if remote.get("manifest") is not None:
        write_json(target / "repo.json", remote["manifest"])
    if remote.get("rawPrimary") is not None:
        write_json(target / "plugins.json", remote["rawPrimary"])
    mirrored = sum(1 for item in entry["plugins"].values() if item.get("mirrored"))
    lines = [
        f"# {entry['label']} — kaynak kopyası",
        "",
        f"- Kaynak depo: <{source['repoUrl']}>",
        f"- Manifest: <{source['manifestUrl']}>" if source.get("manifestUrl") else "- Manifest: yok",
        f"- Eklenti listesi: <{source.get('pluginsJson')}>",
        f"- Kopyalama zamanı: {now_human()}",
        f"- Eklenti sayısı: {entry['pluginCount']}",
        f"- Aynalanan dosya: {mirrored}",
        "",
        "Bu klasördeki JSON dosyaları kaynaktan olduğu gibi alınmıştır;",
        "`.cs3` dosyaları `plugins/" + source["id"] + "/` altında tutulur.",
        "",
    ]
    write_text(target / "SOURCE.md", "\n".join(lines))


def cmd_sync(args: argparse.Namespace) -> int:
    cfg = load_config()
    sources = load_sources()
    lock = load_lock()
    force = bool(getattr(args, "force", False))

    all_stats: dict[str, dict] = {}
    print(f"Pamuk VIP — senkronizasyon ({len(sources)} kaynak){' [tam]' if force else ''}\n")

    for source in sources:
        sid = source["id"]
        label = source.get("label") or sid
        remote = fetch_source(source)
        if not remote["plugins"]:
            print(f"  {label:<9} atlandı (liste alınamadı)")
            for error in remote["errors"]:
                print(f"            {error}")
            continue
        entry, stats = sync_source(source, remote, lock["sources"].get(sid) or {}, force)
        lock["sources"][sid] = entry
        save_upstream_copy(source, remote, entry)
        all_stats[sid] = stats
        print(
            f"  {label:<9} {entry['pluginCount']:>4} eklenti"
            f" | indirilen {stats['downloaded']}"
            f" | yeniden kullanılan {stats['reused']}"
            + (f" | hata {len(stats['failed'])}" if stats["failed"] else "")
        )

    lock["updatedAt"] = now_iso()
    lock["rawBase"] = raw_base(cfg)
    write_json(LOCK_PATH, lock)

    failures = [
        (sid, item) for sid, stats in all_stats.items() for item in stats["failed"]
    ]
    if failures:
        print("\nİndirilemeyen eklentiler (upstream adresiyle yayınlanacak):")
        for sid, item in failures[:20]:
            print(f"  - [{sid}] {item['internalName']}: {item['error'][:110]}")
        if len(failures) > 20:
            print(f"  … ve {len(failures) - 20} tane daha")

    total = sum(entry["pluginCount"] for entry in lock["sources"].values())
    print(f"\nToplam kayıt: {total}. Sırada: python tools/pamuk.py build")
    return 0


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------


def classify(entry: dict, source: dict, cls: dict) -> list[str]:
    pins = cls.get("pins") or {}
    name = entry["internalName"]
    if name in pins:
        value = pins[name]
        if value in (None, "skip", []):
            return []
        return [value] if isinstance(value, str) else list(value)

    key = name.casefold()
    types = [str(item).casefold() for item in entry.get("tvTypes") or []]
    language = str(entry.get("language") or "").casefold()

    adult_hit = (
        bool(source.get("adult"))
        or "nsfw" in types
        or any(keyword in key for keyword in cls.get("adultKeywords", []))
    )
    if adult_hit:
        return ["adult"]

    groups: list[str] = []
    if "live" in types:
        sport_hit = source["id"] == "spor" or any(
            keyword in key for keyword in cls.get("sportKeywords", [])
        )
        groups.append("spor" if sport_hit else "tv")
    else:
        groups.append(primary_group(key, types, cls))

    if language and not language.startswith("tr") and "dunya" not in groups:
        groups.append("dunya")

    ordered: list[str] = []
    for item in groups:
        if item not in ordered:
            ordered.append(item)
    return ordered


def primary_group(key: str, types: list[str], cls: dict) -> str:
    """Eklentiyi tek bir ana başlığa atar (ad sinyali → tür sinyali → varsayılan)."""
    if any(word in key for word in cls.get("sportKeywords", [])):
        return "spor"

    keywords = cls.get("groupKeywords") or {}
    for group_id in ("anime", "belgesel", "dizi", "film", "tv"):
        if any(word in key for word in keywords.get(group_id, [])):
            return group_id

    type_set = set(types)
    if "anime" in type_set and "tvseries" not in type_set and "documentary" not in type_set:
        return "anime"
    if "documentary" in type_set and not (type_set & {"movie", "tvseries"}):
        return "belgesel"
    if "tvseries" in type_set or "asiandrama" in type_set:
        return "dizi"
    if "movie" in type_set:
        return "film"
    if "documentary" in type_set:
        return "belgesel"
    return "tv"


def dedupe(entries: list[dict], cfg: dict) -> list[dict]:
    priority = {
        sid: index
        for index, sid in enumerate(cfg.get("dedupe", {}).get("sourcePriority") or [])
    }
    prefer_version = bool(cfg.get("dedupe", {}).get("preferHighestVersion", True))
    best: dict[str, dict] = {}

    def is_better(candidate: dict, current: dict) -> bool:
        if prefer_version and candidate["version"] != current["version"]:
            return candidate["version"] > current["version"]
        cand_rank = priority.get(candidate["_source"], 99)
        curr_rank = priority.get(current["_source"], 99)
        if cand_rank != curr_rank:
            return cand_rank < curr_rank
        return candidate["_source"] < current["_source"]

    for entry in entries:
        current = best.get(entry["internalName"])
        if current is None or is_better(entry, current):
            best[entry["internalName"]] = entry
    return sorted(best.values(), key=lambda item: str(item["name"]).casefold())


def publish_shape(entry: dict) -> dict:
    payload = {
        "name": entry["name"],
        "internalName": entry["internalName"],
        "version": int(entry["version"]),
        "url": entry["url"],
        "status": 1,
        "apiVersion": entry.get("apiVersion") or 1,
        "language": entry.get("language") or "tr",
        "tvTypes": entry.get("tvTypes") or ["Others"],
        "authors": entry.get("authors") or [],
        "description": entry.get("description") or "",
        "repositoryUrl": entry["repositoryUrl"],
        "fileSize": int(entry.get("fileSize") or 0),
    }
    if entry.get("fileHash"):
        payload["fileHash"] = entry["fileHash"]
    if entry.get("iconUrl"):
        payload["iconUrl"] = entry["iconUrl"]
    return payload


def collect_entries(cfg: dict, lock: dict, sources: list[dict]) -> list[dict]:
    base = raw_base(cfg)
    entries: list[dict] = []
    for source in sources:
        sid = source["id"]
        locked = (lock["sources"].get(sid) or {}).get("plugins") or {}
        for record in locked.values():
            mirrored = bool(record.get("mirrored")) and bool(record.get("file"))
            if mirrored:
                url = f"{base}/plugins/{sid}/{quote(str(record['file']))}"
                file_hash = record.get("sha256") or ""
                file_size = record.get("size") or 0
            else:
                url = record.get("url") or ""
                file_hash = record.get("upstreamFileHash") or ""
                file_size = record.get("upstreamSize") or 0
            if not url:
                continue
            entries.append(
                {
                    "name": record.get("name") or record["internalName"],
                    "internalName": record["internalName"],
                    "version": int(record.get("publishedVersion") or record.get("version") or 1),
                    "url": url,
                    "apiVersion": record.get("apiVersion") or 1,
                    "language": record.get("language") or "tr",
                    "tvTypes": record.get("tvTypes") or ["Others"],
                    "authors": record.get("authors") or [],
                    "description": record.get("description") or "",
                    "iconUrl": record.get("iconUrl") or "",
                    "repositoryUrl": cfg["repo"]["pageUrl"],
                    "fileSize": file_size,
                    "fileHash": file_hash,
                    "mirrored": mirrored,
                    "_source": sid,
                }
            )
    return entries


def write_repo_json(path: Path, name: str, description: str, plugin_list_url: str, count: int) -> dict:
    payload = {
        "name": name,
        "description": description,
        "manifestVersion": 1,
        "pluginLists": [plugin_list_url],
        "lastUpdated": int(time.time()),
        "pluginCount": count,
    }
    write_json(path, payload)
    return payload


def cmd_build(_args: argparse.Namespace) -> int:
    cfg = load_config()
    sources = load_sources()
    lock = load_lock()
    base = raw_base(cfg)

    if not lock["sources"]:
        raise SystemExit("Aynalanmış kayıt yok. Önce: python tools/pamuk.py sync")

    entries = collect_entries(cfg, lock, sources)
    if not entries:
        raise SystemExit("Yayınlanacak eklenti bulunamadı.")

    source_map = {source["id"]: source for source in sources}
    grouped: dict[str, list[dict]] = {group["id"]: [] for group in cfg["groups"]}
    for entry in entries:
        for group_id in classify(entry, source_map[entry["_source"]], cfg.get("classification") or {}):
            if group_id in grouped:
                grouped[group_id].append(entry)

    summary_groups: list[dict] = []
    for group in sorted(cfg["groups"], key=lambda item: item.get("order", 99)):
        gid = group["id"]
        items = dedupe(grouped.get(gid, []), cfg)
        if not items:
            print(f"  uyarı: {group['name']} boş, atlanıyor")
            continue
        payload = [publish_shape(item) for item in items]
        target_dir = BUILDS_DIR / gid
        write_json(target_dir / "plugins.json", payload)
        list_url = f"{base}/builds/{gid}/plugins.json"
        write_repo_json(
            target_dir / "repo.json",
            group["name"],
            group.get("description") or f"{group['name']} — CloudStream eklenti deposu",
            list_url,
            len(payload),
        )
        summary_groups.append(
            {
                "id": gid,
                "name": group["name"],
                "description": group.get("description") or "",
                "count": len(payload),
                "adult": bool(group.get("adult")),
                "pluginsJson": list_url,
                "repoJson": f"{base}/builds/{gid}/repo.json",
                "pageUrl": f"{cfg['repo']['pageUrl']}/blob/{cfg['repo']['branch']}/builds/{gid}/repo.json",
            }
        )
        print(f"  {group['name']:<14} {len(payload):>4} eklenti → builds/{gid}/")

    aggregate = dedupe(entries, cfg)
    aggregate_payload = [publish_shape(item) for item in aggregate]
    agg_id = cfg.get("aggregateId") or "pamuk-vip"
    agg_dir = BUILDS_DIR / agg_id
    write_json(agg_dir / "plugins.json", aggregate_payload)
    agg_list_url = f"{base}/builds/{agg_id}/plugins.json"
    write_repo_json(
        agg_dir / "repo.json",
        cfg["repo"]["name"],
        cfg["repo"]["description"],
        agg_list_url,
        len(aggregate_payload),
    )
    write_repo_json(
        ROOT / "repo.json",
        cfg["repo"]["name"],
        cfg["repo"]["description"],
        agg_list_url,
        len(aggregate_payload),
    )

    source_stats = []
    for source in sources:
        locked = (lock["sources"].get(source["id"]) or {}).get("plugins") or {}
        mirrored = sum(1 for item in locked.values() if item.get("mirrored"))
        source_stats.append(
            {
                "id": source["id"],
                "label": source.get("label") or source["id"],
                "title": source.get("title") or "",
                "repoUrl": source["repoUrl"],
                "count": len(locked),
                "mirrored": mirrored,
                "fallback": len(locked) - mirrored,
            }
        )

    summary = {
        "builtAt": now_iso(),
        "rawBase": base,
        "mainRepoJson": f"{base}/repo.json",
        "mainPluginsJson": agg_list_url,
        "totalUnique": len(aggregate_payload),
        "groups": summary_groups,
        "sources": source_stats,
    }
    write_json(BUILD_SUMMARY_PATH, summary)

    write_text(README_PATH, render_readme(cfg, summary))
    write_text(INVENTORY_PATH, render_inventory(cfg, summary, aggregate))
    write_text(ROOT / "docs" / "kaynak-depolar.md", render_sources(cfg, sources, summary))

    print(f"  {'Pamuk VIP':<14} {len(aggregate_payload):>4} eklenti → builds/{agg_id}/ + kök repo.json")
    print(f"\nAna link: {base}/repo.json")
    print("README.md ve docs/eklenti-envanteri.md güncellendi.")
    return 0


# --------------------------------------------------------------------------
# README / envanter
# --------------------------------------------------------------------------


def render_readme(cfg: dict, summary: dict) -> str:
    repo = cfg["repo"]
    base = summary["rawBase"]
    groups = summary["groups"]
    total = summary["totalUnique"]
    page = repo["pageUrl"]

    lines: list[str] = []
    lines.append("# Pamuk VIP — CloudStream Eklenti Deposu")
    lines.append("")
    lines.append(
        f"Pamuk VIP, **{len(groups)} başlık** altında **{total} eklenti** sunan bir CloudStream "
        "deposudur. Tüm eklenti dosyaları bu depoda aynalanır; kaynak depolar güncellendikçe "
        "buradaki sürümler de güncellenir."
    )
    lines.append("")
    lines.append(f"- Depo: <{page}>")
    lines.append(f"- Son derleme: **{now_human()}**")
    lines.append("")
    lines.append("## Kurulum")
    lines.append("")
    lines.append("1. CloudStream'i açın → **Ayarlar → Eklentiler → Depo ekle**.")
    lines.append("2. Aşağıdaki ana linki yapıştırın ve kaydedin.")
    lines.append("3. Depoya girip istediğiniz eklentileri indirin.")
    lines.append("")
    lines.append("**Ana depo linki (Pamuk VIP — tüm başlıklar):**")
    lines.append("")
    lines.append("```")
    lines.append(summary["mainRepoJson"])
    lines.append("```")
    lines.append("")
    lines.append("## Başlık linkleri")
    lines.append("")
    lines.append("Her başlık ayrı bir depo olarak da eklenebilir. Tek başlık eklerseniz yalnızca o gruptaki eklentiler listelenir.")
    lines.append("")
    lines.append("| Başlık | Eklenti | Depo linki |")
    lines.append("| --- | ---: | --- |")
    lines.append(f"| **Pamuk VIP** (ana) | {total} | {summary['mainRepoJson']} |")
    for group in groups:
        label = f"**{group['name']}**" + (" (18+)" if group["adult"] else "")
        lines.append(f"| {label} | {group['count']} | {group['repoJson']} |")
    lines.append("")
    lines.append("## Kaynak depolar")
    lines.append("")
    lines.append("Bu depodaki eklentiler aşağıdaki kaynaklardan aynalanır. Kaynaklar güncellendiğinde `check → sync → build` akışıyla buraya aktarılır.")
    lines.append("")
    lines.append("| Kaynak | Depo | Aynalanan |")
    lines.append("| --- | --- | ---: |")
    for source in summary["sources"]:
        note = f"{source['mirrored']}/{source['count']}"
        if source["fallback"]:
            note += f" ({source['fallback']} upstream)"
        lines.append(f"| {source['label']} | <{source['repoUrl']}> | {note} |")
    lines.append("")
    lines.append("## Güncelleme akışı")
    lines.append("")
    lines.append("```bash")
    lines.append("python tools/pamuk.py check    # kaynaklarda ne değişti? (rapor: reports/last-check.md)")
    lines.append("python tools/pamuk.py sync     # onay sonrası: yeni/değişen eklentileri indir")
    lines.append("python tools/pamuk.py build    # repo.json + plugins.json + bu README'yi üret")
    lines.append("python tools/pamuk.py verify   # linkleri ve dosya hash'lerini doğrula")
    lines.append("```")
    lines.append("")
    lines.append("Windows'ta kısayol: `pamuk.cmd check`, `pamuk.cmd sync`, `pamuk.cmd build`, `pamuk.cmd verify`.")
    lines.append("")
    lines.append("## Klasör yapısı")
    lines.append("")
    lines.append("```")
    lines.append("config/     kaynak depolar ve başlık tanımları")
    lines.append("plugins/    aynalanan .cs3 eklenti dosyaları (kaynak başına klasör)")
    lines.append("upstream/   kaynak repo.json / plugins.json kopyaları")
    lines.append("builds/     CloudStream'in okuduğu repo.json + plugins.json (başlık başına)")
    lines.append("state/      kaynak sürüm kilidi (upstream.lock.json) ve derleme özeti")
    lines.append("reports/    son güncelleme kontrolü raporu")
    lines.append("tools/      pamuk.py üreteci")
    lines.append("```")
    lines.append("")
    lines.append("## Notlar")
    lines.append("")
    lines.append("- Her eklenti, adı ve ana türüne göre tek bir başlıkta listelenir; Türkçe dışı eklentiler ayrıca **Pamuk Dünya** başlığında görünür.")
    lines.append("- Aynı eklenti birden fazla kaynakta varsa en yüksek sürümlü kayıt yayınlanır (kaynak önceliği: "
                 + " → ".join(cfg.get("dedupe", {}).get("sourcePriority") or []) + ").")
    lines.append("- Kaynaktan indirilemeyen eklentiler, çalışmaya devam etmesi için özgün adresiyle yayınlanır.")
    lines.append("- Pamuk Adult başlığı 18+ içerik barındırır; CloudStream'de yetişkin içerik ayarı kapalıysa görünmez.")
    lines.append("")
    lines.append("## Yasal uyarı")
    lines.append("")
    lines.append("Bu depo yalnızca açık kaynak CloudStream eklentilerini bir araya getirir ve hiçbir içerik barındırmaz. "
                 "Eklentiler üçüncü taraf sitelere bağlanır; içeriklerin yasallığı ve kullanım sorumluluğu kullanıcıya aittir. "
                 "18+ başlığındaki içerikler yalnızca reşit kullanıcılar içindir.")
    lines.append("")
    return "\n".join(lines)


def render_sources(cfg: dict, sources: list[dict], summary: dict) -> str:
    stats = {item["id"]: item for item in summary.get("sources", [])}
    lines = [
        "# Kaynak Depolar",
        "",
        "Pamuk VIP deposu aşağıdaki kaynaklardan beslenir. Bu dosya `config/sources.json` temel alınarak üretilir.",
        "",
        "| Kaynak | Depo sayfası | Manifest (repo.json) | Eklenti listesi | Eklenti |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for source in sources:
        manifest = f"<{source['manifestUrl']}>" if source.get("manifestUrl") else "—"
        plugins = f"<{source['pluginsJson']}>" if source.get("pluginsJson") else "—"
        count = stats.get(source["id"], {}).get("count", 0)
        lines.append(
            f"| {source.get('label') or source['id']} | <{source['repoUrl']}> | {manifest} | {plugins} | {count} |"
        )
    lines.append("")
    lines.append("## Notlar")
    lines.append("")
    for source in sources:
        if source.get("note"):
            lines.append(f"- **{source.get('label') or source['id']}**: {source['note']}")
    lines.append("")
    lines.append(
        "Kaynak JSON'larının son kopyaları `upstream/<kaynak>/` altında, eklenti dosyaları "
        "`plugins/<kaynak>/` altında tutulur."
    )
    lines.append("")
    return "\n".join(lines)


def render_inventory(cfg: dict, summary: dict, aggregate: list[dict]) -> str:
    lines = [
        "# Pamuk VIP — Eklenti Envanteri",
        "",
        f"- Derleme: {now_human()}",
        f"- Toplam benzersiz eklenti: **{len(aggregate)}**",
        "",
        "Aynı eklenti birden fazla başlıkta yer alabilir; bu liste başlık bazlıdır.",
        "",
    ]
    groups = {group["id"]: group for group in summary["groups"]}
    for group in summary["groups"]:
        gid = group["id"]
        payload = read_json(BUILDS_DIR / gid / "plugins.json", []) or []
        lines.append(f"## {group['name']} ({len(payload)})")
        lines.append("")
        lines.append("| Eklenti | Sürüm | Tür | Dil |")
        lines.append("| --- | ---: | --- | --- |")
        for entry in payload:
            types = ", ".join(entry.get("tvTypes") or [])
            lines.append(
                f"| {entry['internalName']} | v{entry['version']} | {types} | {entry.get('language') or '-'} |"
            )
        lines.append("")
    if groups:
        pass
    return "\n".join(lines)


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------


def cmd_verify(_args: argparse.Namespace) -> int:
    cfg = load_config()
    base = raw_base(cfg)
    problems: list[str] = []
    checked = 0
    checked_files = 0

    plugin_lists = sorted(BUILDS_DIR.glob("*/plugins.json"))
    if not plugin_lists:
        raise SystemExit("builds/ altında plugins.json yok. Önce: python tools/pamuk.py build")

    for list_path in plugin_lists:
        data = read_json(list_path, [])
        if not isinstance(data, list) or not data:
            problems.append(f"{list_path.relative_to(ROOT)} boş veya geçersiz")
            continue
        names: set[str] = set()
        for entry in data:
            checked += 1
            where = f"{list_path.relative_to(ROOT)} → {entry.get('internalName')}"
            for field in ("name", "internalName", "version", "url", "tvTypes", "language"):
                if entry.get(field) in (None, ""):
                    problems.append(f"{where}: `{field}` alanı boş")
            if entry["internalName"] in names:
                problems.append(f"{where}: liste içinde tekrarlanan internalName")
            names.add(entry["internalName"])

            url = str(entry.get("url") or "")
            if url.startswith(base + "/"):
                relative = unquote(url[len(base) + 1:])
                path = ROOT / relative
                if not path.exists():
                    problems.append(f"{where}: dosya yok ({relative})")
                    continue
                checked_files += 1
                if entry.get("fileSize") and path.stat().st_size != entry["fileSize"]:
                    problems.append(f"{where}: boyut uyuşmuyor")
                digest = sha256_file(path)
                if entry.get("fileHash") and digest != entry["fileHash"]:
                    problems.append(f"{where}: sha256 uyuşmuyor")
            elif not url.startswith("http"):
                problems.append(f"{where}: geçersiz url")

    for required in (ROOT / "repo.json", BUILDS_DIR / (cfg.get("aggregateId") or "pamuk-vip") / "repo.json"):
        payload = read_json(required, None)
        if not payload:
            problems.append(f"{required.relative_to(ROOT)} eksik")
            continue
        if not payload.get("pluginLists"):
            problems.append(f"{required.relative_to(ROOT)}: pluginLists boş")
        if payload.get("name") != cfg["repo"]["name"] and required.parent == ROOT:
            problems.append(f"{required.relative_to(ROOT)}: depo adı '{cfg['repo']['name']}' değil")

    print(f"Doğrulanan kayıt: {checked}, yerel dosya: {checked_files}, liste: {len(plugin_lists)}")
    if problems:
        print(f"\n{len(problems)} sorun bulundu:")
        for problem in problems[:40]:
            print(f"  - {problem}")
        if len(problems) > 40:
            print(f"  … ve {len(problems) - 40} tane daha")
        return 1
    print("Doğrulama başarılı: tüm linkler, boyutlar ve hash'ler tutarlı.")
    return 0


# --------------------------------------------------------------------------
# status / set-repo
# --------------------------------------------------------------------------


def cmd_status(_args: argparse.Namespace) -> int:
    cfg = load_config()
    sources = load_sources()
    lock = load_lock()
    summary = read_json(BUILD_SUMMARY_PATH, None) or {}

    print(f"Pamuk VIP — {cfg['repo']['owner']}/{cfg['repo']['slug']} ({cfg['repo']['branch']})")
    print(f"Yayın tabanı: {raw_base(cfg)}\n")
    print("Kaynaklar:")
    total_records = 0
    for source in sources:
        locked = (lock["sources"].get(source["id"]) or {}).get("plugins") or {}
        mirrored = sum(1 for item in locked.values() if item.get("mirrored"))
        total_records += len(locked)
        state = "kayıtlı" if locked else "henüz aynalanmadı"
        print(
            f"  {source.get('label'):<9} {len(locked):>4} eklenti"
            f" | yerel {mirrored:>4} | {state}"
        )
    print(f"\nToplam kayıt: {total_records}")
    if summary:
        print(f"Son derleme: {summary.get('builtAt')} — {summary.get('totalUnique')} benzersiz eklenti")
        print(f"Ana link: {summary.get('mainRepoJson')}")
        for group in summary.get("groups", []):
            print(f"  {group['name']:<15} {group['count']:>4}  {group['repoJson']}")
    else:
        print("Henüz derleme yok. Sırada: python tools/pamuk.py build")
    return 0


def cmd_set_repo(args: argparse.Namespace) -> int:
    cfg = load_config()
    if args.owner:
        cfg["repo"]["owner"] = args.owner
    if args.slug:
        cfg["repo"]["slug"] = args.slug
    if args.branch:
        cfg["repo"]["branch"] = args.branch
    if args.name:
        cfg["repo"]["name"] = args.name
    cfg["repo"]["pageUrl"] = (
        f"https://github.com/{cfg['repo']['owner']}/{cfg['repo']['slug']}"
    )
    write_json(CONFIG_PATH, cfg)
    print(f"Depo ayarı: {cfg['repo']['owner']}/{cfg['repo']['slug']}@{cfg['repo']['branch']}")
    print("Yeniden derleniyor…")
    return cmd_build(args)


def cmd_all(args: argparse.Namespace) -> int:
    cmd_sync(args)
    code = cmd_build(args)
    if code:
        return code
    return cmd_verify(args)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pamuk",
        description="Pamuk VIP CloudStream deposu üreteci",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="kaynaklarda güncelleme kontrolü").set_defaults(func=cmd_check)
    sync_parser = sub.add_parser("sync", help="yeni/değişen eklentileri indir")
    sync_parser.add_argument("--force", action="store_true", help="tüm dosyaları yeniden indir")
    sync_parser.set_defaults(func=cmd_sync)
    sub.add_parser("build", help="depo JSON'larını ve README'yi üret").set_defaults(func=cmd_build)
    sub.add_parser("verify", help="link ve dosya bütünlüğünü doğrula").set_defaults(func=cmd_verify)
    sub.add_parser("status", help="özet durum").set_defaults(func=cmd_status)
    sub.add_parser("all", help="sync + build + verify").set_defaults(func=cmd_all)

    setter = sub.add_parser("set-repo", help="GitHub sahip/repo adını değiştir")
    setter.add_argument("--owner")
    setter.add_argument("--slug")
    setter.add_argument("--branch")
    setter.add_argument("--name")
    setter.set_defaults(func=cmd_set_repo)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
