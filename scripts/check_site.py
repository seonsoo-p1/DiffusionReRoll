#!/usr/bin/env python3
"""Small dependency-free structural check for the static project page."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.local_refs: list[str] = []
        self.fragments: list[str] = []
        self.images_without_alt: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.append(element_id)

        if tag == "img" and values.get("alt") is None:
            self.images_without_alt.append(values.get("src", "<unknown>"))

        for attribute in ("src", "href"):
            value = values.get(attribute)
            if not value:
                continue
            if value.startswith("#"):
                self.fragments.append(value[1:])
                continue
            parsed = urlparse(value)
            if not parsed.scheme and not parsed.netloc:
                self.local_refs.append(parsed.path)


def main() -> None:
    parser = SiteParser()
    parser.feed(INDEX.read_text(encoding="utf-8"))

    failures: list[str] = []
    duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
    missing_fragments = sorted(set(parser.fragments) - set(parser.ids))
    missing_files = sorted(
        {
            ref
            for ref in parser.local_refs
            if ref and not (ROOT / ref).resolve().is_file()
        }
    )

    if duplicates:
        failures.append(f"duplicate IDs: {', '.join(duplicates)}")
    if missing_fragments:
        failures.append(f"missing fragment targets: {', '.join(missing_fragments)}")
    if missing_files:
        failures.append(f"missing local files: {', '.join(missing_files)}")
    if parser.images_without_alt:
        failures.append(f"images without alt text: {', '.join(parser.images_without_alt)}")

    if failures:
        raise SystemExit("Site check failed\n- " + "\n- ".join(failures))

    print(
        "Site check passed: "
        f"{len(parser.ids)} IDs, {len(parser.fragments)} internal links, "
        f"{len(set(parser.local_refs))} local assets."
    )


if __name__ == "__main__":
    main()
