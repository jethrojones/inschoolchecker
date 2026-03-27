from app.services.discovery import discover_sources


def test_discovery_ranks_calendar_pdf_above_generic_links():
    html = """
    <html>
      <head><title>Example Public Schools</title></head>
      <body>
        <a href="/about">About</a>
        <a href="/files/calendar-2025-2026.pdf">2025-2026 District Calendar</a>
        <a href="/news/weather-alert">Inclement Weather Alert</a>
      </body>
    </html>
    """
    candidates, cms_type, title = discover_sources("https://www.examplek12.org/", html)
    assert title == "Example Public Schools"
    assert cms_type is None
    assert candidates[0].url.endswith("calendar-2025-2026.pdf")
    assert candidates[0].source_type == "pdf_calendar"

