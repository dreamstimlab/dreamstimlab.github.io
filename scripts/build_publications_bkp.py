from pathlib import Path
import html
import re

import bibtexparser


ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "my_publications.bib"
OUT = ROOT / "publications.html"

TARGET_FAMILY = "Adelhöfer"

GROUPS = [
    ("Senior authorships (shared)", "last"),
    ("First authorships (incl. shared)", "first"),
    ("Co-authorships (selection)", "co_keep"),
]


def latex_to_text(s):
    """Tiny LaTeX cleanup for common BibTeX artifacts."""
    if not s:
        return ""

    replacements = {
        r"\\&": "&",
        r"\&": "&",
        r"---": "—",
        r"--": "–",
        r"{\"a}": "ä",
        r"{\"o}": "ö",
        r"{\"u}": "ü",
        r"{\"A}": "Ä",
        r"{\"O}": "Ö",
        r"{\"U}": "Ü",
        r"{\ss}": "ß",
        r"\"a": "ä",
        r"\"o": "ö",
        r"\"u": "ü",
        r"\"A": "Ä",
        r"\"O": "Ö",
        r"\"U": "Ü",
        r"\ss": "ß",
    }

    for old, new in replacements.items():
        s = s.replace(old, new)

    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def esc(s):
    return html.escape(latex_to_text(s), quote=False)


def has_keyword(entry, keyword):
    kws = entry.get("keywords", "")
    return keyword in [k.strip() for k in kws.split(",")]


def split_authors(raw):
    raw = latex_to_text(raw)
    return [a.strip() for a in raw.split(" and ") if a.strip()]


def parse_name(raw_name):
    name = latex_to_text(raw_name)

    if "," in name:
        family, given = [x.strip() for x in name.split(",", 1)]
    else:
        parts = name.split()
        if not parts:
            return "", ""
        family = parts[-1]
        given = " ".join(parts[:-1])

    return family, given


def given_to_initials(given):
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:-[A-Za-zÀ-ÖØ-öø-ÿ]+)*", given)

    initials = []
    for word in words:
        pieces = [p for p in word.split("-") if p]
        initials.append("-".join(f"{p[0]}." for p in pieces))

    return " ".join(initials)


def format_one_author(raw_name):
    family, given = parse_name(raw_name)
    initials = given_to_initials(given)

    if initials:
        txt = f"{family}, {initials}"
    else:
        txt = family

    txt = esc(txt)

    if family == TARGET_FAMILY:
        return f'<span class="me">{txt}</span>'

    return txt


def format_authors_cv_style(raw_authors):
    """
    Mirrors the LaTeX logic:
    - find target author
    - if target is 4th or later: first author, ..., target
    - if more than 2 authors follow target: ..., last author
    - otherwise print the tail
    """
    authors = split_authors(raw_authors)
    if not authors:
        return ""

    families = [parse_name(a)[0] for a in authors]
    formatted = [format_one_author(a) for a in authors]

    try:
        me = families.index(TARGET_FAMILY)  # zero-based index
    except ValueError:
        return ", ".join(formatted)

    total = len(authors)
    visible = []

    if me > 2:
        visible.extend([formatted[0], "…", formatted[me]])
    else:
        visible.extend(formatted[:me + 1])

    authors_after_me = total - (me + 1)

    if authors_after_me > 2:
        visible.extend(["…", formatted[-1]])
    else:
        visible.extend(formatted[me + 1:])

    # avoid accidental duplicates around short lists
    deduped = []
    for item in visible:
        if not deduped or deduped[-1] != item:
            deduped.append(item)

    return ", ".join(deduped)


def format_journal(entry):
    journal = (
        entry.get("journaltitle")
        or entry.get("journal")
        or entry.get("booktitle")
        or entry.get("publisher")
        or ""
    )

    journal = esc(journal)

    if not journal:
        return ""

    return f'<span class="journal">{journal}</span>'


def sort_key(entry):
    year = entry.get("year") or entry.get("date") or ""
    try:
        year_num = int(str(year)[:4])
    except ValueError:
        year_num = 0

    return year_num


def render_entry(entry, shown_year):
    year = latex_to_text(entry.get("year") or entry.get("date") or "")
    year = year[:4]

    year_html = esc(year) if year != shown_year else "&nbsp;"

    title_html = esc(entry.get("title", ""))
    authors_html = format_authors_cv_style(entry.get("author", ""))
    journal_html = format_journal(entry)

    details_html = ", ".join(x for x in [authors_html, journal_html] if x)

    row = f"""      <div class="pub-row">
        <div class="pub-year">{year_html}</div>
        <div class="pub-text">
          <div class="pub-title">{title_html}</div>
          <div class="pub-details">{details_html}</div>
        </div>
      </div>
"""

    return row, year


def render_sections(entries):
    html_sections = []

    for label, keyword in GROUPS:
        group_entries = [e for e in entries if has_keyword(e, keyword)]
        group_entries.sort(key=sort_key, reverse=True)

        shown_year = None
        rows = []

        for entry in group_entries:
            row, shown_year = render_entry(entry, shown_year)
            rows.append(row)

        if not rows:
            continue

        html_sections.append(f"""    <section class="pub-section">
      <h2>{esc(label)}</h2>
{''.join(rows)}    </section>
""")

    return "\n".join(html_sections)


def main():
    with open(BIB, encoding="utf-8") as f:
        bib = bibtexparser.load(f)

    sections_html = render_sections(bib.entries)

    OUT.write_text(f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>publications · dreamstimlab</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>

<main class="page">
{sections_html}
</main>

<script src="scripts/header.js"></script>

<footer>
  <a href="https://www.youtube.com/@dreamstimlab">youtube</a> ·
  <a href="https://github.com/dreamstimlab">github</a> ·
  <a href="https://linkedin.com/in/nico-adelhoefer">linkedin</a> ·
  <a href="./imprint.html">imprint</a>
</footer>

</body>
</html>
""", encoding="utf-8")


if __name__ == "__main__":
    main()