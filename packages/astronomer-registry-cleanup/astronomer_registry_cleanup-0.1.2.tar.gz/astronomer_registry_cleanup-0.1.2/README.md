# Astronomer Registry Cleanup

Minimal CLI to delete old Docker image tags in Astronomer registries.

## Install

```bash
pip install astronomer-registry-cleanup
```

## Usage

```bash
astronomer-registry-cleanup -r <registry> -p <token> <release_name> -f <prefix> (--keep-n-tags N | --drop-older-tags YYYY-MM-DD) [--dry-run]
```

## Behavior

- Auth: `-p` is your systemadmin token (username is not required).
- Tags considered: `<prefix>-<number>` only.
- Safety: never deletes if ≤ 1 tag exists for the prefix.
- Dry-run prints one line per planned deletion: `<release_name>:<tag> <digest>`.

## Examples

```bash
# Keep the latest 3 tags for prefix "deploy-" (dry-run)
astronomer-registry-cleanup -r registry.example.com -p <token> my-release -f deploy- --keep-n-tags 3 --dry-run

# Delete everything older than a date for prefix "cli-" (dry-run)
astronomer-registry-cleanup -r registry.example.com -p <token> my-release -f cli- --drop-older-tags 2025-08-01 --dry-run
```

## Notes

- Works against Docker Registry v2 auth flow via Houston.
