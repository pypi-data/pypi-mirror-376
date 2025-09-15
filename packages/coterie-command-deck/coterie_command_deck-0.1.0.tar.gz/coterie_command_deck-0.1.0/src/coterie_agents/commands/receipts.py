import json
import re
from pathlib import Path
from typing import Any

from ._cli import has_unknown_flags, print_help, wants_help

try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # type: ignore
try:
    import pytesseract
except ImportError:
    pytesseract = None  # type: ignore
try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None  # type: ignore

OUTPUT_FILE = Path("receipts_parsed.json")


COMMAND = "receipts"
DESCRIPTION = "Automated PDF receipt ingestion and parsing."
USAGE = f"{COMMAND} <folder> [--help]"


def run(arg: list[str] | dict | None = None) -> int | dict:
    """
    Dual API/CLI entrypoint:
    - If arg is a dict, treat as API call and route to appropriate logic
    - If arg is a list (CLI argv), run CLI logic and return int
    """
    if isinstance(arg, dict):
        # API mode: implement API logic here as needed
        # Example: return parsed receipts for a folder
        folder = arg.get("folder")
        if not folder:
            return {"error": "No folder specified"}
        parsed = []
        for pdf_path in Path(folder).glob("*.pdf"):
            text = _extract_text(pdf_path)
            data = _parse_receipt_text(text)
            parsed.append(data)
        return {"receipts": parsed}

    argv: list[str] = arg if isinstance(arg, list) else []
    known_flags = {"--help", "-h"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if not argv:
        print("[❌] No folder provided.")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    folder = argv[0]
    parsed = []
    for pdf_path in Path(folder).glob("*.pdf"):
        text = _extract_text(pdf_path)
        data = _parse_receipt_text(text)
        parsed.append(data)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(parsed, f, indent=2)
    print(f"[✔] Imported {len(parsed)} receipts to {OUTPUT_FILE}")
    return 0


def _extract_text(pdf_path: Path) -> str:
    # Text extraction
    with pdfplumber.open(pdf_path) as pdf:
        text = "".join(page.extract_text() or "" for page in pdf.pages)
    # Fallback to OCR if extraction fails
    if not text.strip():
        images = convert_from_path(str(pdf_path), dpi=300)
        text = "".join(pytesseract.image_to_string(img) for img in images)
    return text


def _parse_receipt_text(text: str) -> dict[str, Any]:
    # Core fields: vendor, date, items, total
    return {
        "vendor": _extract_vendor(text),
        "date": _extract_date(text),
        "items": _extract_items(text),
        "total": _extract_total(text),
    }


def _extract_vendor(text: str) -> str:
    """Grab the first non-empty line as vendor."""
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return "Unknown"


def _extract_date(text: str) -> str:
    """Find the first date in YYYY-MM-DD or MM/DD/YYYY format."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if not m:
        m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text)
    return m.group(1) if m else ""


def _extract_items(text: str) -> list[dict[str, Any]]:
    """
    Extract lines matching 'ItemName    $Price'.
    Returns list of {"name":..., "price":...} dicts.
    """
    items = []
    for line in text.splitlines():
        match = re.match(r"^(.+?)\s+\$?(\d+\.\d{2})$", line.strip())
        if match and not re.search(r"Total|Subtotal", line, re.IGNORECASE):
            name, price = match.groups()
            items.append({"name": name.strip(), "price": float(price)})
    return items


def _extract_total(text: str) -> float:
    """Find the total or amount due."""
    m = re.search(r"(?:Total|Amount Due)[: ]+\$?(\d+\.\d{2})", text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return 0.0
