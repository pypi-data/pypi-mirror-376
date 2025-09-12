from .ir import Dir, EmptyFile, File, NonTextFile, TextFile, TooLargeTextFile


def _form_str_summary(ir: Dir) -> str:
    """Summary of the path tree.

    Example:
        Path summary:
        vibe/.flake8 [size 77B, 4 lines]
        vibe/.gitignore [size 4.4KB, 216 lines]
        vibe/.isort.cfg [size 250B, 10 lines]
        vibe/.pylintrc [size 181B, 8 lines]
        vibe/Makefile [size 194B, 8 lines]
        vibe/README.md [size 2.8KB, 90 lines]
        vibe/poetry.lock [size 35.4KB, 567 lines]
        vibe/poetry.toml [size 46B, 3 lines]
        vibe/pyproject.toml [size 668B, 30 lines]
        vibe/src/vibe/__init__.py [size 0B, empty file]
        vibe/src/vibe/__main__.py [size 60B, 4 lines]
        vibe/src/vibe/form_context.py [size 3.1KB, 96 lines]
        vibe/src/vibe/ir.py [size 5.7KB, 230 lines]
        vibe/src/vibe/main.py [size 4.7KB, 136 lines]
        vibe/tests/__init__.py [size 0B, empty file]
        == 15 files, 3 dirs, total 57.6KB, 1402 lines
    """
    lines: list[str] = ["Path summary:"]
    total_size = 0
    total_lines = 0
    file_count = 0
    dir_count = 0

    def fmt_size(sz: int) -> str:
        if sz < 1024:
            return f"{sz}B"
        if sz < 1024**2:
            return f"{sz/1024:.1f}KB"
        if sz < 1024**3:
            return f"{sz/1024**2:.1f}MB"
        return f"{sz/1024**3:.1f}GB"

    def ftype(file: File) -> str | None:
        if isinstance(file, EmptyFile):
            return "empty file"
        if isinstance(file, NonTextFile):
            return "binary"
        return None

    def walk(d: Dir, path: str = ""):
        nonlocal total_size, total_lines, file_count, dir_count
        current_path = f"{path}/{d.name}" if path else d.name
        dir_count += len(d.subdirs)
        for file in sorted(d.files, key=lambda f: f.name):
            size = getattr(file, "size", 0)
            total_size += size
            file_count += 1
            line = f"{current_path}/{file.name} ["

            meta = [f"size {fmt_size(size)}"]
            type_str = ftype(file)
            if type_str:
                meta.append(type_str)
            if isinstance(file, (TextFile, TooLargeTextFile)):
                total_lines += file.lines
                meta.append(f"{file.lines} lines")
            line += ", ".join(meta) + "]"

            lines.append(line)

        for sub in sorted(d.subdirs, key=lambda s: s.name):
            walk(sub, current_path)

    walk(ir)

    if len(lines) > 2:
        lines.append(f"== {file_count} files, {dir_count} dirs, total {fmt_size(total_size)}, {total_lines} lines")
    return "\n".join(lines)


def _form_text_file_str_contexts(d: Dir, path: str = "") -> list[str]:
    res = []
    current_path = f"{path}/{d.name}" if path else d.name

    for f in sorted(d.files, key=lambda f: f.name):
        if isinstance(f, TextFile):
            res.append(f"## {current_path}/{f.name}\n\n```\n{f.content}\n```")

    for sub in sorted(d.subdirs, key=lambda s: s.name):
        res.extend(_form_text_file_str_contexts(sub, current_path))

    return res


def form_str_context(ir: Dir) -> str:
    res = _form_str_summary(ir)
    file_contexts = _form_text_file_str_contexts(ir)
    res += "\n\n" + "\n\n".join(file_contexts)
    return res
