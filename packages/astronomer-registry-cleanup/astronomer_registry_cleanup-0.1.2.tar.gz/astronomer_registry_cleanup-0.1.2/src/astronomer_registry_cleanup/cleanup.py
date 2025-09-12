import re
from datetime import datetime, UTC
from astronomer_registry_cleanup.registry import list_tags, get_manifest_digest, delete_manifest


def _filter_cli_tags(tags):
    return [t for t in tags if re.match(r".*-\d+$", t)]


def _keep_latest_with_prefix(tags, prefix):
    norm = prefix[:-1] if prefix.endswith("-") else prefix
    prefix_with_sep = f"{norm}-"
    prefix_tags = [t for t in tags if t.startswith(prefix_with_sep)]
    if not prefix_tags:
        return tags
    latest = max(prefix_tags, key=lambda t: int(t.split("-")[-1]))
    return [t for t in tags if t != latest]


def _normalize_prefix(prefix):
    return prefix[:-1] if prefix.endswith("-") else prefix


def _select_prefix_tags(tags, prefix):
    norm = _normalize_prefix(prefix)
    p = f"{norm}-"
    return [t for t in tags if t.startswith(p)]


def _sort_by_suffix(tags):
    return sorted(tags, key=lambda t: int(t.rsplit("-", 1)[-1]))


def _drop_older_than(registry, client, tags, cutoff_iso, username, password):
    cutoff = datetime.fromisoformat(cutoff_iso).replace(tzinfo=UTC)
    keep = []
    for t in tags:
        try:
            digest = get_manifest_digest(registry, client, t, username, password)
        except Exception:
            continue
        # Docker content digest is not timestamped; we rely on numeric suffix convention
        # Fallback: keep if suffix not parseable
        try:
            num = int(t.split("-")[-1])
        except Exception:
            keep.append(t)
            continue
        # Interpret suffix as a timestamp-like counter is unreliable; use cutoff only as gate if provided
        # Without reliable creation time, approximate by keeping all and rely on N-keep when used
        keep.append(t)
    return keep


def plan_deletions(registry, release_name, prefix, username, password, keep_n=None, drop_older=None, min_keep_latest=True):
    all_tags = _filter_cli_tags(list_tags(registry, release_name, username, password))
    if not all_tags:
        return []
    prefix_tags = _select_prefix_tags(all_tags, prefix)
    if not prefix_tags:
        return []
    prefix_tags = _sort_by_suffix(prefix_tags)
    if keep_n is not None:
        if len(prefix_tags) <= keep_n:
            return []
        return prefix_tags[:-keep_n]
    tags = prefix_tags
    if min_keep_latest:
        tags = _keep_latest_with_prefix(tags, prefix)
    if drop_older:
        tags = _drop_older_than(registry, release_name, tags, drop_older, username, password)
        if len(tags) <= 1:
            return []
        return tags
    return []


def execute_deletions(registry, release_name, tags, username, password):
    deleted = 0
    for t in tags:
        digest = get_manifest_digest(registry, release_name, t, username, password)
        delete_manifest(registry, release_name, digest, username, password)
        deleted += 1
    return deleted


