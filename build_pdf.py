#!/usr/bin/env python3
"""Convert the horse racing training plan markdown to a styled PDF.

Strategy:
1. Render Markdown -> HTML with a print-friendly stylesheet.
2. Try WeasyPrint (best CSS fidelity). If unavailable, fall back to
   LibreOffice headless conversion of the HTML.
"""
import subprocess
import sys
import os

SRC = "/home/user/Claude/horse_racing_training_plan.md"
HTML = "/home/user/Claude/horse_racing_training_plan.html"
PDF = "/home/user/Claude/horse_racing_training_plan.pdf"

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
body { font-family: 'DejaVu Sans', 'Liberation Sans', Arial, sans-serif;
       font-size: 10.5pt; line-height: 1.5; color: #1a1a1a; }
h1 { font-size: 22pt; color: #6b1f2a; border-bottom: 3px solid #6b1f2a;
     padding-bottom: 6px; margin-top: 18px; page-break-after: avoid; }
h2 { font-size: 15pt; color: #6b1f2a; border-bottom: 1px solid #c9a227;
     padding-bottom: 3px; margin-top: 20px; page-break-after: avoid; }
h3 { font-size: 12.5pt; color: #333; margin-top: 14px; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 10px 0;
        font-size: 9pt; page-break-inside: avoid; }
th { background: #6b1f2a; color: #fff; text-align: left; padding: 6px 8px;
     border: 1px solid #6b1f2a; }
td { border: 1px solid #ccc; padding: 5px 8px; vertical-align: top; }
tr:nth-child(even) td { background: #f7f3ef; }
code { background: #f0eee9; padding: 1px 4px; border-radius: 3px;
       font-family: 'DejaVu Sans Mono', monospace; font-size: 9pt; }
pre { background: #f0eee9; padding: 10px; border-radius: 5px; overflow-x: auto;
      font-size: 8.5pt; page-break-inside: avoid; border-left: 3px solid #c9a227; }
blockquote { border-left: 4px solid #c9a227; background: #fbf8f2;
             margin: 10px 0; padding: 8px 14px; color: #444; }
a { color: #6b1f2a; text-decoration: none; }
ul, ol { margin: 6px 0 6px 0; }
li { margin: 2px 0; }
hr { border: none; border-top: 1px solid #ddd; margin: 16px 0; }
"""


def render_html():
    import markdown
    with open(SRC, encoding="utf-8") as f:
        text = f.read()
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "toc", "sane_lists", "nl2br"],
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML rendered ->", HTML, flush=True)


def try_weasyprint():
    try:
        from weasyprint import HTML as WHTML
    except Exception as e:
        print("WeasyPrint unavailable:", e, flush=True)
        return False
    try:
        WHTML(filename=HTML).write_pdf(PDF)
        print("PDF built with WeasyPrint ->", PDF, flush=True)
        return True
    except Exception as e:
        print("WeasyPrint render failed:", e, flush=True)
        return False


def try_libreoffice():
    try:
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir",
             os.path.dirname(PDF), HTML],
            check=True, timeout=300,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if os.path.exists(PDF):
            print("PDF built with LibreOffice ->", PDF, flush=True)
            return True
        print("LibreOffice ran but PDF not found", flush=True)
        return False
    except Exception as e:
        print("LibreOffice failed:", e, flush=True)
        return False


if __name__ == "__main__":
    render_html()
    if try_weasyprint():
        sys.exit(0)
    print("Falling back to LibreOffice...", flush=True)
    if try_libreoffice():
        sys.exit(0)
    print("ALL CONVERSION METHODS FAILED", flush=True)
    sys.exit(1)
