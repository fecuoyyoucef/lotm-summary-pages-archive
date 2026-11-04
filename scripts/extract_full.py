#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'metadata' / 'index.json'
HEADERS = {'User-Agent': 'lotm-summary-pages-extractor/1.0 (private research archive)'}


def slug(item):
    return f"{item['start']:04d}-{item['end']:04d}"


def fetch_one(item):
    r = requests.get(item['url'], headers=HEADERS, timeout=60)
    r.raise_for_status()
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.select_one('main') or soup
    # Keep the complete article/main content while removing site chrome and executable content.
    for node in main.select('script, style, nav, footer, form, .sidebar, .comments, [aria-hidden="true"]'):
        node.decompose()
    article_html = str(main)
    md = markdownify(article_html, heading_style='ATX', bullets='-').strip() + '\n'
    md = re.sub(r'\n{3,}', '\n\n', md)
    digest = hashlib.sha256(html.encode('utf-8')).hexdigest()
    return {
        'item': item,
        'html': html,
        'article_html': article_html,
        'markdown': md,
        'sha256': digest,
        'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'http_status': r.status_code,
        'bytes': len(r.content),
    }


def build_docx(results):
    from docx import Document
    from docx.shared import Pt
    doc = Document()
    doc.core_properties.title = 'Lord of the Mysteries — Complete Chapter Summary Pages'
    doc.core_properties.subject = 'Full extracted content from 15 Novel Wiki chapter-summary pages'
    doc.add_heading('Lord of the Mysteries — Complete Chapter Summary Pages', 0)
    doc.add_paragraph('Source archive compiled from the 15 pages listed in the Novel Wiki chapter-summary index.')
    for result in results:
        item = result['item']
        doc.add_page_break()
        doc.add_heading(item['title'], 1)
        p = doc.add_paragraph()
        p.add_run('Source: ').bold = True
        p.add_run(item['url'])
        doc.add_paragraph(f"Chapter range: {item['start']}–{item['end']}")
        for line in result['markdown'].splitlines():
            line = line.strip()
            if not line or line.startswith('Source:') or line.startswith('Chapter range:'):
                continue
            if line.startswith('### '):
                doc.add_heading(line[4:], 3)
            elif line.startswith('## '):
                doc.add_heading(line[3:], 2)
            elif line.startswith('# '):
                doc.add_heading(line[2:], 2)
            elif line.startswith('- '):
                doc.add_paragraph(line[2:], style='List Bullet')
            else:
                doc.add_paragraph(line)
    out = ROOT / 'docs' / 'lord-of-the-mysteries-15-summary-pages.docx'
    doc.save(out)
    return out


def main():
    started = datetime.now(timezone.utc).isoformat()
    items = json.loads(INDEX.read_text(encoding='utf-8'))['items']
    results = []
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_one, item): item for item in items}
        for fut in concurrent.futures.as_completed(futures):
            item = futures[fut]
            try:
                results.append(fut.result())
            except Exception as exc:
                errors.append({'url': item['url'], 'error': repr(exc)})
    results.sort(key=lambda x: x['item']['start'])
    for result in results:
        name = slug(result['item'])
        (ROOT / 'raw' / f'{name}.html').write_text(result['html'], encoding='utf-8')
        page = f"# {result['item']['title']}\n\n- Source: {result['item']['url']}\n- Chapter range: {result['item']['start']}–{result['item']['end']}\n- Retrieved: {result['retrieved_at']}\n- SHA-256: `{result['sha256']}`\n\n{result['markdown']}"
        (ROOT / 'pages' / f'{name}.md').write_text(page, encoding='utf-8')
        meta = {k: result[k] for k in ['item', 'sha256', 'retrieved_at', 'http_status', 'bytes']}
        (ROOT / 'metadata' / f'{name}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    docx_path = build_docx(results) if not errors else None
    log = {
        'started_at': started,
        'finished_at': datetime.now(timezone.utc).isoformat(),
        'status': 'success' if not errors and len(results) == 15 else 'partial',
        'requested_pages': 15,
        'extracted_pages': len(results),
        'errors': errors,
        'docx': str(docx_path.relative_to(ROOT)) if docx_path else None,
        'source_index': 'https://www.novelwiki.net/lord-of-the-mysteries/summaries',
    }
    (ROOT / 'logs' / 'latest.json').write_text(json.dumps(log, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'logs' / ('run-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')).write_text(json.dumps(log, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(log, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
