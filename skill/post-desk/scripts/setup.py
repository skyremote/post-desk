"""Set up Post Desk on this computer.

  setup.py init --sheet "<link>"     save the posting plan link, download the plan, and read its Settings and Accounts tabs
  setup.py init --sheet "<link>" --import-old "<old settings.json>"   also bring account ids and folders from an older skill
  setup.py refresh                   download the plan again and take any changed settings from it
  setup.py show                      print the settings and what is still missing
  setup.py find-folder [--save]      look for the synced handover folder
  setup.py set <key> <value>         change a top-level setting, e.g. set handover_folder "G:\\My Drive\\Deliverables"
  setup.py account <key> [--id ID] [--page PAGE_ID] [--on | --off]
                                     record which Blotato account is which

Running init again is safe: it never removes an account id, a page id, a folder or an on/off choice already saved.
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import sheet  # noqa: E402

common.utf8_stdout()

PLAN_KEYS = ("brand", "timezone", "posting_time", "link", "web_address")


def merge_plan(s, sheets, first_time):
    """Take the plan-wide settings and the account list from the sheet. Local ids, folders and on/off choices stay."""
    ps = sheet.plan_settings(sheets)
    for k in PLAN_KEYS:
        if ps.get(k):
            s[k] = ps[k]
    if "wrong_web_addresses" in ps:
        s["wrong_web_addresses"] = [x.strip() for x in ps["wrong_web_addresses"].split(",") if x.strip()]
    if "handover_markers" in ps:
        s["handover_markers"] = [x.strip() for x in ps["handover_markers"].split("|") if x.strip()]
    for k in ("no_emojis", "linkedin_hashtags"):
        if k in ps:
            s[k] = common.truthy(ps[k])
    if ps.get("posts_folder") and (first_time or not s.get("posts_folder") or s["posts_folder"] == common.DEFAULTS["posts_folder"]):
        s["posts_folder"] = ps["posts_folder"]
    added = []
    for r in sheet.plan_accounts(sheets):
        key = sheet.text(r.get("Account key")).strip()
        if not key:
            continue
        acc = s["accounts"].get(key)
        if acc is None:
            acc = s["accounts"][key] = {"on": common.truthy(r.get("On by default")), "accountId": ""}
            added.append(key)
        acc["platform"] = sheet.text(r.get("Platform")).strip().lower()
        acc["label"] = sheet.text(r.get("Name")).strip()
        acc["needs_page"] = common.truthy(r.get("Needs a page id"))
        if acc["needs_page"]:
            acc.setdefault("pageId", "")
    return added


def import_old(s, path):
    """Bring account ids, page ids, on/off choices and folders from an older skill's settings file."""
    path = common.expand(path)
    if not os.path.exists(path):
        print("No older settings at %s, nothing to bring across." % path)
        return
    with open(path, encoding="utf-8") as f:
        old = json.load(f)
    n = 0
    for key, o in (old.get("accounts") or {}).items():
        acc = s["accounts"].get(key)
        if not acc:
            continue
        if o.get("accountId") and not acc.get("accountId"):
            acc["accountId"] = o["accountId"]
            if "on" in o:
                acc["on"] = bool(o["on"])
            n += 1
        if o.get("pageId") and not acc.get("pageId"):
            acc["pageId"] = o["pageId"]
    old_folder = old.get("handover_folder") or old.get("deliverables_folder")
    if old_folder and not s.get("handover_folder"):
        s["handover_folder"] = old_folder
    if old.get("posts_folder") and s.get("posts_folder") in ("", common.DEFAULTS["posts_folder"]):
        s["posts_folder"] = old["posts_folder"]
    print("Brought across from %s: %d account ids%s." % (path, n, ", the handover folder" if old_folder else ""))


def cmd_init(args):
    first_time = not os.path.exists(common.SETTINGS_PATH)
    s = common.load_settings(required=False)
    if args.sheet:
        s["sheet_url"] = args.sheet.strip()
    if not s.get("sheet_url"):
        sys.exit("Give the posting plan link: setup.py init --sheet \"<link>\"")
    common.save_settings(s)
    sheets, note = sheet.load(s)
    added = merge_plan(s, sheets, first_time)
    if args.import_old:
        import_old(s, args.import_old)
    common.save_settings(s)
    print("%s %s" % ("Created" if first_time else "Updated", common.SETTINGS_PATH))
    print("Plan: %s" % note)
    if added:
        print("Accounts added from the plan: %s" % ", ".join(added))
    print("")
    cmd_show(args)


def cmd_refresh(args):
    s = common.load_settings()
    sheets, note = sheet.load(s)
    added = merge_plan(s, sheets, False)
    common.save_settings(s)
    print("Plan: %s" % note)
    if added:
        print("Accounts added from the plan: %s" % ", ".join(added))


def cmd_show(args):
    s = common.load_settings()
    print("Settings file: %s" % common.SETTINGS_PATH)
    print("Brand: %s" % (s.get("brand") or "(not set)"))
    print("Time zone: %s, posting time %s" % (s["timezone"], s["posting_time"]))
    print("Link in posts: %s   Web address: %s" % (s.get("link") or "-", s.get("web_address") or "-"))
    print("Handover folder: %s" % (s.get("handover_folder") or "(not set)"))
    print("Drafts and log: %s" % common.expand(s.get("posts_folder")))
    print("")
    print("Accounts:")
    for key, acc in s["accounts"].items():
        state = "ON " if acc.get("on") else "off"
        ids = "id saved" if acc.get("accountId") else "no id"
        if acc.get("needs_page"):
            ids += ", page saved" if acc.get("pageId") else ", no page"
        print("  [%s] %-20s %-10s %-20s %s" % (state, key, acc.get("platform", ""), ids, acc.get("label", "")))
    gaps = common.missing(s)
    print("")
    if gaps:
        print("Still to do:")
        for g in gaps:
            print("  - " + g)
    else:
        print("Set-up complete.")


def candidate_roots():
    home = os.path.expanduser("~")
    roots = []
    roots += glob.glob(os.path.join(home, "Library", "CloudStorage", "GoogleDrive-*"))
    roots += [os.path.join(home, "Google Drive"), os.path.join(home, "My Drive")]
    for letter in "GHIJKDEF":
        roots.append("%s:\\" % letter)
    roots += [os.path.join(home, d) for d in ("Desktop", "Documents", "Downloads")]
    return [r for r in roots if os.path.isdir(r)]


def cmd_find_folder(args):
    s = common.load_settings()
    markers = s.get("handover_markers") or []
    if not markers:
        sys.exit("The plan names no folders to look for. Set it by hand: setup.py set handover_folder \"<path>\"")
    hits = []
    for root in ([common.expand(args.under)] if args.under else candidate_roots()):
        base_depth = root.rstrip(os.sep).count(os.sep)
        for dirpath, dirnames, _ in os.walk(root):
            depth = dirpath.count(os.sep) - base_depth
            if depth > 6:
                dirnames[:] = []
                continue
            if all(m in dirnames for m in markers):
                hits.append(dirpath)
                dirnames[:] = []
    if not hits:
        print("Not found. In Google Drive, add a shortcut to the shared handover folder in My Drive, make it available "
              "offline, then run this again. Or set it by hand: setup.py set handover_folder \"<path>\"")
        return
    for h in hits:
        print(h)
    if len(hits) == 1 and args.save:
        s["handover_folder"] = hits[0]
        common.save_settings(s)
        print("Saved as handover_folder.")
    elif args.save:
        print("More than one folder matches. Ask the person which one, then: setup.py set handover_folder \"<path>\"")


def cmd_set(args):
    s = common.load_settings()
    if args.key not in common.DEFAULTS or isinstance(common.DEFAULTS[args.key], (dict, list)):
        sys.exit("Unknown or nested setting: %s" % args.key)
    s[args.key] = common.truthy(args.value) if isinstance(common.DEFAULTS[args.key], bool) else args.value
    common.save_settings(s)
    print("%s = %s" % (args.key, s[args.key]))


def cmd_account(args):
    s = common.load_settings()
    acc = s["accounts"].get(args.key)
    if acc is None:
        sys.exit("Unknown account %s. Accounts: %s" % (args.key, ", ".join(s["accounts"])))
    if args.id is not None:
        acc["accountId"] = args.id
    if args.page is not None:
        acc["pageId"] = args.page
    if args.on:
        acc["on"] = True
    if args.off:
        acc["on"] = False
    common.save_settings(s)
    print("%s: %s, %s%s" % (args.key, "on" if acc.get("on") else "off", "id saved" if acc.get("accountId") else "no id",
                            (", page saved" if acc.get("pageId") else ", no page") if acc.get("needs_page") else ""))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("init")
    a.add_argument("--sheet", help="link to the posting plan sheet")
    a.add_argument("--import-old", help="an older skill's settings.json to bring account ids and folders from")
    sub.add_parser("refresh")
    sub.add_parser("show")
    a = sub.add_parser("find-folder")
    a.add_argument("--save", action="store_true", help="save it if exactly one folder is found")
    a.add_argument("--under", help="look only under this folder")
    a = sub.add_parser("set")
    a.add_argument("key")
    a.add_argument("value")
    a = sub.add_parser("account")
    a.add_argument("key")
    a.add_argument("--id")
    a.add_argument("--page")
    a.add_argument("--on", action="store_true")
    a.add_argument("--off", action="store_true")
    args = p.parse_args()
    {"init": cmd_init, "refresh": cmd_refresh, "show": cmd_show, "find-folder": cmd_find_folder, "set": cmd_set,
     "account": cmd_account}[args.cmd](args)


if __name__ == "__main__":
    main()
