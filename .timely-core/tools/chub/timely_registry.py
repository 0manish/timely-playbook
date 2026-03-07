"""Generate a repo-local Context Hub mirror for Timely Playbook."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from tools.workspace import resolve_workspace, validate_core_manifest

WORKSPACE = resolve_workspace(Path(__file__).resolve())
ROOT = WORKSPACE.root
AUTHOR = "timely-playbook"
OVERRIDES_PATH = WORKSPACE.core_dir / "tools" / "chub" / "metadata_overrides.json"
COMMUNITY_SEARCH_INDEX_URL = "https://cdn.aichub.org/v1/search-index.json"

STOP_WORDS = {
    "a",
    "agent",
    "agents",
    "and",
    "docs",
    "document",
    "documentation",
    "file",
    "files",
    "for",
    "guide",
    "md",
    "playbook",
    "prompt",
    "repository",
    "template",
    "the",
    "timely",
    "to",
}


@dataclass(frozen=True)
class MirrorSource:
    """Represents one repo-authored markdown file mirrored into Context Hub."""

    relative_path: Path
    source_path: Path
    category: str
    entry_name: str

    @property
    def entry_id(self) -> str:
        return f"{AUTHOR}/{self.entry_name}"

    @property
    def content_path(self) -> str:
        return f"docs/{self.entry_name}"


def _slugify(value: str) -> str:
    expanded = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", value)
    expanded = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "-", expanded)
    expanded = re.sub(r"[^A-Za-z0-9]+", "-", expanded)
    return expanded.strip("-").lower() or "entry"


def _tokenize(value: str) -> List[str]:
    slug = _slugify(value)
    return [token for token in slug.split("-") if token]


def _load_overrides(path: Path = OVERRIDES_PATH) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    normalized: Dict[str, Dict[str, Any]] = {}
    for key, raw in payload.items():
        if isinstance(raw, dict):
            normalized[str(Path(key).as_posix())] = raw
    return normalized


def _load_chub_dependency_version(repo_root: Path) -> str | None:
    """Return the pinned @aisuite/chub dependency version when available."""

    workspace = resolve_workspace(repo_root=repo_root)
    for package_json in (workspace.runtime_dir / "package.json", repo_root / "package.json"):
        if not package_json.exists():
            continue
        try:
            payload = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        for section in ("dependencies", "devDependencies"):
            raw = payload.get(section, {})
            if isinstance(raw, dict) and "@aisuite/chub" in raw:
                value = str(raw["@aisuite/chub"]).strip()
                return value or None
    return None


def collect_markdown_sources(repo_root: Path) -> List[MirrorSource]:
    """Return the tracked markdown corpus mirrored into Context Hub."""

    workspace = resolve_workspace(repo_root=repo_root)
    validate_core_manifest(workspace)
    collected: Dict[str, MirrorSource] = {}

    def register(relative_path: Path, source_path: Path) -> None:
        rel = Path(relative_path)
        if rel.as_posix() in collected:
            return
        category, entry_name = classify_path(rel)
        collected[rel.as_posix()] = MirrorSource(rel, source_path.resolve(), category, entry_name)

    if workspace.relocated:
        for path in sorted(workspace.core_dir.glob("*.md")):
            if path.is_file():
                register(path.relative_to(workspace.core_dir), path)

        for name in ("AGENTS.md", "SKILLS.md"):
            path = workspace.local_dir / name
            if path.exists():
                register(Path(name), path)

        roots = {
            "timely-trackers": workspace.local_dir / "timely-trackers",
            "templates": workspace.core_dir / "templates",
            "snippets": workspace.core_dir / "snippets",
        }
        for base, actual_root in roots.items():
            if not actual_root.exists():
                continue
            for path in sorted(actual_root.rglob("*.md")):
                if path.is_file():
                    register(Path(base) / path.relative_to(actual_root), path)

        status_path = workspace.local_dir / ".orchestrator" / "STATUS.md"
        if status_path.exists():
            register(Path(".orchestrator/STATUS.md"), status_path)

        prompts_dir = workspace.core_dir / "tools" / "orchestrator" / "fullstack_prompts"
        if prompts_dir.exists():
            for path in sorted(prompts_dir.glob("*.md")):
                if path.is_file():
                    register(Path("tools/orchestrator/fullstack_prompts") / path.name, path)
    else:
        for path in sorted(repo_root.glob("*.md")):
            if path.is_file():
                register(path.relative_to(repo_root), path)

        for base in ("timely-trackers", "templates", "snippets"):
            actual_root = repo_root / base
            if not actual_root.exists():
                continue
            for path in sorted(actual_root.rglob("*.md")):
                if path.is_file():
                    register(path.relative_to(repo_root), path)

        status_path = repo_root / ".orchestrator" / "STATUS.md"
        if status_path.exists():
            register(status_path.relative_to(repo_root), status_path)

        prompts_dir = repo_root / "tools" / "orchestrator" / "fullstack_prompts"
        if prompts_dir.exists():
            for path in sorted(prompts_dir.glob("*.md")):
                if path.is_file():
                    register(path.relative_to(repo_root), path)

    return [collected[key] for key in sorted(collected)]


def classify_path(relative_path: Path) -> tuple[str, str]:
    """Map a repo path to a stable Context Hub category and entry id suffix."""

    stem = relative_path.stem
    if relative_path == Path(".orchestrator/STATUS.md"):
        return "status", "status"
    if relative_path.parts and relative_path.parts[0] == "timely-trackers":
        return "tracker", f"tracker-{_slugify(stem)}"
    if relative_path.parts and relative_path.parts[0] == "templates":
        return "template", f"template-{_slugify(stem)}"
    if relative_path.parts and relative_path.parts[0] == "snippets":
        return "snippet", f"snippet-{_slugify(stem)}"
    if relative_path.parts[:3] == ("tools", "orchestrator", "fullstack_prompts"):
        prompt_name = re.sub(r"^\d+[_-]*", "", stem)
        return "prompt", f"prompt-{_slugify(prompt_name)}"
    return "root", _slugify(stem)


def derive_title(relative_path: Path, content: str) -> str:
    """Extract a human-readable title from the markdown content or file name."""

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    words = _slugify(relative_path.stem).replace("-", " ").strip()
    return words.title() if words else relative_path.stem


def extract_description(content: str, fallback: str) -> str:
    """Use the first prose paragraph as a searchable description."""

    paragraph: List[str] = []
    in_code = False
    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not stripped:
            if paragraph:
                break
            continue
        if stripped in {"---", "***"} or re.fullmatch(r"[-*]{3,}", stripped):
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("|") and not paragraph:
            continue
        cleaned = stripped.lstrip("> ").strip()
        if not cleaned:
            if paragraph:
                break
            continue
        if cleaned.startswith("- ") or cleaned.startswith("* ") or re.match(r"^\d+\.\s", cleaned):
            if paragraph:
                break
            continue
        paragraph.append(cleaned)
    if paragraph:
        return " ".join(paragraph)
    return fallback


def derive_tags(source: MirrorSource, override_tags: Iterable[str] | None = None) -> List[str]:
    """Derive stable tags from path, category, and override metadata."""

    tags = {"timely-playbook", "markdown", source.category}
    if source.category == "tracker":
        tags.add("governance")
    if source.category == "template":
        tags.add("scaffold")
    if source.category == "snippet":
        tags.add("shared")
    if source.category in {"prompt", "status"}:
        tags.add("orchestrator")
    if source.category == "prompt":
        tags.add("fullstack")

    for part in source.relative_path.parts:
        tags.update(_tokenize(part))

    for token in list(tags):
        if token in STOP_WORDS or token.isdigit():
            tags.discard(token)

    if override_tags:
        tags.update(_slugify(tag) for tag in override_tags if tag)

    return sorted(tag for tag in tags if tag)


def git_last_updated(repo_root: Path, relative_path: Path) -> str | None:
    """Return the last git commit date for a file when repo history is available."""

    if not (repo_root / ".git").exists():
        return None

    result = subprocess.run(
        ["git", "-C", str(repo_root), "log", "-1", "--format=%cs", "--", relative_path.as_posix()],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def last_updated_for(repo_root: Path, relative_path: Path) -> str:
    """Return git date when possible, otherwise fall back to the local file mtime."""

    git_date = git_last_updated(repo_root, relative_path)
    if git_date:
        return git_date
    workspace = resolve_workspace(repo_root=repo_root)
    source_path = repo_root / relative_path
    if workspace.relocated:
        if relative_path == Path("AGENTS.md"):
            source_path = workspace.local_dir / "AGENTS.md"
        elif relative_path == Path("SKILLS.md"):
            source_path = workspace.local_dir / "SKILLS.md"
        elif len(relative_path.parts) == 1 and relative_path.suffix == ".md":
            source_path = workspace.core_dir / relative_path
        elif relative_path.parts and relative_path.parts[0] == "timely-trackers":
            source_path = workspace.local_dir / relative_path
        elif relative_path.parts and relative_path.parts[0] in {"templates", "snippets"}:
            source_path = workspace.core_dir / relative_path
        elif relative_path == Path(".orchestrator/STATUS.md"):
            source_path = workspace.local_dir / relative_path
        elif relative_path.parts[:3] == ("tools", "orchestrator", "fullstack_prompts"):
            source_path = workspace.core_dir / relative_path
    stat = source_path.stat()
    return datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).date().isoformat()


def build_registry_payload(
    repo_root: Path,
    sources: Iterable[MirrorSource],
    author_dir: Path,
    overrides: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Copy markdown into the local source tree and emit author registry data."""

    docs: List[Dict[str, Any]] = []
    docs_root = author_dir / "docs"
    docs_root.mkdir(parents=True, exist_ok=True)

    for source in sources:
        repo_file = source.source_path
        override = overrides.get(source.relative_path.as_posix(), {})
        content = repo_file.read_text(encoding="utf-8")
        title = derive_title(source.relative_path, content)
        description = str(override.get("description") or extract_description(content, title))
        tags = derive_tags(source, override.get("tags"))
        last_updated = last_updated_for(repo_root, source.relative_path)

        entry_dir = docs_root / source.entry_name
        entry_dir.mkdir(parents=True, exist_ok=True)
        copied = entry_dir / "DOC.md"
        copied.write_text(content, encoding="utf-8")
        size = copied.stat().st_size

        docs.append(
            {
                "id": source.entry_id,
                "name": source.entry_name,
                "description": description,
                "source": "maintainer",
                "tags": tags,
                "languages": [
                    {
                        "language": "markdown",
                        "versions": [
                            {
                                "version": "current",
                                "path": source.content_path,
                                "files": ["DOC.md"],
                                "size": size,
                                "lastUpdated": last_updated,
                            }
                        ],
                        "recommendedVersion": "current",
                    }
                ],
            }
        )

    return {
        "version": "1.0.0",
        "docs": docs,
        "skills": [],
    }


def write_config(config_path: Path, dist_dir: Path) -> None:
    """Write a deterministic repo-local chub config."""

    config_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(
        [
            "# Managed by tools/chub/timely_registry.py",
            "sources:",
            "  - name: community",
            "    url: https://cdn.aichub.org/v1",
            "  - name: timely",
            f"    path: {dist_dir.resolve().as_posix()}",
            'source: "official,maintainer,community"',
            "refresh_interval: 21600",
            "telemetry: true",
            "",
        ]
    )
    config_path.write_text(content, encoding="utf-8")


def write_mirror_metadata(
    metadata_path: Path,
    repo_root: Path,
    chub_dir: Path,
    sources: Iterable[MirrorSource],
    registry_path: Path,
    config_path: Path,
    dist_dir: Path,
    payload: Dict[str, Any],
    overrides_path: Path,
    community_search_index: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    """Write a generated snapshot describing the local mirror inputs and outputs."""

    registry_bytes = registry_path.read_bytes()
    metadata = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "author": AUTHOR,
        "repo_root": repo_root.as_posix(),
        "chub_dir": chub_dir.as_posix(),
        "chub_dependency_version": _load_chub_dependency_version(repo_root),
        "docs": len(payload.get("docs", [])),
        "entry_ids": [doc.get("id") for doc in payload.get("docs", []) if isinstance(doc, dict)],
        "tracked_paths": [source.relative_path.as_posix() for source in sources],
        "registry_path": registry_path.as_posix(),
        "registry_sha256": hashlib.sha256(registry_bytes).hexdigest(),
        "config_path": config_path.as_posix(),
        "dist_dir": dist_dir.as_posix(),
        "overrides_path": overrides_path.resolve().as_posix(),
    }
    if community_search_index is not None:
        metadata["community_search_index"] = community_search_index

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def sync_community_search_index(chub_dir: Path, force: bool = False) -> Dict[str, str]:
    """Fetch the public search index used by multi-source remote searches."""

    target = chub_dir / "sources" / "community" / "search-index.json"
    if target.exists() and not force:
        return {"status": "cached", "path": target.as_posix()}

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(COMMUNITY_SEARCH_INDEX_URL, timeout=30) as response:
            data = response.read()
    except Exception as exc:
        return {
            "status": "warning",
            "path": target.as_posix(),
            "message": str(exc),
        }

    target.write_bytes(data)
    return {"status": "synced", "path": target.as_posix()}


def prepare_repo_local_chub(
    repo_root: Path = ROOT,
    chub_dir: Path | None = None,
    overrides_path: Path = OVERRIDES_PATH,
    sync_public_search_index: bool = False,
    force_public_search_index: bool = False,
) -> Dict[str, Any]:
    """Generate the Timely local source tree and repo-local config."""

    repo_root = repo_root.resolve()
    workspace = resolve_workspace(repo_root=repo_root)
    validate_core_manifest(workspace)
    chub_dir = (chub_dir or workspace.chub_dir).resolve()
    source_dir = chub_dir / "timely-source"
    dist_dir = chub_dir / "timely-dist"
    config_path = chub_dir / "config.yaml"

    overrides = _load_overrides(overrides_path)
    sources = collect_markdown_sources(repo_root)

    if source_dir.exists():
        shutil.rmtree(source_dir)

    author_dir = source_dir / AUTHOR
    author_dir.mkdir(parents=True, exist_ok=True)
    payload = build_registry_payload(repo_root, sources, author_dir, overrides)
    registry_path = author_dir / "registry.json"
    registry_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_config(config_path, dist_dir)
    community_search_index = None
    if sync_public_search_index:
        community_search_index = sync_community_search_index(
            chub_dir,
            force=force_public_search_index,
        )
    metadata_path = chub_dir / "timely-mirror-metadata.json"
    write_mirror_metadata(
        metadata_path=metadata_path,
        repo_root=repo_root,
        chub_dir=chub_dir,
        sources=sources,
        registry_path=registry_path,
        config_path=config_path,
        dist_dir=dist_dir,
        payload=payload,
        overrides_path=overrides_path,
        community_search_index=community_search_index,
    )

    summary = {
        "author": AUTHOR,
        "docs": len(payload["docs"]),
        "source_dir": source_dir.as_posix(),
        "dist_dir": dist_dir.as_posix(),
        "config_path": config_path.as_posix(),
        "registry_path": registry_path.as_posix(),
        "metadata_path": metadata_path.as_posix(),
    }
    if community_search_index is not None:
        summary["community_search_index"] = community_search_index
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare the Timely Playbook Context Hub mirror")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root to mirror")
    parser.add_argument(
        "--chub-dir",
        default=None,
        help="CHUB_DIR location; defaults to <repo>/.chub",
    )
    parser.add_argument(
        "--overrides",
        default=str(OVERRIDES_PATH),
        help="JSON metadata override file",
    )
    parser.add_argument(
        "--sync-community-search-index",
        action="store_true",
        help="Fetch the public search-index.json into CHUB_DIR when missing",
    )
    parser.add_argument(
        "--force-community-search-index",
        action="store_true",
        help="Force-refresh the public search-index.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = prepare_repo_local_chub(
        repo_root=Path(args.repo_root),
        chub_dir=Path(args.chub_dir) if args.chub_dir else None,
        overrides_path=Path(args.overrides),
        sync_public_search_index=args.sync_community_search_index,
        force_public_search_index=args.force_community_search_index,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
