"""Read the posting plan sheet and turn its rows into post files, ready to check and schedule.

  plan.py next                       the next post that is due and not yet logged
  plan.py day --date tomorrow        one day (today, tomorrow, or YYYY-MM-DD)
  plan.py week [--date 2026-11-23]   Monday to Sunday of this week, or of the week holding that date
  plan.py all                        the whole plan
  plan.py status                     every dated post against the posting log on this computer
  plan.py when --date 2026-11-16 [--time 07:00]    the posting time in local time and in UTC

next, day and week also write each post file (post_v1.json and post_v1.md) into the posts folder, unless one is
already there. Add --no-write to look only, --json for machine-readable output, --offline to use the last download.
Every date in the plan is a proposal. A person agrees the date and time before anything is scheduled.
"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import sheet  # noqa: E402
import check_post  # noqa: E402

DONE = ("scheduled", "published", "posted-by-hand")


def split_lines(v):
    return [l.strip() for l in sheet.text(v).split("\n") if l.strip()]


def load_packs(sheets, settings):
    """Group the Captions tab into one pack per date and piece of content."""
    rows = sheet.table(sheet.tab(sheets, "Captions"), ["Post date", "Account key", "Caption"])
    if not rows:
        sys.exit("The posting plan has no Captions tab with the columns Post date, Account key and Caption. See references/SHEET.md.")
    notes = {}
    for r in sheet.table(sheet.tab(sheets, "Content and notes"), ["Content key"]):
        key = sheet.text(r.get("Content key")).strip()
        col = next((k for k in r if k.lower().startswith("to confirm") or k.lower().startswith("for ")), None)
        if key and col:
            notes[key] = [re.sub(r"^\d+\.\s*", "", l) for l in split_lines(r[col])]
    packs = {}
    for r in rows:
        d = sheet.to_date(r.get("Post date"))
        key = sheet.text(r.get("Content key")).strip()
        if not d or not key:
            continue
        pk = packs.setdefault((d, key), {
            "date": d, "key": key, "content": sheet.text(r.get("Content")).strip(), "format": sheet.text(r.get("Format")).strip(),
            "type": sheet.text(r.get("Type")).strip(), "media_type": (sheet.text(r.get("Media type")).strip() or "video").lower(),
            "files": split_lines(r.get("Files")), "srt": sheet.text(r.get("Caption file")).strip() or None,
            "notes": notes.get(key, []), "posts": [],
        })
        post = {"account": sheet.text(r.get("Account key")).strip(), "platform": sheet.text(r.get("Platform")).strip().lower(),
                "text": sheet.text(r.get("Caption")).strip()}
        hooks = [sheet.text(r.get(c)).strip() for c in ("Other opening 1", "Other opening 2") if sheet.text(r.get(c)).strip()]
        if hooks:
            post["hooks"] = hooks
        title = sheet.text(r.get("Title (YouTube only)") or r.get("Title")).strip()
        if title:
            post["title"] = title
        extra = sheet.text(r.get("Extra fields")).strip()
        if extra:
            try:
                post["fields"] = json.loads(extra)
            except ValueError:
                print("Extra fields ignored for %s %s (not valid JSON)" % (key, post["account"]), file=sys.stderr)
        pk["posts"].append(post)
    return [packs[k] for k in sorted(packs, key=lambda x: (x[0], x[1]))]


def read_log(settings):
    path = os.path.join(common.expand(settings.get("posts_folder") or common.DEFAULTS["posts_folder"]), "posting-log.csv")
    by = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                by.setdefault(r.get("date", ""), {})[r.get("account", "")] = r.get("state", "")
    return by


def pack_file(pk, settings):
    return {
        "date": pk["date"].isoformat(),
        "slot": " · ".join(x for x in (common.day_name(pk["date"]), pk["content"], pk["format"], pk["type"]) if x),
        "source": {"srt": pk["srt"]} if pk["srt"] else {},
        "media": {"type": pk["media_type"], "files": pk["files"], "cover": None},
        "link": settings.get("link", ""),
        "release": release(pk["date"], settings),
        "notes_to_confirm": pk["notes"],
        "posts": pk["posts"],
    }


def release(d, settings, time=None):
    hh, mm = (time or settings["posting_time"]).split(":")
    local = datetime(d.year, d.month, d.day, int(hh), int(mm))
    return {"mode": "draft", "proposed_local": local.strftime("%Y-%m-%d %H:%M"), "timezone": settings["timezone"],
            "proposed_scheduledTime": common.utc_iso(common.local_to_utc(local, settings["timezone"]))}


def describe(pk, settings, rules, log, today, start, write):
    accounts = settings.get("accounts", {})
    folder = common.expand(settings.get("handover_folder"))
    posts_folder = common.expand(settings.get("posts_folder") or common.DEFAULTS["posts_folder"])
    pack = pack_file(pk, settings)
    out = {"date": pack["date"], "day": common.day_name(pk["date"]), "content": pk["content"], "key": pk["key"],
           "format": pk["format"], "type": pk["type"], "release": pack["release"], "notes_to_confirm": pk["notes"], "files": []}
    for f in pk["files"]:
        there = bool(folder) and os.path.exists(os.path.join(folder, f))
        out["files"].append({"file": f, "state": "OK" if there else ("NO FOLDER" if not folder else "MISSING")})
    logged = log.get(pack["date"], {})
    rows = []
    for p in pk["posts"]:
        acc = accounts.get(p["account"])
        rows.append({"account": p["account"], "platform": p["platform"], "label": (acc or {}).get("label", ""),
                     "on": bool(acc and acc.get("on")), "has_id": bool(acc and acc.get("accountId")),
                     "characters": check_post.x_length(p["text"]) if p["platform"] == "twitter" else len(p["text"]),
                     "logged": logged.get(p["account"], "")})
    out["accounts"] = rows
    on_rows = [r for r in rows if r["on"]]
    done = [r for r in on_rows if r["logged"] in DONE]
    if on_rows and len(done) == len(on_rows):
        out["state"] = "DONE"
    elif done:
        out["state"] = "PART DONE"
    elif pk["date"] < start:
        out["state"] = "DATE PASSED"
    else:
        out["state"] = "DUE"
    report = check_post.check_pack(pack, settings, rules, posts_folder)
    out["blocks"] = report["blocks"] + ["%s: %s" % (p["account"], b) for p in report["posts"] for b in p["blocks"]]
    out["warns"] = report["warns"] + ["%s: %s" % (p["account"], w) for p in report["posts"] for w in p["warns"]
                                       if "switched off" not in w and "accountId" not in w]
    if write:
        d = os.path.join(posts_folder, "%s_%s" % (pack["date"], pk["key"]))
        pj = os.path.join(d, "post_v1.json")
        versions = sorted(f for f in (os.listdir(d) if os.path.isdir(d) else []) if re.fullmatch(r"post_v\d+\.json", f))
        if versions:
            out["post_file"] = os.path.join(d, versions[-1])
            out["post_file_state"] = "already there, left as it is"
        else:
            os.makedirs(d, exist_ok=True)
            with open(pj, "w", encoding="utf-8") as f:
                json.dump(pack, f, indent=2, ensure_ascii=False)
            check_post.write_review(pack, report, os.path.join(d, "post_v1.md"), settings)
            out["post_file"] = pj
            out["post_file_state"] = "written"
        out["review_page"] = os.path.splitext(out["post_file"])[0] + ".md"
    return out


def show(o):
    lines = ["%s · %s · %s · %s   [%s]" % (o["day"], o["content"], o["format"], o["type"], o["state"])]
    r = o["release"]
    lines.append("  Proposed time: %s %s = %s UTC. A proposal only: a person agrees the date and time first." % (
        r["proposed_local"], r["timezone"], r["proposed_scheduledTime"]))
    if o["state"] == "DATE PASSED":
        lines.append("  The proposed date has passed. Ask the person for a new date. Never schedule into the past.")
    for f in o["files"][:2]:
        lines.append("  File: %-9s %s" % (f["state"], f["file"]))
    if len(o["files"]) > 2:
        missing = sum(1 for f in o["files"] if f["state"] != "OK")
        lines.append("  ... %d files in all, %d not found" % (len(o["files"]), missing))
    if o["notes_to_confirm"]:
        lines.append("  To confirm before this posts:")
        lines += ["    - " + n for n in o["notes_to_confirm"]]
    lines.append("  Accounts:")
    for a in o["accounts"]:
        flag = "ON " if a["on"] else "off"
        idn = "" if a["has_id"] or not a["on"] else "  NO BLOTATO ID YET"
        log = ("  logged: " + a["logged"]) if a["logged"] else ""
        lines.append("    [%s] %-20s %-10s %5d characters%s%s" % (flag, a["account"], a["platform"], a["characters"], idn, log))
    for b in o["blocks"]:
        lines.append("  BLOCK  " + b)
    for w in o["warns"]:
        lines.append("  WARN   " + w)
    if o.get("post_file"):
        lines.append("  Post file:   %s (%s)" % (o["post_file"], o["post_file_state"]))
        lines.append("  Review page: %s" % o["review_page"])
    return "\n".join(lines)


def main():
    common.utf8_stdout()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--settings", help="settings file (default ~/.post-desk/settings.json)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("next", "day", "week", "all", "status"):
        a = sub.add_parser(name)
        a.add_argument("--file", help="read a local .xlsx copy of the plan")
        a.add_argument("--offline", action="store_true", help="use the last downloaded copy")
        a.add_argument("--json", action="store_true")
        a.add_argument("--no-write", action="store_true", help="do not write post files")
        if name in ("day", "week"):
            a.add_argument("--date", required=(name == "day"))
    a = sub.add_parser("when")
    a.add_argument("--date", required=True)
    a.add_argument("--time", help="HH:MM, default the posting_time setting")
    args = p.parse_args()

    settings = common.load_settings(args.settings)
    tz = settings["timezone"]
    now = common.now_local(tz)
    today = now.date()

    def read_date(v):
        d = {"today": today, "tomorrow": today + timedelta(days=1)}.get(v) or sheet.to_date(v)
        if not d:
            sys.exit("Could not read the date %s. Use today, tomorrow or YYYY-MM-DD." % v)
        return d

    if args.cmd == "when":
        d = read_date(args.date)
        r = release(d, settings, args.time)
        print(json.dumps({"local": r["proposed_local"], "day": common.day_name(d), "timezone": tz,
                          "scheduledTime": r["proposed_scheduledTime"],
                          "in_the_past": r["proposed_local"] <= now.strftime("%Y-%m-%d %H:%M")}, indent=2))
        return

    sheets, note = sheet.load(settings, offline=args.offline, file=args.file)
    rules = sheet.plan_rules(sheets)
    packs = load_packs(sheets, settings)
    log = read_log(settings)
    hh, mm = settings["posting_time"].split(":")
    # A post is still "due" today until the posting time has passed.
    start = today + timedelta(days=1) if (now.hour, now.minute) >= (int(hh), int(mm)) else today
    write = args.cmd in ("next", "day", "week") and not args.no_write

    if args.cmd == "day":
        d = read_date(args.date)
        chosen = [pk for pk in packs if pk["date"] == d]
    elif args.cmd == "week":
        d = read_date(args.date) if args.date else start
        monday = d - timedelta(days=d.weekday())
        chosen = [pk for pk in packs if monday <= pk["date"] <= monday + timedelta(days=6)]
    else:
        chosen = packs

    described = [describe(pk, settings, rules, log, today, start, write and args.cmd != "next") for pk in chosen]
    missed = []
    if args.cmd == "next":
        missed = [o for o in described if o["state"] == "DATE PASSED"]
        upcoming = [(pk, o) for pk, o in zip(chosen, described) if pk["date"] >= start and o["state"] not in ("DONE",)]
        described = [describe(upcoming[0][0], settings, rules, log, today, start, write)] if upcoming else []

    head = {"plan": note, "brand": settings.get("brand", ""), "today": common.day_name(today), "timezone": tz,
            "posting_time": settings["posting_time"], "handover_folder": settings.get("handover_folder") or "(not set)"}
    if args.json:
        print(json.dumps({**head, "posts": described, "missed": missed}, indent=2, ensure_ascii=False, default=str))
        return
    print("Plan: %s" % note)
    print("%sToday is %s in %s. Posts go out at %s." % ((settings["brand"] + ". ") if settings.get("brand") else "", head["today"], tz, settings["posting_time"]))
    print("Handover folder: %s" % head["handover_folder"])
    print("")
    if args.cmd == "status":
        for o in described:
            on = [a for a in o["accounts"] if a["on"]]
            done = [a for a in on if a["logged"] in DONE]
            print("%-16s %-11s %d of %d accounts logged   %s" % (o["day"], o["state"], len(done), len(on), o["content"]))
        counts = {}
        for o in described:
            counts[o["state"]] = counts.get(o["state"], 0) + 1
        print("")
        print("Summary: " + ", ".join("%s %d" % kv for kv in sorted(counts.items())))
        print("This log is this computer's record only. Check Blotato's own post list before you call anything missing.")
        return
    if not described:
        print("Nothing in the plan for that." if args.cmd != "next" else "Nothing left to post in the plan.")
    for o in described:
        print(show(o))
        print("")
    if missed:
        print("Dates that have passed with nothing logged (ask the person what to do with each):")
        for o in missed:
            print("  %s · %s" % (o["day"], o["content"]))


if __name__ == "__main__":
    main()
