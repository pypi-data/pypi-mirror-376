"""IR - Intermediate Representation of a file system."""

from pathlib import Path

import git
from pydantic import BaseModel, Field


class File(BaseModel):
    name: str


class EmptyFile(File):
    pass


class TextFile(File):
    content: str
    size: int
    lines: int


class TooLargeTextFile(File):
    size: int
    lines: int


class NonTextFile(File):
    size: int


class Dir(BaseModel):
    name: str
    subdirs: list["Dir"] = Field(default_factory=list)
    files: list[File] = Field(default_factory=list)


SNIFF_BYTES = 8 * 1024  # 8KB
NON_PRINTABLE_RATIO = 0.3
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5MB


def _has_nulls(chunk: bytes) -> bool:
    return b"\x00" in chunk


def _is_printable_byte(b: int) -> bool:
    if b in (9, 10, 12, 13):  # \t \n \f \r
        return True
    return 32 <= b <= 126


def _looks_text_by_ratio(chunk: bytes) -> bool:
    if not chunk:
        return True
    non_printable = sum(1 for b in chunk if not _is_printable_byte(b))
    return (non_printable / len(chunk)) < NON_PRINTABLE_RATIO


def _sniff_encoding_from_bom(chunk: bytes) -> str | None:
    # UTF-8 BOM
    if chunk.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    # UTF-16 LE/BE
    if chunk.startswith(b"\xff\xfe") and not chunk.startswith(b"\xff\xfe\x00\x00"):
        return "utf-16-le"
    if chunk.startswith(b"\xfe\xff"):
        return "utf-16-be"
    # UTF-32 LE/BE
    if chunk.startswith(b"\xff\xfe\x00\x00"):
        return "utf-32-le"
    if chunk.startswith(b"\x00\x00\xfe\xff"):
        return "utf-32-be"
    return None


def _detect_encoding(p: Path, head: bytes | None = None) -> str:
    if head is None:
        try:
            with p.open("rb") as f:
                head = f.read(SNIFF_BYTES)
        except (OSError, FileNotFoundError):
            return "utf-8"
    enc = _sniff_encoding_from_bom(head)
    return enc or "utf-8"


def _count_lines_stream(p: Path, encoding: str) -> int:
    try:
        with p.open("r", encoding=encoding, errors="ignore", newline=None) as f:
            return sum(1 for _ in f)
    except (OSError, UnicodeDecodeError, FileNotFoundError):
        return 0


def _count_lines_from_text(content: str) -> int:
    return len(content.splitlines())


def _is_probably_text(p: Path) -> bool:
    try:
        with p.open("rb") as f:
            chunk = f.read(SNIFF_BYTES)
    except (OSError, FileNotFoundError):
        return False

    if _has_nulls(chunk):
        return False

    if _sniff_encoding_from_bom(chunk):
        return True

    # UTF-8?
    try:
        chunk.decode("utf-8")  # errors='strict' by default
        return True
    except UnicodeDecodeError:
        pass

    # The last chance
    return _looks_text_by_ratio(chunk)


def _read_text_file(p: Path) -> tuple[str | None, str]:
    try:
        st = p.stat()
        if st.st_size == 0:
            return "", "utf-8"
        if st.st_size > MAX_FILE_BYTES:
            enc = _detect_encoding(p)
            return None, enc
    except FileNotFoundError:
        return None, "utf-8"

    try:
        enc = _detect_encoding(p)
        # newline=None включает universal newlines → CRLF нормализуется в \n
        with p.open("r", encoding=enc, errors="ignore", newline=None) as f:
            return f.read(), enc
    except (OSError, UnicodeDecodeError, FileNotFoundError):
        return None, "utf-8"


def _make_file_ir(file: Path) -> File:
    if not _is_probably_text(file):
        return NonTextFile(name=file.name, size=file.stat().st_size)

    content, enc = _read_text_file(file)

    try:
        size = file.stat().st_size
    except FileNotFoundError:
        size = 0

    if content is None:
        lines = _count_lines_stream(file, enc)
        return TooLargeTextFile(name=file.name, size=size, lines=lines)

    text = content.strip()
    if not text:
        return EmptyFile(name=file.name)

    lines = _count_lines_from_text(content)
    return TextFile(name=file.name, content=text, size=size, lines=lines)


def make_ir(path: Path, consider_git: bool = True) -> Dir:
    path = path.resolve()

    repo = None
    git_dir: Path | None = None
    if consider_git:
        try:
            repo = git.Repo(path, search_parent_directories=True)
            git_dir = Path(repo.git_dir).resolve()
        except git.exc.InvalidGitRepositoryError:
            consider_git = False
            repo = None
            git_dir = None

    def is_inside_git_dir(p: Path) -> bool:
        if not git_dir:
            return False
        try:
            p.resolve().relative_to(git_dir)
            return True
        except ValueError:
            return False

    def is_ignored_by_git(p: Path) -> bool:
        if not (consider_git and repo):
            return False
        try:
            return bool(repo.ignored(str(p)))
        except git.exc.GitCommandError:
            return False

    def build_dir(d: Path) -> Dir:
        node = Dir(name=d.name)

        try:
            entries = list(d.iterdir())
        except PermissionError:
            return node
        except FileNotFoundError:
            return node

        dirs = [e for e in entries if e.is_dir() and not e.is_symlink()]
        files = [e for e in entries if e.is_file() and not e.is_symlink()]

        for sd in sorted(dirs, key=lambda p: p.name):
            if sd.name == ".git":
                continue
            if consider_git and (is_inside_git_dir(sd) or is_ignored_by_git(sd)):
                continue
            node.subdirs.append(build_dir(sd))  # pylint: disable=no-member

        for f in sorted(files, key=lambda p: p.name):
            if consider_git:
                if is_inside_git_dir(f) or is_ignored_by_git(f):
                    continue

            node.files.append(_make_file_ir(f))  # pylint: disable=no-member

        return node

    if path.is_file():
        return Dir(name=str(path.parent), files=[_make_file_ir(path)])

    return build_dir(path)
