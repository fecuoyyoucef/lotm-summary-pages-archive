from pathlib import Path
import json, re
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content'
CONTENT.mkdir(exist_ok=True)

items = json.loads((ROOT / 'metadata' / 'index.json').read_text(encoding='utf-8'))['items']
all_parts = []
doc = Document()
doc.core_properties.title = 'Lord of the Mysteries — Content Only: 15 Chapter Summary Pages'
doc.add_heading('Lord of the Mysteries — 15 Chapter Summary Pages', 0)
doc.add_paragraph('Standalone extracted content. No external links are required to read the summaries in this folder or document.')

for item in sorted(items, key=lambda x: x['start']):
    name = f"{item['start']:04d}-{item['end']:04d}"
    source = ROOT / 'pages' / f'{name}.md'
    text = source.read_text(encoding='utf-8')
    # Remove the archive metadata header and retain only the extracted page content.
    body = text.split('\n# Ch. ', 1)[1] if '\n# Ch. ' in text else text
    body = '# Ch. ' + body
    body = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', body)
    body = re.sub(r'^- (Source|Retrieved|SHA-256):.*\n', '', body, flags=re.M)
    (CONTENT / f'{name}.md').write_text(body.strip() + '\n', encoding='utf-8')
    (CONTENT / f'{name}.txt').write_text(re.sub(r'[`*_#]', '', body).strip() + '\n', encoding='utf-8')
    all_parts.append(body.strip())
    doc.add_page_break()
    doc.add_heading(f"Chapters {item['start']}–{item['end']}", 1)
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('# '):
            doc.add_heading(line[2:], 2)
        elif line.startswith('- '):
            doc.add_paragraph(line[2:], style='List Bullet')
        else:
            doc.add_paragraph(line)

(CONTENT / 'all-15-pages.txt').write_text('\n\n' + '\n\n'.join(all_parts) + '\n', encoding='utf-8')
(CONTENT / 'all-15-pages.md').write_text('\n\n---\n\n'.join(all_parts) + '\n', encoding='utf-8')
doc.save(ROOT / 'docs' / 'lord-of-the-mysteries-15-summary-pages-content-only.docx')
print('created content-only files for', len(items), 'pages')
