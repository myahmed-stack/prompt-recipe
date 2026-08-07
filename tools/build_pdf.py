"""Build downloads/the-prompt-recipe.pdf from the Markdown manuscript.

Renders a single HTML document and prints it to PDF with headless Chrome
(pre-installed on GitHub's ubuntu runners and on most desktops) — no LaTeX
needed. Needs the `markdown` package.
"""
import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'downloads', 'the-prompt-recipe.pdf')

AUTHOR = 'Ahmed Bouchentouf'
REPO_URL = 'https://github.com/myahmed-stack/prompt-recipe'

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

def find_chrome():
    for env in ('CHROME_PATH',):
        if os.environ.get(env) and os.path.exists(os.environ[env]):
            return os.environ[env]
    candidates = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    for name in ('google-chrome', 'chromium-browser', 'chromium', 'chrome'):
        p = shutil.which(name)
        if p:
            return p
    sys.exit('Chrome/Chromium not found — set CHROME_PATH')

md = markdown.Markdown(extensions=['tables'], output_format='html5')

sections = []
toc_items = []
for slug in CHAPTERS:
    with open(os.path.join(ROOT, 'manuscript', slug + '.md'), encoding='utf-8') as f:
        text = f.read()
    title = re.match(r'# (.+)\n', text).group(1).strip()
    toc_items.append(f'<li><a href="#{slug}">{title}</a></li>')
    body = md.reset().convert(text)
    sections.append(f'<section class="chapter" id="{slug}">\n{body}\n</section>')

with open(os.path.join(ROOT, 'assets', 'cover.jpg'), 'rb') as f:
    cover_b64 = base64.b64encode(f.read()).decode()

repo_line = f'<p>Source and latest version: {REPO_URL}</p>' if REPO_URL else \
    '<p>Source and latest version: see the project repository on GitHub.</p>'

html_doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>The Prompt Recipe</title>
<style>
@page {{ size: 152mm 229mm; margin: 19mm 17mm; }}
html {{ font-size: 10.5pt; }}
body {{ font-family: Georgia, 'Times New Roman', serif; line-height: 1.55; margin: 0; color: #1a1a1a; }}
p {{ margin: 0 0 0.7em; text-align: justify; orphans: 2; widows: 2; }}
h1 {{ font-size: 1.7em; line-height: 1.25; margin: 2.5em 0 1.2em; }}
h2 {{ font-size: 1.25em; line-height: 1.3; margin: 1.5em 0 0.6em; page-break-after: avoid; }}
h3 {{ font-size: 1.05em; font-style: italic; margin: 1.2em 0 0.5em; page-break-after: avoid; }}
li {{ margin-bottom: 0.3em; }}
ul, ol {{ padding-left: 1.4em; }}
blockquote {{ margin: 1em 1.5em; font-style: italic; }}
table {{ border-collapse: collapse; font-size: 0.8em; margin: 1em 0; width: 100%; page-break-inside: avoid; }}
th, td {{ border: 0.5pt solid #888; padding: 0.35em 0.5em; text-align: left; vertical-align: top; }}
hr {{ border: none; margin: 1.5em 0; text-align: center; }}
hr::after {{ content: "* * *"; color: #666; }}
.chapter {{ page-break-before: always; }}
.cover-page {{ page-break-after: always; text-align: center; }}
.cover-page img {{ width: 100%; }}
.title-page {{ page-break-after: always; text-align: center; padding-top: 30%; }}
.title-page h1 {{ font-size: 2.1em; margin: 0 0 0.3em; }}
.copyright-page {{ page-break-after: always; font-size: 0.85em; padding-top: 55%; }}
.copyright-page p {{ text-align: left; }}
.toc-page {{ page-break-after: always; }}
.toc-page ul {{ list-style: none; padding: 0; line-height: 2; }}
.toc-page a {{ text-decoration: none; color: inherit; }}
</style>
</head>
<body>
<div class="cover-page"><img src="data:image/jpeg;base64,{cover_b64}" alt="Cover"></div>
<div class="title-page">
  <h1>The Prompt Recipe</h1>
  <p><i>A Practical Guide to Prompt Engineering and AI Interaction</i></p>
  <p style="margin-top:2em"><b>{AUTHOR}</b></p>
  <p>Bread Books</p>
</div>
<div class="copyright-page">
  <p><b>The Prompt Recipe: A Practical Guide to Prompt Engineering and AI Interaction</b></p>
  <p>Copyright &copy; 2025 {AUTHOR}. Originally published on Amazon in April 2025.</p>
  <p>Open edition, 2026. This book &mdash; text and cover &mdash; is licensed under the Creative Commons
     Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
     You are free to copy, share, and adapt it for non-commercial purposes, provided you credit
     the author and distribute any derivative work under the same license.</p>
  <p>Full license: creativecommons.org/licenses/by-nc-sa/4.0</p>
  {repo_line}
</div>
<div class="toc-page"><h1>Contents</h1><ul>
{chr(10).join(toc_items)}
</ul></div>
{chr(10).join(sections)}
</body>
</html>
'''

tmp = tempfile.mkdtemp(prefix='tpr-pdf-')
src = os.path.join(tmp, 'book.html')
dst = os.path.join(tmp, 'book.pdf')
with open(src, 'w', encoding='utf-8') as f:
    f.write(html_doc)

chrome = find_chrome()
subprocess.run([
    chrome, '--headless=new', '--disable-gpu', '--no-sandbox',
    '--no-pdf-header-footer', f'--print-to-pdf={dst}',
    'file:///' + src.replace('\\', '/'),
], check=True, cwd=tmp, timeout=300)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
shutil.move(dst, OUT)
shutil.rmtree(tmp, ignore_errors=True)
print('built', OUT, f'({os.path.getsize(OUT):,} bytes)')
