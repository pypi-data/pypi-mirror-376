from __future__ import annotations
from pathlib import Path
from fnmatch import fnmatch

class IgnoreMatcher:
    """
    Minimal ignore rules
    """
    def __init__(self, root: Path) -> None:
        self.root = root
        self.patterns: list[str] = []
        f = root / ".minivcignore"
        if f.exists():
            for raw in f.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.endswith("/"):
                    self.patterns.append(line.rstrip("/") + "/**")
                else:
                    self.patterns.append(line)

    def is_ignored(self, p: Path) -> bool:
        rel = p.relative_to(self.root).as_posix()
        base = p.name
        for pat in self.patterns:
            if "/" in pat:
                if fnmatch(rel, pat) or fnmatch(rel + "/", pat):
                    return True
            if fnmatch(base, pat):
                return True
        return False
