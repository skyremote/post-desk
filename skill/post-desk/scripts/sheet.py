"""Download and read the posting plan sheet (a Google Sheet shared as "anyone with the link can view").

The sheet is the one source for the captions, the dates, the accounts and the house rules. See references/SHEET.md.
Standard library only: the sheet is downloaded as .xlsx and read with zipfile.
"""
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def export_url(url):
    """Any Google Sheets link becomes its .xlsx download link. Other links are used as they are."""
    m = re.search(r"docs\.google\.com/spreadsheets/d/([\w-]+)", url or "")
    return "https://docs.google.com/spreadsheets/d/%s/export?format=xlsx" % m.group(1) if m else url


def download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    try:
        with urllib.request.urlopen(url, timeout=30) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
    except Exception as first_error:
        # Some Mac Python installs have no SSL certificates. curl ships with macOS and Windows 10+.
        curl = shutil.which("curl.exe") or shutil.which("curl")
        if not curl:
            raise first_error
        subprocess.run([curl, "-sSL", "-o", tmp, url], check=True, timeout=60)
    with open(tmp, "rb") as f:
        if f.read(2) != b"PK":
            os.remove(tmp)
            raise RuntimeError("The download is not a spreadsheet. Is the sheet still shared with 'anyone with the link'?")
    os.replace(tmp, dest)


def read_xlsx(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall(NS + "si"):
            shared.append("".join(t.text or "" for t in si.iter(NS + "t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels}
    sheets = {}
    for s in wb.find(NS + "sheets"):
        t = target[s.get(RNS + "id")].lstrip("/")
        p = t if t.startswith("xl/") else "xl/" + t
        rows = []
        for row in ET.fromstring(z.read(p)).iter(NS + "row"):
            cells = {}
            for c in row.findall(NS + "c"):
                ref = re.match(r"([A-Z]+)", c.get("r")).group(1)
                col = 0
                for ch in ref:
                    col = col * 26 + (ord(ch) - 64)
                v = c.find(NS + "v")
                kind = c.get("t")
                if kind == "s" and v is not None:
                    val = shared[int(v.text)]
                elif kind == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter(NS + "t"))
                elif kind == "b" and v is not None:
                    val = v.text == "1"
                elif v is not None:
                    val = v.text
                else:
                    val = ""
                cells[col - 1] = val
            if cells:
                rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
        sheets[s.get("name")] = rows
    return sheets


def to_date(v):
    if isinstance(v, (int, float)) or (isinstance(v, str) and re.fullmatch(r"\d+(\.\d+)?", v.strip())):
        return date(1899, 12, 30) + timedelta(days=int(float(v)))
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%a %d %b %Y", "%d %b %Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def text(v):
    """Cell text with Windows line endings normalised."""
    return str(v if v is not None else "").replace("\r\n", "\n").replace("\r", "\n")


def table(rows, must_have):
    """Rows under the first header row that holds every name in must_have, as dicts."""
    for i, r in enumerate(rows):
        head = [text(c).strip() for c in r]
        if all(m in head for m in must_have):
            out = []
            for r2 in rows[i + 1:]:
                if not any(text(c).strip() for c in r2):
                    continue
                out.append({head[j]: (r2[j] if j < len(r2) else "") for j in range(len(head)) if head[j]})
            return out
    return []


def load(settings, offline=False, file=None):
    """Return (sheets, note). Downloads unless offline or a local file is given, and falls back to the last copy."""
    if file:
        return read_xlsx(common.expand(file)), "read from %s" % file
    note = ""
    if not offline:
        if not settings.get("sheet_url"):
            sys.exit("No posting plan link in the settings. Run: setup.py init --sheet \"<link>\"")
        try:
            download(export_url(settings["sheet_url"]), common.PLAN_CACHE)
            note = "posting plan downloaded just now"
        except Exception as e:  # keep going with the last copy
            note = "could not download the posting plan (%s), using the last copy" % e
    if not os.path.exists(common.PLAN_CACHE):
        sys.exit("No posting plan available. Check the sheet link in the settings and the internet connection.")
    if not note:
        note = "using the last downloaded copy"
    note += " (saved %s)" % datetime.fromtimestamp(os.path.getmtime(common.PLAN_CACHE)).strftime("%d %b %Y %H:%M")
    return read_xlsx(common.PLAN_CACHE), note


def tab(sheets, name):
    for k, v in sheets.items():
        if k.strip().lower() == name.lower():
            return v
    return []


def plan_settings(sheets):
    """The Settings tab as a dict: two columns, Key and Value."""
    out = {}
    for r in table(tab(sheets, "Settings"), ["Key", "Value"]):
        out[text(r["Key"]).strip()] = text(r["Value"]).strip()
    return out


def plan_accounts(sheets):
    return table(tab(sheets, "Accounts"), ["Account key", "Platform"])


def plan_rules(sheets):
    """House rules as (level, compiled pattern, message). Level is BLOCK or WARN."""
    rules = []
    for r in table(tab(sheets, "Rules"), ["Level", "Pattern", "Message"]):
        level = text(r["Level"]).strip().upper()
        pat = text(r["Pattern"]).strip()
        if level not in ("BLOCK", "WARN") or not pat:
            continue
        try:
            rules.append((level, re.compile(pat, re.I), text(r["Message"]).strip()))
        except re.error as e:
            print("Rule skipped, the pattern does not read (%s): %s" % (e, pat), file=sys.stderr)
    return rules
