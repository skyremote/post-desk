"""Shared helpers for the Post Desk scripts.

Standard library only, so it runs the same on Mac and Windows with Python 3.8 or later.
"""
import io
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME_DIR = os.environ.get("POST_DESK_HOME") or os.path.join(os.path.expanduser("~"), ".post-desk")
SETTINGS_PATH = os.path.join(HOME_DIR, "settings.json")
PLAN_CACHE = os.path.join(HOME_DIR, "plan.xlsx")

# Everything here can be replaced by the Settings tab of the posting plan sheet.
DEFAULTS = {
    "sheet_url": "",
    "brand": "",
    "timezone": "Australia/Sydney",
    "posting_time": "07:00",
    "link": "",
    "web_address": "",
    "wrong_web_addresses": [],
    "handover_folder": "",
    "handover_markers": [],
    "posts_folder": "~/Documents/Social Posts",
    "no_emojis": False,
    "linkedin_hashtags": True,
    "accounts": {},
}


def utf8_stdout():
    """Windows consoles default to a code page that cannot print the sheet's dots and quotes."""
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, io.UnsupportedOperation):
            pass


def load_settings(path=None, required=True):
    path = path or SETTINGS_PATH
    if not os.path.exists(path):
        if required:
            sys.exit("No settings yet at %s. Run the set-up first: setup.py init --sheet \"<link to the posting plan sheet>\"" % path)
        return json.loads(json.dumps(DEFAULTS))
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for k, v in DEFAULTS.items():
        data.setdefault(k, json.loads(json.dumps(v)))
    return data


def save_settings(data, path=None):
    path = path or SETTINGS_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def expand(p):
    if not p:
        return p
    return os.path.normpath(os.path.expandvars(os.path.expanduser(p)))


def missing(s):
    """What still has to be done before anything can be scheduled from this computer."""
    gaps = []
    folder = expand(s.get("handover_folder"))
    if not folder:
        gaps.append("handover_folder is empty. Run: setup.py find-folder --save")
    elif not os.path.isdir(folder):
        gaps.append("handover_folder does not exist on this computer: %s" % folder)
    else:
        for m in s.get("handover_markers") or []:
            if not os.path.isdir(os.path.join(folder, m)):
                gaps.append("handover_folder has no '%s' inside: %s" % (m, folder))
    for key, acc in s.get("accounts", {}).items():
        if not acc.get("on"):
            continue
        if not acc.get("accountId"):
            gaps.append("%s is switched on but has no Blotato accountId" % key)
        if acc.get("needs_page") and not acc.get("pageId"):
            gaps.append("%s needs a pageId (it posts to a page, not to a personal profile)" % key)
    return gaps


def truthy(v):
    return v is True or str(v).strip().lower() in ("true", "yes", "y", "1", "on")


# ---------- time zones ----------

def _first_sunday(year, month):
    d = date(year, month, 1)
    return d + timedelta(days=(6 - d.weekday()) % 7)


def _aus_east_offset(local_naive):
    """Fallback for Sydney and Melbourne when Windows has no time zone data.

    Daylight time (UTC+11) runs from 02:00 on the first Sunday in October to 03:00 on the
    first Sunday in April. Standard time is UTC+10.
    """
    y = local_naive.year
    start = datetime.combine(_first_sunday(y, 10), datetime.min.time()).replace(hour=2)
    end = datetime.combine(_first_sunday(y, 4), datetime.min.time()).replace(hour=3)
    in_dst = local_naive >= start or local_naive < end
    return timedelta(hours=11 if in_dst else 10)


def get_tz(name):
    try:
        from zoneinfo import ZoneInfo  # Python 3.9+

        return ZoneInfo(name)
    except Exception:
        if name in ("Australia/Sydney", "Australia/Melbourne", "Australia/Canberra", "Australia/Hobart"):
            return None  # use the fallback rule
        sys.exit("No time zone data for %s on this computer. Run: python -m pip install tzdata" % name)


def local_to_utc(local_naive, tz_name):
    tz = get_tz(tz_name)
    if tz is None:
        return (local_naive - _aus_east_offset(local_naive)).replace(tzinfo=timezone.utc)
    return local_naive.replace(tzinfo=tz).astimezone(timezone.utc)


def now_local(tz_name):
    utc_now = datetime.now(timezone.utc)
    tz = get_tz(tz_name)
    if tz is None:
        guess = utc_now.replace(tzinfo=None) + timedelta(hours=10)
        return utc_now.replace(tzinfo=None) + _aus_east_offset(guess)
    return utc_now.astimezone(tz).replace(tzinfo=None)


def utc_iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def day_name(d):
    return "%s %d %s %d" % (d.strftime("%a"), d.day, d.strftime("%b"), d.year)
