# Lord of the Mysteries — Full 15-Page Chapter Summary Archive

This repository contains a full local archive of the 15 chapter-summary pages listed in the [Novel Wiki summary index](https://www.novelwiki.net/lord-of-the-mysteries/summaries).

## Contents

- `raw/`: complete fetched HTML snapshots for all 15 pages.
- `pages/`: cleaned Markdown copies of the complete main content of each page.
- `metadata/`: source URL, chapter range, retrieval timestamp, byte count, and SHA-256 checksum for each page.
- `docs/lord-of-the-mysteries-15-summary-pages.docx`: compiled DOCX reading copy.
- `scripts/extract_full.py`: rerunnable extractor using four concurrent workers.
- `logs/`: persistent extraction history, including `latest.json`.

## Rebuild

```bash
python3 scripts/extract_full.py
```

The archive preserves source attribution and canonical URLs. It is intended for private research and extraction workflows; consult Novel Wiki's terms and copyright policies before redistributing the content.
