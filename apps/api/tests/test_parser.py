from unittest.mock import MagicMock, patch

from app.services.parser import parse_html_document, parse_pdf_document


def test_html_parser_extracts_school_year_and_dates():
    html = """
    <html>
      <head><title>Calendar</title></head>
      <body>
        <h1>2025-2026 District Calendar</h1>
        <p>Spring Break March 27-28, 2026</p>
      </body>
    </html>
    """
    parsed = parse_html_document(html)
    assert parsed.title == "Calendar"
    assert parsed.school_year_text == "2025-2026"
    assert parsed.events[0].label_raw == "Spring Break"


def test_pdf_parser_extracts_text_using_reader():
    page = MagicMock()
    page.extract_text.return_value = "No School March 27, 2026"
    reader = MagicMock()
    reader.pages = [page]
    with patch("app.services.parser.PdfReader", return_value=reader):
        parsed = parse_pdf_document(b"%PDF-1.4")
    assert parsed.parse_method == "pdf_text"
    assert parsed.events[0].label_raw == "No School"


def test_html_parser_strips_docaccess_boilerplate():
    html = """
    <html>
      <body>
        <p>This document has been archived per Title II of the Americans with Disabilities Act (28 CFR § 35.200).</p>
        <p>DocAccess Logo</p>
        <p>Your Documents — Transcribed, Searchable, Translated & Assisted — Instantly Accessible</p>
        <p>Spring Break March 27-28, 2026</p>
      </body>
    </html>
    """
    parsed = parse_html_document(html)
    assert "DocAccess Logo" not in parsed.extracted_text
    assert "Title II of the Americans with Disabilities Act" not in parsed.extracted_text
    assert parsed.events[0].label_raw == "Spring Break"
