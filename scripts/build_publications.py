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
    ≤ 5 authors → show everyone.
    > 5 authors → show at least 5 names, using ellipses where needed.
    Prefers: first authors + me + last author(s).
    """
    authors = split_authors(raw_authors)
    if not authors:
        return ""

    families = [parse_name(a)[0] for a in authors]
    formatted = [format_one_author(a) for a in authors]
    total = len(authors)

    # short list → show all
    if total <= 5:
        return ", ".join(formatted)

    try:
        me = families.index(TARGET_FAMILY)
    except ValueError:
        # target not found → just show first 4 + last
        return ", ".join(formatted[:4] + ["…", formatted[-1]])

    visible = []

    # how many names we still need to reach at least 5
    # we always keep: some front + me + some back
    if me <= 2:
        # me is near the front → take first (me+1) names, then fill from the end
        visible.extend(formatted[: me + 1])
        remaining = 5 - len(visible)
        if remaining > 0:
            # take from the end, but avoid overlap
            tail = formatted[max(me + 1, total - remaining) :]
            if len(tail) < remaining:
                visible.append("…")
            visible.extend(tail)
        else:
            if me + 1 < total:
                visible.append("…")
                visible.append(formatted[-1])
    else:
        # me is further back → first 2, …, me, then fill to reach 5
        visible.extend([formatted[0], formatted[1], "…", formatted[me]])
        remaining = 5 - 3   # we already have 3 items (2 names + me)
        if remaining > 0 and me < total - 1:
            tail_start = max(me + 1, total - remaining)
            tail = formatted[tail_start :]
            if tail_start > me + 1:
                visible.append("…")
            visible.extend(tail)
        elif me < total - 1:
            visible.append("…")
            visible.append(formatted[-1])

    # final clean-up of consecutive ellipses / duplicates
    cleaned = []
    for item in visible:
        if not cleaned or cleaned[-1] != item:
            cleaned.append(item)

    return ", ".join(cleaned)


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

    # authors on one line, journal on its own line
    details_parts = []
    if authors_html:
        details_parts.append(f'<div class="pub-authors">{authors_html}</div>')
    if journal_html:
        details_parts.append(f'<div class="pub-journal">{journal_html}</div>')

    details_html = "\n          ".join(details_parts)

    row = f"""      <div class="pub-row">
        <div class="pub-year">{year_html}</div>
        <div class="pub-text">
          <div class="pub-title">{title_html}</div>
          {details_html}
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

<main class="page publications-page">
{sections_html}
</main>

<script src="scripts/header.js"></script>

<script src="scripts/footer.js"></script>

</body>
</html>
""", encoding="utf-8")


if __name__ == "__main__":
    main()