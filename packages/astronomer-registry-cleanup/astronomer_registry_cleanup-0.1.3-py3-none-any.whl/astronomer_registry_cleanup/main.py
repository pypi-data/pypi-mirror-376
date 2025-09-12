import argparse
import logging
import sys
from astronomer_registry_cleanup.cleanup import plan_deletions, execute_deletions
from astronomer_registry_cleanup.registry import get_manifest_digest

def setup_logging():
    logging.basicConfig(level=logging.ERROR, stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s")

def cmd_run(args):
    setup_logging()
    username = ""
    to_delete = plan_deletions(
        args.registry,
        args.release_name,
        args.prefix,
        username,
        args.password,
        keep_n=args.keep_n_tags if not args.drop_older_tags else None,
        drop_older=args.drop_older_tags,
    )
    if args.dry_run:
        for t in to_delete:
            d = get_manifest_digest(args.registry, args.release_name, t, username, args.password)
            print(f"{args.release_name}:{t} {d}")
        return 0
    execute_deletions(args.registry, args.release_name, to_delete, username, args.password)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--registry", required=True)
    parser.add_argument("-p", "--password", required=True)
    parser.add_argument("release_name")
    parser.add_argument("-f", "--prefix", required=True)
    mex = parser.add_mutually_exclusive_group(required=True)
    mex.add_argument("--keep-n-tags", dest="keep_n_tags", type=int)
    mex.add_argument("--drop-older-tags", dest="drop_older_tags")
    parser.add_argument("--dry-run", action="store_true")
    parser.set_defaults(func=cmd_run)

    args = parser.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
