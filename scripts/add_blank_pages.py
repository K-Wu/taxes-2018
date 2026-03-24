import os
import re
import sys
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from typing import List, Tuple, Dict, Any


def parse_outline(reader: PdfReader, items: list, depth: int = 0) -> List[Tuple[str, int, int]]:
    """Flatten PDF outline into (title, page_number, depth) tuples."""
    result = []
    for item in items:
        if isinstance(item, list):
            result.extend(parse_outline(reader, item, depth + 1))
        else:
            try:
                title = item.title if hasattr(item, 'title') else item.get('/Title', '')
                page_num = reader.get_destination_page_number(item)
                result.append((title, page_num, depth))
            except Exception:
                pass
    return result


def extract_form_key(title: str) -> str:
    """Extract base form/schedule name for grouping related pages and copies."""
    m = re.match(r'^(.*?):', title)
    if m:
        return m.group(1).strip()
    m = re.match(r'^(.*?)\s*\(Page', title)
    if m:
        return m.group(1).strip()
    return title.strip()


def compute_blank_insertions(
    bookmarks: List[Tuple[str, int, int]],
    total_pages: int
) -> set:
    """
    Group consecutive bookmarks by form key.
    Return set of original page numbers after which a blank should be inserted.
    """
    groups = []
    prev_key = None
    for title, page, depth in bookmarks:
        key = extract_form_key(title)
        if key != prev_key:
            groups.append((key, page))
            prev_key = key
    insertions = set()
    for i, (key, start) in enumerate(groups):
        end = groups[i + 1][1] - 1 if i + 1 < len(groups) else total_pages - 1
        page_count = end - start + 1
        if page_count > 0 and page_count % 2 == 1:
            insertions.add(end)
            print(f"  Adding blank after: {key} (p{start+1}-p{end+1}, {page_count} pages)")
    return insertions


def make_blank_page(width: float, height: float) -> PdfReader:
    """Create an in-memory blank PDF page with the given dimensions."""
    buf = BytesIO()
    w = PdfWriter()
    w.add_blank_page(width=width, height=height)
    w.write(buf)
    buf.seek(0)
    return PdfReader(buf)


def add_blank_pages(input_path: str, output_path: str) -> None:
    reader = PdfReader(input_path)
    first = reader.pages[0]
    blank_reader = make_blank_page(
        float(first.mediabox.width), float(first.mediabox.height)
    )
    blank_page = blank_reader.pages[0]
    total_pages = len(reader.pages)
    print(f"Input PDF has {total_pages} pages")
    outline = reader.outline if reader.outline else []
    bookmarks = parse_outline(reader, outline)
    print(f"Found {len(bookmarks)} bookmarks\n")
    insertions = compute_blank_insertions(bookmarks, total_pages)
    page_map: Dict[int, int] = {}
    new_idx = 0
    for orig in range(total_pages):
        page_map[orig] = new_idx
        new_idx += 1
        if orig in insertions:
            new_idx += 1
    writer = PdfWriter()
    for orig in range(total_pages):
        writer.add_page(reader.pages[orig])
        if orig in insertions:
            writer.add_page(blank_page)
    parent_refs: Dict[int, Any] = {}
    for title, orig_page, depth in bookmarks:
        new_page = page_map.get(orig_page, orig_page)
        parent = parent_refs.get(depth - 1) if depth > 0 else None
        ref = writer.add_outline_item(title, new_page, parent=parent)
        parent_refs[depth] = ref
    with open(output_path, 'wb') as f:
        writer.write(f)
    blanks_added = len(insertions)
    print(f"\nWrote {total_pages + blanks_added} pages ({blanks_added} blank pages inserted)")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.pdf> <output.pdf>")
        sys.exit(1)
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    add_blank_pages(input_pdf, output_pdf)
    print(f"Output saved to:\n{output_pdf}")


if __name__ == "__main__":
    main()
