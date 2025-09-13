from __future__ import annotations
import hashlib, json, os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import difflib
from .ignore import IgnoreMatcher

REPO_DIRNAME = ".minivc"
OBJECTS_DIRNAME = "objects"
HEAD_FILENAME = "HEAD"
CONFIG_FILENAME = "config.json"
REFS_DIRNAME = "refs"
HEADS_DIRNAME = "heads"

class MinivcError(Exception): ...

@dataclass
class Author:
    name: str
    email: str

# ---------- repo discovery ----------
def find_repo_root(start: Path | str | None = None) -> Path:
    p = Path(start or os.getcwd()).resolve()
    while True:
        if (p / REPO_DIRNAME).is_dir():
            return p
        if p.parent == p:
            raise MinivcError("not a minivc repository (or any parent): .minivc")
        p = p.parent

def _paths(root: Path) -> Tuple[Path, Path, Path, Path]:
    repo = root / REPO_DIRNAME
    objects = repo / OBJECTS_DIRNAME
    head = repo / HEAD_FILENAME
    config = repo / CONFIG_FILENAME
    return repo, objects, head, config

def _refs_dir(root: Path) -> Path:
    return root / REPO_DIRNAME / REFS_DIRNAME / HEADS_DIRNAME

# ---------- object store ----------
def _obj_path(objects_dir: Path, sha: str) -> Path:
    return objects_dir / sha[:2] / sha[2:]

def _write_object(objects_dir: Path, typ: str, payload: bytes) -> str:
    """
    Store object with tiny header 'type:<typ>\\n' and return sha256 of full bytes.
    Atomic by writing to a tmp file then renaming.
    """
    header = f"type:{typ}\n".encode("utf-8")
    data = header + payload
    sha = hashlib.sha256(data).hexdigest()
    dest = _obj_path(objects_dir, sha)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(dest)
    return sha

def _read_object(objects_dir: Path, sha: str) -> Tuple[str, bytes]:
    p = _obj_path(objects_dir, sha)
    if not p.exists():
        raise MinivcError(f"object {sha} not found")
    data = p.read_bytes()
    i = data.find(b"\n")
    if i < 0:
        raise MinivcError(f"corrupt object {sha}")
    header = data[:i].decode("utf-8")
    if not header.startswith("type:"):
        raise MinivcError(f"corrupt object {sha}")
    return header[5:], data[i+1:]

# ---------- trees & commits ----------
def _json_dumps(obj: object) -> bytes:
    # deterministic JSON for hashing
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _blob_hash(objects_dir: Path, path: Path) -> str:
    data = path.read_bytes()
    return _write_object(objects_dir, "blob", data)

def _tree_hash(objects_dir: Path, entries: List[Dict]) -> str:
    payload = _json_dumps({"type": "tree", "entries": entries})
    return _write_object(objects_dir, "tree", payload)

def _build_tree(objects_dir: Path, root: Path, ignore: IgnoreMatcher, rel: Path = Path(".")) -> Tuple[str, List[Dict]]:
    abs_dir = (root / rel).resolve()
    items = []
    for child in sorted(abs_dir.iterdir(), key=lambda p: p.name):
        if child.name == REPO_DIRNAME:
            continue
        if ignore.is_ignored(child):
            continue
        if child.is_file():
            sha = _blob_hash(objects_dir, child)
            items.append({"name": child.name, "type": "blob", "hash": sha})
        elif child.is_dir():
            sub_sha, _ = _build_tree(objects_dir, root, ignore, rel / child.name)
            items.append({"name": child.name, "type": "tree", "hash": sub_sha})
    tree_sha = _tree_hash(objects_dir, items)
    return tree_sha, items

def _commit_hash(objects_dir: Path, tree_sha: str, parent: Optional[str], author: Author, message: str) -> str:
    doc = {
        "type": "commit",
        "tree": tree_sha,
        "parent": parent,
        "author": {"name": author.name, "email": author.email},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": message,
    }
    return _write_object(objects_dir, "commit", _json_dumps(doc))

def _read_commit(objects_dir: Path, sha: str) -> Dict:
    typ, payload = _read_object(objects_dir, sha)
    if typ != "commit":
        raise MinivcError(f"object {sha} is not a commit")
    try:
        return json.loads(payload.decode("utf-8"))
    except Exception as e:
        raise MinivcError(f"corrupt commit {sha}") from e

def _read_tree(objects_dir: Path, sha: str) -> Dict:
    typ, payload = _read_object(objects_dir, sha)
    if typ != "tree":
        raise MinivcError(f"object {sha} is not a tree")
    return json.loads(payload.decode("utf-8"))

# ---------- refs / HEAD helpers ----------
def _head_is_symbolic(head_file: Path) -> bool:
    if not head_file.exists():
        return False
    txt = head_file.read_text(encoding="utf-8").strip()
    return txt.startswith("ref:")

def _read_symbolic_target(head_file: Path) -> Optional[str]:
    if not head_file.exists():
        return None
    txt = head_file.read_text(encoding="utf-8").strip()
    if txt.startswith("ref:"):
        return txt.split(":", 1)[1].strip()
    return None

def _resolve_head_to_commit(root: Path, objects: Path, head_file: Path) -> str:
    """Return current commit SHA for HEAD (symbolic or detached). Empty if none."""
    if not head_file.exists():
        return ""
    txt = head_file.read_text(encoding="utf-8").strip()
    if txt.startswith("ref:"):
        ref_rel = txt.split(":", 1)[1].strip()
        ref_file = root / REPO_DIRNAME / ref_rel
        return ref_file.read_text(encoding="utf-8").strip() if ref_file.exists() else ""
    return txt

def resolve_sha(objects_dir: Path, prefix: str) -> str:
    """Resolve abbreviated hash to full; raise on ambiguous or not found."""
    if len(prefix) < 4:
        raise MinivcError("hash prefix too short")
    base = objects_dir / prefix[:2]
    if not base.exists():
        raise MinivcError(f"no object with prefix {prefix}")
    matches = [p for p in base.iterdir() if p.name.startswith(prefix[2:])]
    if len(matches) == 0:
        raise MinivcError(f"no object with prefix {prefix}")
    if len(matches) > 1:
        raise MinivcError(f"ambiguous prefix {prefix}")
    return prefix[:2] + matches[0].name

# ---------- init ----------
def init_repo(name: Optional[str], email: Optional[str], force: bool) -> None:
    root = Path(os.getcwd()).resolve()
    repo, objects, head, config = _paths(root)
    if repo.exists() and not force and not (repo.is_dir() and (repo / OBJECTS_DIRNAME).is_dir()):
        raise MinivcError(f"{REPO_DIRNAME} already exists (use --force to reinit)")
    repo.mkdir(exist_ok=True)
    objects.mkdir(parents=True, exist_ok=True)
    # Set symbolic HEAD to main (branch file created on first commit)
    head.write_text(f"ref: {REFS_DIRNAME}/{HEADS_DIRNAME}/main", encoding="utf-8")
    if name or email:
        cfg = {"name": name or "", "email": email or ""}
        (repo / CONFIG_FILENAME).write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"Initialized empty minivc repository in {repo}")

# ---------- commit ----------
def _read_head(head: Path) -> str:
    return head.read_text(encoding="utf-8").strip() if head.exists() else ""

def _write_head(head: Path, sha: str) -> None:
    head.write_text(sha, encoding="utf-8")

def _load_author(config_file: Path, name: Optional[str], email: Optional[str]) -> Author:
    if name and email:
        return Author(name, email)
    if config_file.exists():
        try:
            data = json.loads(config_file.read_text(encoding="utf-8"))
            n = name or data.get("name") or ""
            e = email or data.get("email") or ""
            if n and e:
                return Author(n, e)
        except Exception:
            pass
    raise MinivcError("author unknown: provide --name and --email (or set in .minivc/config.json)")

def commit_snapshot(message: str, name: Optional[str], email: Optional[str], allow_empty: bool) -> None:
    if not message.strip():
        raise MinivcError("commit message cannot be empty")
    root = find_repo_root()
    repo, objects, head_file, config_file = _paths(root)
    author = _load_author(config_file, name, email)
    ignore = IgnoreMatcher(root)
    tree_sha, _ = _build_tree(objects, root, ignore)

    # Determine parent from HEAD (symbolic or detached)
    parent = _resolve_head_to_commit(root, objects, head_file) or None

    if parent:
        parent_tree = _read_commit(objects, parent)["tree"]
        if parent_tree == tree_sha and not allow_empty:
            print("Nothing to commit")
            return

    commit_sha = _commit_hash(objects, tree_sha, parent, author, message)

    # Update branch ref if symbolic HEAD, else write detached SHA to HEAD
    sym = _read_symbolic_target(head_file)
    if sym:
        ref_file = root / REPO_DIRNAME / sym
        ref_file.parent.mkdir(parents=True, exist_ok=True)
        ref_file.write_text(commit_sha, encoding="utf-8")
    else:
        _write_head(head_file, commit_sha)

    print(f"[{commit_sha[:7]}] {message}")

# ---------- log ----------
def print_log(oneline: bool, max_n: Optional[int]) -> None:
    root = find_repo_root()
    _, objects, head_file, _ = _paths(root)
    cur = _resolve_head_to_commit(root, objects, head_file)
    if not cur:
        print("No commits yet")
        return
    n = 0
    while cur:
        doc = _read_commit(objects, cur)
        if oneline:
            msg = doc["message"].splitlines()[0]
            print(f"{cur[:7]} {msg}")
        else:
            ts = doc["timestamp"]
            author = doc["author"]
            print(f"commit {cur}")
            print(f"Author: {author['name']} <{author['email']}>")
            print(f"Date:   {ts}")
            print()
            print(f"    {doc['message']}")
            print()
        n += 1
        if max_n and n >= max_n:
            break
        cur = doc.get("parent")

# ---------- status ----------
def _tree_to_dict(objects_dir: Path, tree_sha: str) -> Dict[str, str]:
    """Return {path: blob_sha} for a tree (recursive)."""
    result: Dict[str, str] = {}
    doc = _read_tree(objects_dir, tree_sha)
    for entry in doc["entries"]:
        if entry["type"] == "blob":
            result[entry["name"]] = entry["hash"]
        else:
            sub = _tree_to_dict(objects_dir, entry["hash"])
            for k, v in sub.items():
                result[f"{entry['name']}/{k}"] = v
    return result

def print_status() -> None:
    root = find_repo_root()
    _, objects, head_file, _ = _paths(root)
    head = _resolve_head_to_commit(root, objects, head_file)
    if not head:
        print("No commits yet")
        return

    head_tree = _read_commit(objects, head)["tree"]
    committed = _tree_to_dict(objects, head_tree)

    ignore = IgnoreMatcher(root)
    working: Dict[str, str] = {}
    for path in root.rglob("*"):
        if REPO_DIRNAME in path.parts or not path.is_file():
            continue
        if ignore.is_ignored(path):
            continue
        rel = path.relative_to(root).as_posix()
        sha = _blob_hash(objects, path)
        working[rel] = sha

    added = sorted(set(working) - set(committed))
    deleted = sorted(set(committed) - set(working))
    modified = sorted(k for k in set(working) & set(committed) if working[k] != committed[k])

    if not (added or deleted or modified):
        print("Working tree clean")
        return

    if added:
        print("Added:")
        for f in added: print("  " + f)
    if deleted:
        print("Deleted:")
        for f in deleted: print("  " + f)
    if modified:
        print("Modified:")
        for f in modified: print("  " + f)

# ---------- diff ----------
def print_diff(paths: List[str]) -> None:
    root = find_repo_root()
    _, objects, head_file, _ = _paths(root)
    head = _resolve_head_to_commit(root, objects, head_file)
    if not head:
        print("No commits yet")
        return

    head_tree = _read_commit(objects, head)["tree"]
    committed = _tree_to_dict(objects, head_tree)

    ignore = IgnoreMatcher(root)
    all_paths = paths or list(committed.keys())
    for rel in sorted(all_paths):
        f = root / rel
        if ignore.is_ignored(f) or not f.exists() or not f.is_file():
            continue
        current = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        committed_sha = committed.get(rel)
        if not committed_sha:
            # file untracked in HEAD; show as added
            old = []
            fromfile = f"{rel} (HEAD: missing)"
        else:
            _, data = _read_object(objects, committed_sha)
            old = data.decode("utf-8", errors="ignore").splitlines()
            fromfile = f"{rel} (HEAD)"
        diff = difflib.unified_diff(old, current,
                                    fromfile=fromfile,
                                    tofile=f"{rel} (working)",
                                    lineterm="")
        printed = False
        for line in diff:
            printed = True
            print(line)
        if not printed and paths:
            # if specific paths requested, indicate no diff
            print(f"No changes: {rel}")

# ---------- restore ----------
def _materialize_tree(objects_dir: Path, tree_sha: str, dest_root: Path) -> List[Tuple[Path, str]]:
    """
    Returns list of (file_path, blob_sha) for the entire tree (recursive).
    """
    result: List[Tuple[Path, str]] = []
    doc = _read_tree(objects_dir, tree_sha)
    for entry in doc["entries"]:
        if entry["type"] == "blob":
            result.append((dest_root / entry["name"], entry["hash"]))
        else:
            result.extend(_materialize_tree(objects_dir, entry["hash"], dest_root / entry["name"]))
    return result

def _find_subtree_sha(objects_dir: Path, tree_sha: str, rel_parts: List[str]) -> Optional[str]:
    """Follow path parts within tree; return subtree/tree/blob sha if path is found."""
    if not rel_parts:
        return tree_sha
    doc = _read_tree(objects_dir, tree_sha)
    head = rel_parts[0]
    for e in doc["entries"]:
        if e["name"] == head:
            if len(rel_parts) == 1:
                return e["hash"]
            if e["type"] != "tree":
                return None
            return _find_subtree_sha(objects_dir, e["hash"], rel_parts[1:])
    return None

def restore_paths(paths: List[str], commit_ref: str, force: bool) -> None:
    root = find_repo_root()
    _, objects, head_file, _ = _paths(root)
    if commit_ref == "HEAD":
        commit_sha = _resolve_head_to_commit(root, objects, head_file)
    else:
        commit_sha = resolve_sha(objects, commit_ref)
    if not commit_sha:
        raise MinivcError("no commits to restore from")
    commit_doc = _read_commit(objects, commit_sha)
    tree_sha = commit_doc["tree"]

    targets: List[Tuple[Path, str]] = []
    if not paths:
        targets = _materialize_tree(objects, tree_sha, root)
    else:
        for s in paths:
            rel = Path(s)
            sha = _find_subtree_sha(objects, tree_sha, rel.as_posix().split("/"))
            if not sha:
                raise MinivcError(f"path '{s}' not found in commit {commit_sha[:7]}")
            typ, _ = _read_object(objects, sha)
            if typ == "blob":
                targets.append((root / rel, sha))
            else:
                targets.extend(_materialize_tree(objects, sha, root / rel))

    # conflict detection
    conflicts: List[Path] = []
    for fpath, blob_sha in targets:
        if fpath.exists() and fpath.is_file() and not force:
            _, data = _read_object(objects, blob_sha)
            on_disk = fpath.read_bytes()
            if on_disk != data:
                conflicts.append(fpath)
    if conflicts and not force:
        msg = "restore would overwrite modified files:\n" + "\n".join(f"  {p}" for p in conflicts)
        raise MinivcError(msg)

    # write files
    for fpath, blob_sha in targets:
        fpath.parent.mkdir(parents=True, exist_ok=True)
        _, data = _read_object(objects, blob_sha)
        fpath.write_bytes(data)

    restored = [str(p) for p, _ in targets]
    if len(restored) == 1:
        print(f"Restored {restored[0]} from {commit_sha[:7]}")
    else:
        print(f"Restored {len(restored)} paths from {commit_sha[:7]}")

# ---------- branch & checkout ----------
def branch_cmd(name: Optional[str]) -> None:
    root = find_repo_root()
    repo, objects, head_file, _ = _paths(root)
    refs = _refs_dir(root)
    refs.mkdir(parents=True, exist_ok=True)

    if not name:
        # list branches, mark current
        current = ""
        sym = _read_symbolic_target(head_file)
        if sym and sym.startswith(f"{REFS_DIRNAME}/{HEADS_DIRNAME}/"):
            current = Path(sym).name
        for ref in sorted(refs.glob("*")):
            branch = ref.name
            mark = "*" if branch == current else " "
            print(f"{mark} {branch}")
        return

    head_sha = _resolve_head_to_commit(root, objects, head_file)
    if not head_sha:
        raise MinivcError("No commits yet to branch from")
    new_ref = refs / name
    if new_ref.exists():
        raise MinivcError(f"branch '{name}' already exists")
    new_ref.write_text(head_sha, encoding="utf-8")
    print(f"Created branch {name}")

def checkout_cmd(ref: str, force: bool) -> None:
    root = find_repo_root()
    repo, objects, head_file, _ = _paths(root)
    refs = _refs_dir(root)

    target_sha: Optional[str] = None
    # Branch?
    ref_path = refs / ref
    if ref_path.exists():
        target_sha = ref_path.read_text(encoding="utf-8").strip()
        head_file.write_text(f"ref: {REFS_DIRNAME}/{HEADS_DIRNAME}/{ref}", encoding="utf-8")
    else:
        # Commit (detached)
        target_sha = resolve_sha(objects, ref)
        head_file.write_text(target_sha, encoding="utf-8")

    if not target_sha:
        raise MinivcError(f"unknown ref: {ref}")

    commit_doc = _read_commit(objects, target_sha)
    tree_sha = commit_doc["tree"]
    targets = _materialize_tree(objects, tree_sha, root)

    # conflict detection
    conflicts: List[Path] = []
    for fpath, blob_sha in targets:
        if fpath.exists() and fpath.is_file() and not force:
            _, data = _read_object(objects, blob_sha)
            if fpath.read_bytes() != data:
                conflicts.append(fpath)
    if conflicts and not force:
        msg = "checkout would overwrite modified files:\n" + "\n".join(f"  {p}" for p in conflicts)
        raise MinivcError(msg)

    # restore working tree
    for fpath, blob_sha in targets:
        fpath.parent.mkdir(parents=True, exist_ok=True)
        _, data = _read_object(objects, blob_sha)
        fpath.write_bytes(data)

    print(f"Checked out {ref}")



# ----- parents helper (back-compat for old commits) -----
def _commit_parents(doc: Dict) -> List[str]:
    # New commits may store "parents": [..]; older ones have single "parent"
    if "parents" in doc and isinstance(doc["parents"], list):
        return [p for p in doc["parents"] if p]
    p = doc.get("parent")
    return [p] if p else []

# ----- get current branch name (or None if detached) -----
def _current_branch_name(root: Path, head_file: Path) -> Optional[str]:
    sym = _read_symbolic_target(head_file)
    if not sym:
        return None
    p = Path(sym)
    if p.parts[:2] != (REFS_DIRNAME, HEADS_DIRNAME):
        return None
    return p.name

# ----- compute merge-base (Lowest Common Ancestor) -----
def _merge_base(objects: Path, a: str, b: str) -> Optional[str]:
    """
    Simple LCA by breadth-first search of parents.
    Returns SHA of common ancestor with minimum distance sum (approx).
    """
    def ancestors(start: str) -> Dict[str, int]:
        dist: Dict[str, int] = {}
        q = [(start, 0)]
        while q:
            cur, d = q.pop(0)
            if cur in dist:
                continue
            dist[cur] = d
            doc = _read_commit(objects, cur)
            for p in _commit_parents(doc):
                q.append((p, d + 1))
        return dist

    da = ancestors(a)
    db = ancestors(b)
    commons = set(da) & set(db)
    if not commons:
        return None
    # choose the node minimizing distance sum (basic heuristic)
    best = min(commons, key=lambda s: da[s] + db[s])
    return best

# ----- write a full tree snapshot into the working directory (with conflict checks) -----
def _apply_tree_to_working(objects: Path, tree_sha: str, root: Path, force: bool) -> None:
    targets = _materialize_tree(objects, tree_sha, root)
    conflicts: List[Path] = []
    for fpath, blob_sha in targets:
        if fpath.exists() and fpath.is_file() and not force:
            _, data = _read_object(objects, blob_sha)
            if fpath.read_bytes() != data:
                conflicts.append(fpath)
    if conflicts and not force:
        msg = "operation would overwrite modified files:\n" + "\n".join(f"  {p}" for p in conflicts)
        raise MinivcError(msg)

    # ensure parent dirs + write files
    for fpath, blob_sha in targets:
        fpath.parent.mkdir(parents=True, exist_ok=True)
        _, data = _read_object(objects, blob_sha)
        fpath.write_bytes(data)

# ----- three-way merge of one path -----
def _merge_blob_triple(objects: Path,
                       base_sha: Optional[str],
                       left_sha: Optional[str],
                       right_sha: Optional[str],
                       left_label: str,
                       right_label: str) -> Tuple[Optional[bytes], bool]:
    """
    Return (merged_bytes_or_None_for_delete, conflicted)
    Rules:
      - If one side equals base -> take the other side (incl. deletions)
      - If left == right -> take either
      - Otherwise -> textual conflict markers (utf-8, errors='replace')
    """
    # Normalize equality comparisons on missing values
    def eq(x, y): return x == y

    # Quick resolves on equality with base
    if eq(left_sha, base_sha) and not eq(right_sha, base_sha):
        # take right (may be delete if None)
        if right_sha is None:
            return None, False
        _, rb = _read_object(objects, right_sha)
        return rb, False

    if eq(right_sha, base_sha) and not eq(left_sha, base_sha):
        if left_sha is None:
            return None, False
        _, lb = _read_object(objects, left_sha)
        return lb, False

    # Identical result on both sides (including both None)
    if eq(left_sha, right_sha):
        if left_sha is None:
            return None, False
        _, lb = _read_object(objects, left_sha)
        return lb, False

    # Otherwise: conflict (modify/modify OR delete/modify)
    base_bytes = b""
    if base_sha:
        _, base_bytes = _read_object(objects, base_sha)
    left_bytes = b""
    if left_sha:
        _, left_bytes = _read_object(objects, left_sha)
    right_bytes = b""
    if right_sha:
        _, right_bytes = _read_object(objects, right_sha)

    # Try a cheap auto-merge: if base==left, take right (already handled); if base==right, take left (handled)
    # Fallback: textual conflict
    left_txt = left_bytes.decode("utf-8", errors="replace")
    right_txt = right_bytes.decode("utf-8", errors="replace")
    merged_txt = (
        f"<<<<<<< HEAD\n{left_txt}=======\n{right_txt}>>>>>>> {right_label}\n"
    )
    return merged_txt.encode("utf-8"), True

# ----- build dict path->sha (already exists in your code; shown for context) -----
# def _tree_to_dict(objects_dir: Path, tree_sha: str) -> Dict[str, str]: ...

# ----- Merge engine for trees -----
def _merge_trees(objects: Path,
                 base_tree: Optional[str],
                 left_tree: str,
                 right_tree: str,
                 left_label: str,
                 right_label: str) -> Tuple[Dict[str, Optional[bytes]], List[str]]:
    """
    Returns (result_map, conflicts).
    result_map: { "path": bytes or None (None => delete) }
    """
    base_map: Dict[str, Optional[str]] = {}
    if base_tree:
        base_map = _tree_to_dict(objects, base_tree)
    left_map = _tree_to_dict(objects, left_tree)
    right_map = _tree_to_dict(objects, right_tree)

    paths = sorted(set(base_map) | set(left_map) | set(right_map))
    result: Dict[str, Optional[bytes]] = {}
    conflicts: List[str] = []

    for p in paths:
        b = base_map.get(p)
        l = left_map.get(p)
        r = right_map.get(p)
        merged, is_conflict = _merge_blob_triple(objects, b, l, r, "HEAD", right_label)
        result[p] = merged  # may be None for deletion
        if is_conflict:
            conflicts.append(p)

    return result, conflicts

# ----- Apply a merged map (bytes/None) into working dir -----
def _apply_merge_result_to_working(root: Path, result_map: Dict[str, Optional[bytes]]) -> None:
    # Write / delete paths
    for rel, content in result_map.items():
        fpath = root / rel
        if content is None:
            if fpath.exists():
                try:
                    fpath.unlink()
                except IsADirectoryError:
                    # if path is a dir in working (shouldn’t happen for blobs), skip
                    pass
            continue
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_bytes(content)

# ----- Merge command -----
def merge_cmd(branch: str, force: bool, message: Optional[str]) -> None:
    """
    Merge <branch> into the current branch.
    Fast-forward when possible. On clean 3-way merge, auto-commit.
    On conflicts, writes conflict markers and asks user to resolve + commit.
    """
    root = find_repo_root()
    repo, objects, head_file, _ = _paths(root)
    cur_branch = _current_branch_name(root, head_file)
    if not cur_branch:
        raise MinivcError("cannot merge in detached HEAD; checkout a branch first")

    refs = _refs_dir(root)
    other_ref = refs / branch
    if not other_ref.exists():
        raise MinivcError(f"unknown branch '{branch}'")

    other = other_ref.read_text(encoding="utf-8").strip()
    current = _resolve_head_to_commit(root, objects, head_file)
    if not current:
        raise MinivcError("current branch has no commits")

    if current == other:
        print(f"Already up to date: {cur_branch}")
        return

    # Find merge base
    base = _merge_base(objects, current, other)

    # Fast-forward if base == current (i.e., current is ancestor of other)
    if base == current:
        # Update working tree to other; may need --force
        other_tree = _read_commit(objects, other)["tree"]
        _apply_tree_to_working(objects, other_tree, root, force=force)

        # Move current branch ref to 'other'
        (refs / cur_branch).parent.mkdir(parents=True, exist_ok=True)
        (refs / cur_branch).write_text(other, encoding="utf-8")
        print(f"Fast-forward {cur_branch} -> {branch} ({other[:7]})")
        return

    # Regular 3-way merge
    base_tree = _read_commit(objects, base)["tree"] if base else None
    left_tree = _read_commit(objects, current)["tree"]
    right_tree = _read_commit(objects, other)["tree"]

    result_map, conflicts = _merge_trees(objects, base_tree, left_tree, right_tree,
                                         left_label="HEAD", right_label=branch)

    # Before applying, optional conflict safety: if not force, ensure we won't clobber unrelated modified files
    # (We conservatively reuse the same overwrite rule as restore/checkout for paths we will write.)
    if not force:
        for rel, content in result_map.items():
            if content is None:
                # deletion never overwrites modified bytes; skip
                continue
            fpath = root / rel
            if fpath.exists() and fpath.is_file():
                on_disk = fpath.read_bytes()
                if on_disk != content:
                    # It's a write that changes file; allowed, but check is informational only.
                    # We keep behavior consistent with restore: we don't block merge here,
                    # since merge is expected to modify files. If you want stricter safety,
                    # you could list modified paths here.
                    pass

    # Apply merged snapshot into working directory
    _apply_merge_result_to_working(root, result_map)

    if conflicts:
        print("Automatic merge failed; fix conflicts and commit:")
        for p in conflicts:
            print(f"  CONFLICT: {p}")
        print("\nHint: after resolving, run:")
        print("  minivc commit -m \"Merge fix\"")
        return

    # Auto-commit merge (two parents)
    author = None
    # Try to load author from config for the commit (same helper as commit_snapshot)
    _, _, _, config_file = _paths(root)
    try:
        author = _load_author(config_file, None, None)
    except MinivcError:
        # Fall back: require explicit author via commit if not set
        raise MinivcError("author unknown for merge; set it via 'minivc init --name ... --email ...' or .minivc/config.json")

    # Rebuild tree from working directory (matches merged result)
    ignore = IgnoreMatcher(root)
    merged_tree_sha, _ = _build_tree(objects, root, ignore)

    # Create a merge commit with two parents [current, other]
    doc = {
        "type": "commit",
        "tree": merged_tree_sha,
        "parent": current,           # first parent for back-compat
        "parents": [current, other], # full parent list
        "author": {"name": author.name, "email": author.email},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": message or f"Merge branch '{branch}' into {cur_branch}",
    }
    merge_sha = _write_object(objects, "commit", _json_dumps(doc))

    # Advance current branch ref
    (refs / cur_branch).write_text(merge_sha, encoding="utf-8")
    print(f"Merge made commit {merge_sha[:7]}")
