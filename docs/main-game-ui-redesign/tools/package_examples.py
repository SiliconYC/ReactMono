"""Package a renderer export for offline archival; Python standard library only.

Usage: python3 tools/package_examples.py
The original editable fragment stays unchanged in source/.
"""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'examples/interactive.html'


class FrameParser(HTMLParser):
    frame = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'iframe' and attrs.get('id') == 'codex-visualization':
            self.frame = attrs.get('data-srcdoc')


def package():
    document = TARGET.read_text(encoding='utf-8')
    parser = FrameParser()
    parser.feed(document)
    if parser.frame is None:
        raise SystemExit('Expected renderer export containing a data-srcdoc iframe')
    # This mockup uses neither tooltips nor icons. The renderer adds three CDN
    # helpers; remove their script elements, keeping its inline styles/runtime.
    frame, removed = re.subn(r'<script\b[^>]*\bsrc=[^>]*>\s*</script>', '',
                             parser.frame, flags=re.I)
    # No other content is interpolated into this replacement string.
    encoded = escape(frame, quote=True)
    document, replaced = re.subn(r'data-srcdoc="[^"]*"',
                                 lambda _: 'data-srcdoc="' + encoded + '"',
                                 document, count=1)
    assert replaced == 1
    TARGET.write_text(document, encoding='utf-8')
    assert not re.search(r'<script\b[^>]*\bsrc=', frame, re.I)
    print(f'Offline export ready: {TARGET.name}; removed {removed} external helpers')


if __name__ == '__main__':
    package()
