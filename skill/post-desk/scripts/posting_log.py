"""The posting log: one line per account per post, so we always know what went where.

The posting plan sheet is view-only, so this log is the record of what has been scheduled and posted on this computer.
It lives in the posts folder as posting-log.csv and opens in Excel or Google Sheets.

  posting_log.py add --date 2026-11-12 --account founder_linkedin --platform linkedin \\
      --submission <postSubmissionId> --state scheduled --scheduled 2026-11-11T20:00:00Z --pack <post_v1.json>
  posting_log.py update --submission <postSubmissionId> --state published --url <public post URL>
  posting_log.py list [--from 2026-11-11] [--to 2026-11-20]
"""
import argparse
import csv
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

common.utf8_stdout()

FIELDS = ["logged_at", "date", "account", "platform", "submission_id", "state", "scheduled_utc", "public_url", "pack", "note"]
STATES = ("drafted", "approved", "scheduled", "published", "failed", "cancelled", "posted-by-hand")


def log_path(settings):
    folder = common.expand(settings.get("posts_folder") or common.DEFAULTS["posts_folder"])
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "posting-log.csv")


def read(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write(path, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    os.replace(tmp, path)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--settings")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    for k in ("date", "account", "platform", "state"):
        a.add_argument("--" + k, required=True)
    for k in ("submission", "scheduled", "url", "pack", "note"):
        a.add_argument("--" + k, default="")
    u = sub.add_parser("update")
    u.add_argument("--submission", required=True)
    u.add_argument("--state", required=True)
    u.add_argument("--url", default="")
    u.add_argument("--note", default="")
    l = sub.add_parser("list")
    l.add_argument("--from", dest="from_")
    l.add_argument("--to")
    args = p.parse_args()

    settings = common.load_settings(args.settings, required=False)
    path = log_path(settings)
    rows = read(path)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    if args.cmd == "add":
        if args.state not in STATES:
            sys.exit("state must be one of: " + ", ".join(STATES))
        if args.submission and any(r["submission_id"] == args.submission for r in rows):
            sys.exit("Already logged: %s. Use update instead." % args.submission)
        dupes = [r for r in rows if r["date"] == args.date and r["account"] == args.account
                 and r["state"] in ("scheduled", "published", "posted-by-hand")]
        rows.append({"logged_at": stamp, "date": args.date, "account": args.account, "platform": args.platform,
                     "submission_id": args.submission, "state": args.state, "scheduled_utc": args.scheduled,
                     "public_url": args.url, "pack": args.pack, "note": args.note})
        write(path, rows)
        print("Logged %s %s %s" % (args.date, args.account, args.state))
        if dupes:
            print("WARNING: %s already has a %s post logged for %s. Check this is not a double post." % (
                args.account, dupes[0]["state"], args.date))
    elif args.cmd == "update":
        hit = [r for r in rows if r["submission_id"] == args.submission]
        if not hit:
            sys.exit("No log line with submission %s" % args.submission)
        for r in hit:
            r["state"] = args.state
            if args.url:
                r["public_url"] = args.url
            if args.note:
                r["note"] = args.note
            r["logged_at"] = stamp
        write(path, rows)
        print("Updated %s to %s" % (args.submission, args.state))
    else:
        shown = [r for r in rows if (not args.from_ or r["date"] >= args.from_) and (not args.to or r["date"] <= args.to)]
        print("Log: %s" % path)
        if not shown:
            print("Nothing logged in that range.")
        for r in shown:
            print("%s  %-18s %-10s %-14s %s" % (r["date"], r["account"], r["platform"], r["state"], r["public_url"] or r["scheduled_utc"]))


if __name__ == "__main__":
    main()
