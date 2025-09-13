from __future__ import annotations
import argparse, sys
from .core import (
    init_repo, commit_snapshot, print_log,
    restore_paths, MinivcError, print_status, print_diff,
    branch_cmd, checkout_cmd
)

def _add_identity_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--name", help="Author name")
    p.add_argument("--email", help="Author email")

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="minivc", description="Minimal Git-like VCS (CLI only)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="Initialize a repository")
    _add_identity_flags(sp)
    sp.add_argument("--force", action="store_true", help="Reinitialize if already present")

    sp = sub.add_parser("commit", help="Create a new snapshot commit")
    sp.add_argument("-m", "--message", required=True, help="Commit message")
    _add_identity_flags(sp)
    sp.add_argument("--allow-empty", action="store_true", help="Allow empty commit if no changes")

    sp = sub.add_parser("log", help="Show commit history")
    sp.add_argument("--oneline", action="store_true", help="Short format")
    sp.add_argument("--max", type=int, help="Limit number of entries")

    sp = sub.add_parser("restore", help="Restore files/dirs from a commit (default HEAD)")
    sp.add_argument("paths", nargs="*", help="Paths to restore; empty means whole snapshot")
    sp.add_argument("--commit", default="HEAD", help="Commit hash (or HEAD)")
    sp.add_argument("--force", action="store_true", help="Overwrite modified files")

    sub.add_parser("status", help="Show changes vs HEAD")

    sp = sub.add_parser("diff", help="Show line differences vs HEAD")
    sp.add_argument("paths", nargs="*", help="Specific files to diff (optional)")

    sp = sub.add_parser("branch", help="List branches or create one")
    sp.add_argument("name", nargs="?", help="Branch name to create (omit to list)")

    sp = sub.add_parser("checkout", help="Switch to a branch or commit (detached)")
    sp.add_argument("ref", help="Branch name or commit hash/prefix")
    sp.add_argument("--force", action="store_true", help="Overwrite modified files")

    sp = sub.add_parser("merge", help="Merge another branch into the current branch")
    sp.add_argument("branch", help="Branch name to merge into the current branch")
    sp.add_argument("--force", action="store_true", help="Overwrite modified files in working tree if needed")
    sp.add_argument("-m", "--message", help="Custom merge commit message (used when auto-commit)")

    return p

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "init":
            init_repo(name=args.name, email=args.email, force=args.force)
        elif args.cmd == "commit":
            commit_snapshot(message=args.message, name=args.name, email=args.email, allow_empty=args.allow_empty)
        elif args.cmd == "log":
            print_log(oneline=args.oneline, max_n=args.max)
        elif args.cmd == "restore":
            restore_paths(paths=args.paths, commit_ref=args.commit, force=args.force)
        elif args.cmd == "status":
            print_status()
        elif args.cmd == "diff":
            print_diff(args.paths)
        elif args.cmd == "branch":
            branch_cmd(args.name)
        elif args.cmd == "checkout":
            checkout_cmd(args.ref, force=args.force)
        elif args.cmd == "merge":
            from .core import merge_cmd
            merge_cmd(args.branch, force=args.force, message=args.message)
        return 0
    except MinivcError as e:
        print(f"fatal: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())

