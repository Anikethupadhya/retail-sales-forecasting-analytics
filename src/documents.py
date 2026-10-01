"""Replace explicitly owned Markdown sections while preserving maintained prose."""
from pathlib import Path


def update_section(path: Path, key: str, body: str, *, title: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    start, end = f"<!-- generated:{key}:start -->", f"<!-- generated:{key}:end -->"
    text = path.read_text(encoding="utf-8") if path.exists() else (f"# {title}\n" if title else "")
    if text.count(start) != text.count(end) or text.count(start) > 1:
        raise ValueError(f"Malformed generated-section boundaries: {path.name}:{key}")
    owned = f"{start}\n{body.strip()}\n{end}"
    if start in text:
        a, b = text.index(start), text.index(end)
        if b < a:
            raise ValueError(f"Reversed generated-section boundaries: {key}")
        text = text[:a] + owned + text[b + len(end):]
    else:
        text = text.rstrip() + "\n\n" + owned + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
