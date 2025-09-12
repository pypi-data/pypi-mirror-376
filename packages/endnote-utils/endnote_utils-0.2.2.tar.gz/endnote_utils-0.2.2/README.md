# EndNote Utils

Convert **EndNote XML** and **RIS files** into clean **CSV / JSON / XLSX** with automatic **TXT reports**.  
Supports both **Python API** and **command-line interface (CLI)**.

---

## Features

- ✅ Parse one file (`--xml` or `--ris`) or an entire folder of mixed `*.xml` / `*.ris`
- ✅ Streams records with `iterparse` (XML) and line-based parsing (RIS) → low memory usage
- ✅ Extracts fields:  
  `database, ref_type, title, journal, authors, year, volume, number, abstract, doi, urls, keywords, publisher, isbn, language, extracted_date`
- ✅ Adds a `database` column from the filename stem (`IEEE.xml → IEEE`, `PubMed.ris → PubMed`)
- ✅ Normalizes DOI (`10.xxxx` → `https://doi.org/...`)
- ✅ Always generates a **TXT report** (default: `<out>_report.txt`) with:
  - per-file counts (exported/skipped records)  
  - totals, run timestamp & duration  
  - **duplicates table by database** (Origin / Retractions / Duplicates / Remaining)  
  - optional **summary stats** (by year, ref_type, journal, authors)
- ✅ Deduplication by `doi` or `title+year` (`--dedupe`)
- ✅ Export formats: **CSV, JSON, XLSX**
- ✅ Auto-creates output folders if missing
- ✅ Importable Python API for scripting & integration

---

## Installation

### From PyPI

```bash
pip install endnote-utils
```

Optional (for Excel export):

```bash
pip install "openpyxl>=3.1.0"
```

Requires **Python 3.8+**.

---

## Usage

### Command Line

#### Single XML file

```bash
endnote-utils --xml data/IEEE.xml --out output/ieee.csv
```

#### Single RIS file

```bash
endnote-utils --ris data/PubMed.ris --out output/pubmed.json
```

#### Folder with mixed files

```bash
endnote-utils --folder data/refs --out output/all.xlsx
```

→ Each produces both the chosen output (`csv/json/xlsx`) and a TXT report (`<out>_report.txt`).

---

### CLI Options

| Option          | Description                                           | Default            |
| --------------- | ----------------------------------------------------- | ------------------ |
| `--xml`         | Path to a single EndNote XML file                     | –                  |
| `--ris`         | Path to a single RIS file                             | –                  |
| `--folder`      | Path to a folder containing `*.xml` / `*.ris` files   | –                  |
| `--out`         | Output file path; format inferred from extension      | –                  |
| `--format`      | Explicit format (`csv`, `json`, `xlsx`)               | inferred           |
| `--report`      | Output TXT report path                                | `<out>_report.txt` |
| `--no-report`   | Disable TXT report                                    | –                  |
| `--delimiter`   | CSV delimiter                                         | `,`                |
| `--quoting`     | CSV quoting: `minimal`, `all`, `nonnumeric`, `none`   | `minimal`          |
| `--no-header`   | Suppress CSV header row                               | –                  |
| `--encoding`    | Output encoding                                       | `utf-8`            |
| `--ref-type`    | Filter: only include records with this ref\_type      | –                  |
| `--year`        | Filter: only include records with this year           | –                  |
| `--max-records` | Stop after N records per file (for testing)           | –                  |
| `--dedupe`      | Deduplicate (`none`, `doi`, `title-year`)             | `none`             |
| `--dedupe-keep` | For duplicates, keep `first` or `last`                | `first`            |
| `--stats`       | Add summary stats (year, ref\_type, journal, authors) | –                  |
| `--stats-json`  | Save stats + duplicates as JSON file                  | –                  |
| `--verbose`     | Verbose logging with debug details                    | –                  |

---

### Example Report (snippet)

```
========================================
EndNote Export Report
========================================
Run started : 2025-09-12 12:42:20
Files       : 4
Duration    : 0.47 seconds

Per-file results
----------------------------------------
GGScholar.xml  : 13 exported, 0 skipped
IEEE.xml       : 2147 exported, 0 skipped
PubMed.ris     : 504 exported, 0 skipped
Scopus.ris     : 847 exported, 0 skipped
TOTAL exported : 3511

Duplicates table (by database)
----------------------------------------
Database       Origin  Retractions  Duplicates  Remaining
---------------------------------------------------------
IEEE             2200            0         53        2147
PubMed            520            2         14         504
Scopus            880            0         33         847
TOTAL            3600            2        100        3498

Duplicate keys (top)
----------------------------------------
Mode   : doi
Keep   : first
Removed: 100
Details (top):
  https://doi.org/10.1109/abc.123 : 5 duplicate(s)
  ...

Summary stats
----------------------------------------
By year:
  2022 : 569
  2023 : 684
  2024 : 1148
  2025 : 1108
By ref_type (top):
  Journal Article        : 2037
  Conference Proceedings : 1470
By journal (top 10):
  IEEE Access : 175
  ...
Top authors (top 10):
  Y. Wang : 50
  X. Wang : 35
  ...
```

---

## Python API

```python
from pathlib import Path
from endnote_utils import export, export_folder

# Single XML
total, out_file, report_file = export(
    Path("data/IEEE.xml"), Path("output/ieee.csv"),
    dedupe="doi", stats=True
)

# Folder (mixed XML + RIS)
total, out_file, report_file = export_folder(
    Path("data/refs"), Path("output/all.csv"),
    dedupe="title-year", stats=True, stats_json=Path("output/stats.json")
)

print(f"Exported {total} → {out_file}")
print(f"Report at {report_file}")
```

---

## Development Notes

* Pure Python, only stdlib (`argparse`, `csv`, `xml.etree.ElementTree`, `logging`, `pathlib`, `json`, `re`).
* Optional: `openpyxl` for Excel output.
* Streaming parsers for XML and RIS avoid high memory usage.
* Robust error handling: skips malformed records but logs them in verbose mode.
* Follows [PEP 621](https://peps.python.org/pep-0621/) packaging (`pyproject.toml`).

---

## License

MIT License © 2025 Minh Quach