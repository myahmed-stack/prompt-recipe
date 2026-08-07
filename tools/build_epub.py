"""Build downloads/the-prompt-recipe.epub from the Markdown manuscript.

Pure Python (needs only the `markdown` package): the EPUB is assembled
directly as a zip archive. Run from anywhere; paths resolve relative to
the repo root.
"""
import html
import os
import re
import uuid
import zipfile
import xml.etree.ElementTree as ET

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'downloads', 'the-prompt-recipe.epub')

TITLE = 'The Prompt Recipe: A Practical Guide to Prompt Engineering and AI Interaction'
AUTHOR = 'Ahmed Bouchentouf'
PUBLISHER = 'Bread Books'
LANG = 'en'
MODIFIED = '2026-08-07T00:00:00Z'
REPO_URL = 'https://github.com/myahmed-stack/prompt-recipe'

BOOK_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, 'the-prompt-recipe/ahmed-bouchentouf/cc-edition'))

CHAPTERS = [
    '00-introduction',
    '01-inside-the-ais-mind',
    '02-the-first-ingredient-is-clarity',
    '03-the-art-of-the-recipe-card',
    '04-the-precision-of-the-grammage',
    '05-taste-adjust-repeat',
    '06-your-signature-recipes',
    '07-conclusion',
]

CSS = '''
body { font-family: serif; line-height: 1.5; margin: 0 5%; }
h1 { font-size: 1.5em; margin: 1.5em 0 1em; line-height: 1.3; }
h2 { font-size: 1.2em; margin: 1.4em 0 0.6em; line-height: 1.3; }
h3 { font-size: 1.05em; margin: 1.2em 0 0.5em; font-style: italic; }
p { margin: 0.4em 0 0.8em; text-align: justify; }
li { margin-bottom: 0.35em; }
blockquote { margin: 1em 1.5em; font-style: italic; }
table { border-collapse: collapse; font-size: 0.85em; margin: 1em 0; }
th, td { border: 1px solid #999; padding: 0.35em 0.5em; text-align: left; }
hr { border: none; text-align: center; margin: 1.5em 0; }
hr:after { content: "* * *"; }
.titlepage { text-align: center; margin-top: 20%; }
.titlepage h1 { font-size: 1.9em; border: none; }
.copyright { font-size: 0.85em; margin-top: 15%; }
.cover { text-align: center; margin: 0; }
.cover img { max-width: 100%; max-height: 100%; }
'''.strip()

XHTML = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="../css/style.css"/>
</head>
<body>
{body}
</body>
</html>
'''

def page(title, body):
    doc = XHTML.format(title=html.escape(title), body=body)
    ET.fromstring(doc)  # fail fast on invalid XHTML
    return doc

md = markdown.Markdown(extensions=['tables'], output_format='xhtml')

chapters = []
for slug in CHAPTERS:
    with open(os.path.join(ROOT, 'manuscript', slug + '.md'), encoding='utf-8') as f:
        text = f.read()
    m = re.match(r'# (.+)\n', text)
    title = m.group(1).strip()
    body = md.reset().convert(text)
    chapters.append((slug, title, page(title, body)))

titlepage = page(TITLE, f'''
<div class="titlepage">
  <h1>The Prompt Recipe</h1>
  <p><i>A Practical Guide to Prompt Engineering and AI Interaction</i></p>
  <p><b>{html.escape(AUTHOR)}</b></p>
  <p>{html.escape(PUBLISHER)}</p>
</div>''')

repo_line = f'<p>Source and latest version: <a href="{REPO_URL}">{REPO_URL}</a></p>' if REPO_URL else \
    '<p>Source and latest version: see the project repository on GitHub.</p>'
copyright_page = page('Copyright', f'''
<div class="copyright">
  <p><b>{html.escape(TITLE)}</b></p>
  <p>Copyright &#169; 2025 {html.escape(AUTHOR)}. Originally published on Amazon in April 2025.</p>
  <p>Open edition, 2026. This book &#8212; text and cover &#8212; is licensed under the
     Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License
     (CC BY-NC-SA 4.0).</p>
  <p>You are free to copy, share, and adapt it for non-commercial purposes, provided you
     credit the author and distribute any derivative work under the same license.</p>
  <p>Full license: <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">creativecommons.org/licenses/by-nc-sa/4.0</a></p>
  {repo_line}
</div>''')

nav_lis = '\n'.join(
    f'      <li><a href="text/{slug}.xhtml">{html.escape(title)}</a></li>'
    for slug, title, _ in chapters)
nav = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><title>Table of Contents</title></head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Table of Contents</h1>
    <ol>
{nav_lis}
    </ol>
  </nav>
</body>
</html>
'''
ET.fromstring(nav)

manifest_items = '\n'.join(
    f'    <item id="{slug}" href="text/{slug}.xhtml" media-type="application/xhtml+xml"/>'
    for slug, _, _ in chapters)
spine_items = '\n'.join(f'    <itemref idref="{slug}"/>' for slug, _, _ in chapters)
opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="en">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:{BOOK_ID}</dc:identifier>
    <dc:title>{html.escape(TITLE)}</dc:title>
    <dc:creator>{html.escape(AUTHOR)}</dc:creator>
    <dc:publisher>{html.escape(PUBLISHER)}</dc:publisher>
    <dc:language>{LANG}</dc:language>
    <dc:date>2025-04-05</dc:date>
    <dc:rights>&#169; 2025 {html.escape(AUTHOR)}. Licensed under CC BY-NC-SA 4.0.</dc:rights>
    <meta property="dcterms:modified">{MODIFIED}</meta>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="css" href="css/style.css" media-type="text/css"/>
    <item id="coverpage" href="text/coverpage.xhtml" media-type="application/xhtml+xml"/>
    <item id="titlepage" href="text/titlepage.xhtml" media-type="application/xhtml+xml"/>
    <item id="copyright" href="text/copyright.xhtml" media-type="application/xhtml+xml"/>
{manifest_items}
  </manifest>
  <spine>
    <itemref idref="coverpage"/>
    <itemref idref="titlepage"/>
    <itemref idref="copyright"/>
{spine_items}
  </spine>
</package>
'''
ET.fromstring(opf)

coverpage = page('Cover', '<div class="cover"><img src="../images/cover.jpg" alt="Book cover"/></div>')

container = '''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
'''

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, 'w') as z:
    z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip', zipfile.ZIP_STORED)
    z.writestr('META-INF/container.xml', container, zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/package.opf', opf, zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/nav.xhtml', nav, zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/css/style.css', CSS, zipfile.ZIP_DEFLATED)
    z.write(os.path.join(ROOT, 'assets', 'cover.jpg'), 'OEBPS/images/cover.jpg', zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/text/coverpage.xhtml', coverpage, zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/text/titlepage.xhtml', titlepage, zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/text/copyright.xhtml', copyright_page, zipfile.ZIP_DEFLATED)
    for slug, _, doc in chapters:
        z.writestr(f'OEBPS/text/{slug}.xhtml', doc, zipfile.ZIP_DEFLATED)

print('built', OUT, f'({os.path.getsize(OUT):,} bytes)')
