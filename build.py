#!/usr/bin/env python3
"""
The Weitzman Archive — build.py
================================
Converts markdown paper entries into HTML pages and keeps
papers.json in sync.

Usage:
    python build.py                 # build all papers
    python build.py --file papers/weitzman-1974.md   # build one paper
    python build.py --json-only     # only update papers.json, no HTML

Requirements:
    pip install python-frontmatter markdown jinja2

Install once:
    pip install python-frontmatter markdown jinja2
"""

import os
import re
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

try:
    import frontmatter
    import markdown
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("Missing dependencies. Run: pip install python-frontmatter markdown jinja2")
    raise

# ── PATHS ──────────────────────────────────────────────────────
ROOT       = Path(__file__).parent
PAPERS_DIR = ROOT / "papers"
DATA_FILE  = ROOT / "data" / "papers.json"
TMPL_DIR   = ROOT / "templates"
OUT_DIR    = ROOT   # HTML files go to root

# Section config: slug → (display name, accent colour, og image)
SECTIONS = {
    "solow-room":       ("The Solow Room",        "#7A1603", "solow-room.jpg"),
    "pigou-lab":        ("The Pigou Lab",          "#0097B2", "pigou-lab.jpg"),
    "krutilla-gallery": ("The Krutilla Gallery",   "#FEBE10", "krutilla-gallery.jpg"),
    "long-equilibrium": ("The Long Equilibrium",   "#1B4332", "long-equilibrium.jpg"),
    "nordhaus-index":   ("The Nordhaus Index",     "#2E3F50", "nordhaus-index.jpg"),
    "gazette":          ("The Gazette",            "#440939", "gazette.jpg"),
}

# ── MARKDOWN PROCESSOR ─────────────────────────────────────────
md_processor = markdown.Markdown(
    extensions=[
        "markdown.extensions.extra",      # tables, fenced code, etc.
        "markdown.extensions.smarty",     # smart quotes, em dashes
        "markdown.extensions.nl2br",      # newlines → <br> in prose
    ]
)

# ── LATEX / KATEX HANDLING ─────────────────────────────────────
def protect_math(text):
    """
    Pull math out of the text before markdown processes it,
    so markdown doesn't corrupt LaTeX syntax.
    Returns (protected_text, math_store) where math_store maps
    placeholder tokens back to the original math strings.
    """
    store = {}
    counter = [0]

    def _store(m, display):
        key = f"MATHTOKEN{counter[0]}ENDTOKEN"
        counter[0] += 1
        latex = m.group(1)
        if display:
            store[key] = f'<div class="katex-display">{latex}</div>'
        else:
            store[key] = f'\\({latex}\\)'
        return key

    # Display math: $$...$$ and \[...\]
    text = re.sub(r'\$\$(.*?)\$\$',
                  lambda m: _store(m, display=True),
                  text, flags=re.DOTALL)
    text = re.sub(r'\\\[(.*?)\\\]',
                  lambda m: _store(m, display=True),
                  text, flags=re.DOTALL)
    # Inline math: $...$ and \(...\)
    text = re.sub(r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)',
                  lambda m: _store(m, display=False),
                  text)
    text = re.sub(r'\\\((.*?)\\\)',
                  lambda m: _store(m, display=False),
                  text)
    return text, store


def restore_math(html, store):
    """Replace placeholder tokens with the original math HTML."""
    for key, value in store.items():
        html = html.replace(key, value)
    return html


def md_to_html(text):
    """Convert a markdown string to HTML, preserving LaTeX."""
    protected, store = protect_math(text)
    md_processor.reset()
    html = md_processor.convert(protected)
    return restore_math(html, store)


# ── SECTION EXTRACTION ─────────────────────────────────────────
def extract_sections(body_text):
    """
    Split the markdown body into the four named sections:
    In Plain English, Short Summary, Marshall Notes, References.
    Returns a dict of section_name → raw markdown string.
    """
    sections = {
        "plain_english":  "",
        "short_summary":  "",
        "marshall_notes": {},
        "references":     "",
    }

    # Split on H2 headings
    parts = re.split(r'^## (.+)$', body_text, flags=re.MULTILINE)
    # parts = [pre, heading1, content1, heading2, content2, ...]

    i = 1
    while i < len(parts) - 1:
        heading = parts[i].strip()
        content = parts[i + 1].strip()
        i += 2

        if "In Plain English" in heading:
            sections["plain_english"] = content
        elif "Short Summary" in heading:
            sections["short_summary"] = content
        elif "Marshall Notes" in heading:
            # Extract H3 sub-sections within Marshall Notes
            sub_parts = re.split(r'^### (.+)$', content, flags=re.MULTILINE)
            j = 1
            while j < len(sub_parts) - 1:
                sub_heading = sub_parts[j].strip()
                sub_content = sub_parts[j + 1].strip()
                j += 2
                key = sub_heading.lower().replace(" ", "_").replace("the_", "")
                sections["marshall_notes"][key] = sub_content
        elif "References" in heading:
            sections["references"] = content

    return sections


# ── LOAD AND VALIDATE FRONTMATTER ──────────────────────────────
REQUIRED_FIELDS = [
    "slug", "title", "authors", "year", "journal",
    "section", "jel", "topics", "entry_author", "entry_date"
]

def load_paper(md_path):
    """Load a markdown paper file, validate, and return (meta, sections)."""
    post = frontmatter.load(str(md_path))
    meta = dict(post.metadata)
    body = post.content

    # Validate required fields
    missing = [f for f in REQUIRED_FIELDS if f not in meta]
    if missing:
        raise ValueError(f"{md_path.name}: missing required fields: {missing}")

    # Defaults for optional fields
    meta.setdefault("doi", "")
    meta.setdefault("volume", "")
    meta.setdefault("issue", "")
    meta.setdefault("pages", "")
    meta.setdefault("subtitle", "")
    meta.setdefault("datasets", [])
    meta.setdefault("repos", [])
    meta.setdefault("related", [])
    meta.setdefault("entry_affil", "")
    meta.setdefault("image", "")

    sections = extract_sections(body)
    return meta, sections


# ── UPDATE papers.json ──────────────────────────────────────────
JSON_FIELDS = [
    "slug", "title", "authors", "year", "journal",
    "volume", "issue", "pages", "doi", "section",
    "jel", "topics", "datasets", "repos", "related",
    "entry_author", "entry_affil", "entry_date", "image"
]

def update_json(meta):
    """Add or update this paper's metadata in papers.json."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
    else:
        db = {"papers": []}

    papers = db.get("papers", [])
    slug = meta["slug"]

    # Extract only the JSON fields
    entry = {k: meta[k] for k in JSON_FIELDS if k in meta}

    # Find existing entry by slug
    existing = next((i for i, p in enumerate(papers) if p.get("slug") == slug), None)
    if existing is not None:
        papers[existing] = entry
        print(f"  ↻  Updated {slug} in papers.json")
    else:
        papers.append(entry)
        print(f"  +  Added {slug} to papers.json")

    db["papers"] = papers
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


# ── BUILD HTML ──────────────────────────────────────────────────
def build_html(meta, sections):
    """
    Render the article HTML page and write it to the root folder.
    Uses an inline template (no external template file required).
    """
    slug    = meta["slug"]
    section = meta["section"]
    sec_name, accent, sec_og = SECTIONS.get(section, ("", "#333", "og-default.jpg"))

    # Resolve display image
    # Paper-specific image takes priority; always falls back to section placeholder
    paper_img = f"assets/images/papers/{meta['image']}" if meta["image"] else f"assets/images/papers/{slug}.jpg"
    og_image  = paper_img if meta["image"] else f"assets/images/sections/{sec_og}"
    hero_img  = (
        f'<img src="{paper_img}"\n'
        f'         onerror="this.src=\'assets/images/sections/{sec_og}\'"\n'
        f'         alt="{meta["title"]}">'
    )

    # Convert sections to HTML
    plain_html   = md_to_html(sections["plain_english"])
    summary_html = md_to_html(sections["short_summary"])
    refs_html    = md_to_html(sections["references"])

    # Marshall Notes steps
    mn = sections["marshall_notes"]
    mn_steps_html = ""
    step_order = [
        ("research_question",   "Research Question"),
        ("measurement_problem", "The Measurement Problem"),
        ("workaround",          "The Workaround"),
        ("defence",             "The Defence"),
        ("vulnerability",       "The Vulnerability"),
        ("reach",               "The Reach"),
    ]
    for i, (key, label) in enumerate(step_order, 1):
        content = mn.get(key, "")
        if content:
            content_html = md_to_html(content)
            mn_steps_html += f"""
              <div class="mn-step">
                <div class="mn-step-head">
                  <span class="mn-step-n">{i}</span>
                  <span class="mn-step-label">{label}</span>
                </div>
                <div class="mn-step-body">{content_html}</div>
              </div>"""

    # Authors string
    authors_str = " &amp; ".join(a["name"] for a in meta["authors"])

    # DOI link
    doi_html = ""
    if meta["doi"]:
        doi_url = f"https://doi.org/{meta['doi']}"
        doi_html = f'<a href="{doi_url}" class="sidebar-doi-link" target="_blank" rel="noopener">doi:{meta["doi"]} ↗</a>'

    # JEL tags
    jel_tags = " ".join(
        f'<a href="jel-{j.lower()}.html" class="tag-jel">{j}</a>'
        for j in meta["jel"]
    )

    # Topic tags
    topic_tags = " ".join(
        f'<a href="topic-{t}.html" class="tag-topic">{t.replace("-", " ")}</a>'
        for t in meta["topics"]
    )

    # Dataset links
    dataset_links = ""
    for ds in meta.get("datasets", []):
        dataset_links += f'<a href="{ds["url"]}" class="resource-link" target="_blank" rel="noopener">↗ {ds["name"]}</a>'

    # Repo links
    repo_links = ""
    for r in meta.get("repos", []):
        repo_links += f'<a href="{r["url"]}" class="resource-link" target="_blank" rel="noopener">↗ {r["name"]}</a>'

    # Citation strings
    volume_issue = ""
    if meta.get("volume"):
        volume_issue = meta["volume"]
        if meta.get("issue"):
            volume_issue += f'({meta["issue"]})'
    pages_str  = f', {meta["pages"]}' if meta.get("pages") else ""
    doi_str    = f'. doi:{meta["doi"]}' if meta.get("doi") else ""
    cite_paper = f'{authors_str} ({meta["year"]}). {meta["title"]}. {meta["journal"]}{", " + volume_issue if volume_issue else ""}{pages_str}{doi_str}'
    cite_entry = f'{meta["entry_author"]} ({meta["entry_date"][:4]}). {meta["title"]} — Marshall Notes Entry. The Weitzman Archive. weitzmanarchive.com/{slug}'

    # Entry date display
    try:
        dt = datetime.strptime(meta["entry_date"], "%Y-%m")
        entry_date_display = dt.strftime("%B %Y")
    except Exception:
        entry_date_display = meta["entry_date"]

    # Author avatar
    avatar_img_path = f"assets/images/authors/{meta['entry_author'].lower().replace(' ', '-')}.jpg"
    if (ROOT / avatar_img_path).exists():
        avatar_html = f'<img src="{avatar_img_path}" alt="{meta["entry_author"]}">'
    else:
        avatar_html = '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.2" aria-hidden="true">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>'''

    subtitle_html = f'<p class="article-subtitle">{meta["subtitle"]}</p>' if meta.get("subtitle") else ""

    resource_section = ""
    if dataset_links or repo_links:
        resource_section = f'<div class="resource-links">{dataset_links}{repo_links}</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{meta['title']} — {authors_str} {meta['year']} | The Weitzman Archive</title>
  <meta name="description" content="{meta.get('subtitle', meta['title'])} — {meta['journal']}, {meta['year']}.">
  <link rel="canonical" href="https://weitzmanarchive.com/{slug}.html">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "ScholarlyArticle",
    "headline": "{meta['title']}",
    "author": {{ "@type": "Person", "name": "{meta['authors'][0]['name']}" }},
    "datePublished": "{meta['year']}",
    "isPartOf": {{ "@type": "Periodical", "name": "{meta['journal']}" }}{',\n    "identifier": {{ "@type": "PropertyValue", "propertyID": "DOI", "value": "' + meta['doi'] + '" }}' if meta.get('doi') else ''}
  }}
  </script>
  <meta property="og:type"        content="article">
  <meta property="og:title"       content="{meta['title']} — {authors_str} {meta['year']}">
  <meta property="og:description" content="{meta.get('subtitle', meta['title'])}">
  <meta property="og:url"         content="https://weitzmanarchive.com/{slug}.html">
  <meta property="og:image"       content="https://weitzmanarchive.com/{og_image}">
  <meta name="twitter:card"       content="summary_large_image">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📜</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;0,700;0,800;1,400;1,600&family=Castoro:ital@0;1&family=Rubik:wght@300;400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
  <link rel="stylesheet" href="css/main.css">
  <link rel="stylesheet" href="css/article.css">
  <style>:root {{ --accent: {accent}; }}</style>
</head>
<body>
<nav class="site-nav" role="navigation" aria-label="Main navigation">
  <div class="nav-inner">
    <a href="index.html" class="site-wordmark">The Weitzman Archive</a>
    <div class="nav-right">
      <div class="nav-item">
        <button class="nav-btn" aria-expanded="false" aria-haspopup="true">
          Sections <svg class="chevron" viewBox="0 0 10 6" aria-hidden="true"><path d="M1 1l4 4 4-4" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <div class="nav-dropdown" role="menu">
          <div class="nav-dropdown-section">
            <span class="nav-dropdown-label">Named Sections</span>
            <a href="solow-room.html" role="menuitem"><span class="nav-dot" style="background:#7A1603"></span>The Solow Room — Theory</a>
            <a href="pigou-lab.html" role="menuitem"><span class="nav-dot" style="background:#0097B2"></span>The Pigou Lab — Empirics</a>
            <a href="krutilla-gallery.html" role="menuitem"><span class="nav-dot" style="background:#FEBE10"></span>The Krutilla Gallery — Transdisciplinary</a>
            <a href="long-equilibrium.html" role="menuitem"><span class="nav-dot" style="background:#1B4332"></span>The Long Equilibrium — Game Theory</a>
            <a href="nordhaus-index.html" role="menuitem"><span class="nav-dot" style="background:#2E3F50"></span>The Nordhaus Index — Data &amp; Repos</a>
          </div>
          <div class="nav-dropdown-section">
            <a href="gazette.html" role="menuitem"><span class="nav-dot" style="background:#440939"></span>The Gazette</a>
            <a href="ciriacy-wantrup.html" role="menuitem"><span class="nav-dot" style="background:#888"></span>Ciriacy-Wantrup — Timeline</a>
            <a href="marshall-notes.html" role="menuitem"><span class="nav-dot" style="background:#888"></span>Marshall Notes</a>
          </div>
        </div>
      </div>
      <div class="nav-sep" aria-hidden="true"></div>
      <a href="papers.html"  class="nav-link">Search</a>
      <a href="about.html"   class="nav-link">About</a>
      <a href="contact.html" class="nav-link">Contact</a>
    </div>
  </div>
</nav>

<main class="page" id="main-content">
  <header class="article-masthead">
    <div class="article-kicker">
      <span class="article-section-badge">{sec_name}</span>
      <span class="article-kicker-journal">{meta['journal']}, {meta['year']}</span>
    </div>
    <h1 class="article-title">{meta['title']}</h1>
    {subtitle_html}
    <div class="article-meta-bar">
      <div class="meta-cell">
        <span class="meta-cell-label">Paper Author</span>
        <span class="meta-cell-val">{authors_str}</span>
      </div>
      <div class="meta-cell">
        <span class="meta-cell-label">Journal</span>
        <span class="meta-cell-val">{meta['journal']}</span>
      </div>
      <div class="meta-cell">
        <span class="meta-cell-label">Year</span>
        <span class="meta-cell-val">{meta['year']}</span>
      </div>
      <div class="meta-cell">
        <span class="meta-cell-label">Entry Author</span>
        <span class="meta-cell-val">{meta['entry_author']}</span>
      </div>
      <div class="meta-cell">
        <span class="meta-cell-label">Entry Date</span>
        <span class="meta-cell-val muted">{entry_date_display}</span>
      </div>
    </div>
  </header>

  <div class="article-hero">
    {hero_img}
  </div>

  <div class="article-layout">
    <div class="article-main">

      <div class="accordion" role="region" aria-label="Article content">
        <div class="acc-item">
          <button class="acc-trigger" aria-expanded="true" aria-controls="layer-1">
            <span class="acc-trigger-label">In Plain English</span>
            <span class="acc-trigger-layer">Layer 1 of 3</span>
            <span class="acc-icon" aria-hidden="true"><svg viewBox="0 0 10 10"><line x1="5" y1="1" x2="5" y2="9" stroke-linecap="round"/><line x1="1" y1="5" x2="9" y2="5" stroke-linecap="round"/></svg></span>
          </button>
          <div class="acc-body open" id="layer-1">
            <div class="prose">{plain_html}</div>
          </div>
        </div>

        <div class="acc-item">
          <button class="acc-trigger" aria-expanded="false" aria-controls="layer-2">
            <span class="acc-trigger-label">Short Summary</span>
            <span class="acc-trigger-layer">Layer 2 of 3</span>
            <span class="acc-icon" aria-hidden="true"><svg viewBox="0 0 10 10"><line x1="5" y1="1" x2="5" y2="9" stroke-linecap="round"/><line x1="1" y1="5" x2="9" y2="5" stroke-linecap="round"/></svg></span>
          </button>
          <div class="acc-body" id="layer-2">
            <div class="prose">{summary_html}</div>
          </div>
        </div>

        <div class="acc-item">
          <button class="acc-trigger" aria-expanded="false" aria-controls="layer-3">
            <span class="acc-trigger-label">Marshall Notes</span>
            <span class="acc-trigger-layer">Layer 3 of 3</span>
            <span class="acc-icon" aria-hidden="true"><svg viewBox="0 0 10 10"><line x1="5" y1="1" x2="5" y2="9" stroke-linecap="round"/><line x1="1" y1="5" x2="9" y2="5" stroke-linecap="round"/></svg></span>
          </button>
          <div class="acc-body" id="layer-3">
            <div class="mn-steps">{mn_steps_html}</div>
          </div>
        </div>
      </div>

      <div class="tags-area">
        <div class="tags-row">
          <span class="tags-row-label">JEL</span>
          {jel_tags}
        </div>
        <div class="tags-row">
          <span class="tags-row-label">Topics</span>
          {topic_tags}
        </div>
      </div>

      {resource_section}

      <div class="article-refs">
        <h3 class="article-refs-head">References</h3>
        {refs_html}
      </div>

    </div>

    <aside class="article-sidebar" aria-label="Paper information">
      <div class="sidebar-block">
        <span class="sidebar-block-label">Entry Author</span>
        <div class="sidebar-author-card">
          <div class="sidebar-avatar">{avatar_html}</div>
          <div>
            <span class="sidebar-author-name">{meta['entry_author']}</span>
            <span class="sidebar-author-affil">{meta.get('entry_affil', '')}</span>
          </div>
        </div>
        <span class="sidebar-entry-date">Entry published {entry_date_display}</span>
      </div>

      <div class="sidebar-block">
        <span class="sidebar-block-label">Original Paper</span>
        <div class="sidebar-paper-title">{meta['title']}</div>
        <div class="sidebar-paper-row"><strong>Author</strong> &nbsp;{authors_str}</div>
        <div class="sidebar-paper-row"><strong>Journal</strong> &nbsp;{meta['journal']}</div>
        {f'<div class="sidebar-paper-row"><strong>Volume</strong> &nbsp;{volume_issue} &nbsp;·&nbsp; <strong>Pages</strong> &nbsp;{meta.get("pages","")}</div>' if volume_issue else ''}
        <div class="sidebar-paper-row"><strong>Year</strong> &nbsp;{meta['year']}</div>
        {doi_html}
      </div>

      <div class="sidebar-block">
        <span class="sidebar-block-label">Suggested Citations</span>
        <div class="sidebar-cite-box">
          <span class="sidebar-cite-label">Cite the Original Paper</span>
          <div class="sidebar-cite-text" id="cite-paper">{cite_paper}</div>
          <button class="sidebar-cite-copy copy-btn" data-copy-target="#cite-paper">Copy citation</button>
        </div>
        <div class="sidebar-cite-box">
          <span class="sidebar-cite-label">Cite this Archive Entry</span>
          <div class="sidebar-cite-text" id="cite-entry">{cite_entry}</div>
          <button class="sidebar-cite-copy copy-btn" data-copy-target="#cite-entry">Copy citation</button>
        </div>
      </div>
    </aside>
  </div>
</main>

<footer class="site-footer">
  <div class="footer-inner">
    <span class="footer-wordmark">The Weitzman Archive</span>
    <div class="footer-links">
      <a href="about.html">About</a>
      <a href="contact.html">Contact</a>
      <a href="marshall-notes.html">Marshall Notes</a>
      <a href="ciriacy-wantrup.html">Timeline</a>
    </div>
    <span class="footer-copy">&copy; {datetime.now().year} The Weitzman Archive</span>
  </div>
</footer>

<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"></script>
<script src="js/main.js"></script>
<script>
document.addEventListener('DOMContentLoaded', () => {{
  if (typeof renderMathInElement !== 'undefined') {{
    renderMathInElement(document.body, {{
      delimiters: [
        {{ left: '$$',  right: '$$',  display: true  }},
        {{ left: '\\\\[', right: '\\\\]', display: true  }},
        {{ left: '$',   right: '$',   display: false }},
        {{ left: '\\\\(', right: '\\\\)', display: false }}
      ],
      throwOnError: false
    }});
  }}
}});
</script>
</body>
</html>"""

    out_path = OUT_DIR / f"{slug}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"  ✓  Built {out_path.name}")


# ── MAIN ───────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Build Weitzman Archive paper pages")
    parser.add_argument("--file",      help="Build a single markdown file")
    parser.add_argument("--json-only", action="store_true", help="Only update papers.json")
    args = parser.parse_args()

    if args.file:
        md_files = [Path(args.file)]
    else:
        md_files = sorted(PAPERS_DIR.glob("*.md"))

    if not md_files:
        print("No markdown files found in papers/")
        return

    print(f"\nThe Weitzman Archive — build.py")
    print(f"{'─' * 40}")

    for md_path in md_files:
        print(f"\nProcessing: {md_path.name}")
        try:
            meta, sections = load_paper(md_path)
            update_json(meta)
            if not args.json_only:
                build_html(meta, sections)
        except Exception as e:
            print(f"  ✗  Error: {e}")
            continue

    print(f"\n{'─' * 40}")
    print(f"Done. {len(md_files)} file(s) processed.\n")


if __name__ == "__main__":
    main()
