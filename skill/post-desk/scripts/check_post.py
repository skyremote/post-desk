"""Check a post file against the house rules in the posting plan sheet and each platform's limits.

  check_post.py "<posts folder>/2026-11-16_launch/post_v1.json"
  check_post.py post_v1.json --review post_v1.md      also write a page for a person to read
  check_post.py --platform linkedin --text "the caption"   check one caption

BLOCK means fix it before it posts. WARN means a person looks at it and decides.
Exit code 1 if anything is blocked.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import sheet  # noqa: E402

common.utf8_stdout()

EMOJI = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF️‍]")
URL = re.compile(r"https?://\S+")
HASHTAG = re.compile(r"(?<!\w)#\w+")
SRT_TIME = re.compile(r"\d+:\d+:\d+[,.]\d+\s*-->\s*\d+:\d+:\d+[,.]\d+")

LIMITS = {"twitter": 280, "threads": 500, "instagram": 2200, "linkedin": 3000, "facebook": 60000, "youtube": 5000,
          "tiktok": 2200, "bluesky": 300}


def x_length(text):
    # X counts every link as 23 characters.
    return len(URL.sub("x" * 23, text))


def numbers(text):
    return set(re.findall(r"\d+(?:\.\d+)?%?", text))


def srt_words(path):
    """The spoken words of a clip, from its .srt caption file."""
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        blocks = re.split(r"\n\s*\n", f.read().replace("\r\n", "\n").strip())
    words = []
    for b in blocks:
        lines = [l.strip() for l in b.split("\n") if l.strip()]
        for i, l in enumerate(lines):
            if SRT_TIME.search(l):
                words.append(" ".join(re.sub(r"<[^>]+>", "", x) for x in lines[i + 1:]))
                break
    return re.sub(r"\s+", " ", " ".join(words)).strip()


def check_text(text, platform, settings, rules, srt_text=None, title=None):
    blocks, warns = [], []
    low_platform = (platform or "").lower()
    for level, pat, why in rules:
        for m in pat.finditer(text):
            (blocks if level == "BLOCK" else warns).append("'%s': %s" % (m.group(0), why))
    if settings.get("no_emojis") and EMOJI.search(text):
        blocks.append("emoji found: the house rule is no emojis")
    for wrong in settings.get("wrong_web_addresses") or []:
        if wrong and wrong.lower() in text.lower():
            warns.append("'%s': the web address is %s" % (wrong, settings.get("web_address")))
    if srt_text is not None:
        extra = sorted(n for n in numbers(text) - numbers(srt_text) if len(n.strip("%")) > 1 or "%" in n)
        if extra:
            warns.append("figures not in the clip's own words: %s. Use only figures the owner has confirmed" % ", ".join(extra))
    tags = HASHTAG.findall(text)
    limit = LIMITS.get(low_platform)
    length = x_length(text) if low_platform == "twitter" else len(text)
    if limit and length > limit:
        blocks.append("%d characters, the %s limit is %d" % (length, platform, limit))
    first_para = text.strip().split("\n\n")[0] if text.strip() else ""
    link = settings.get("link") or ""
    web = settings.get("web_address") or ""
    has_link = bool(URL.search(text)) or bool(web and web in text)
    if low_platform == "linkedin":
        if tags and not settings.get("linkedin_hashtags"):
            warns.append("hashtags on LinkedIn: the plan has no hashtag block under the post")
        if len(first_para) > 210:
            warns.append("the opening runs %d characters. LinkedIn cuts at about two lines before 'see more'" % len(first_para))
        if link and not has_link:
            warns.append("no link. Every post points to %s" % link)
    elif low_platform == "instagram":
        if len(tags) > 30:
            blocks.append("%d hashtags, Instagram allows 30" % len(tags))
        elif len(tags) > 8:
            warns.append("%d hashtags. About five reads better" % len(tags))
        if URL.search(text):
            warns.append("links in an Instagram caption are not clickable. Say 'link in bio' and keep the bio link current")
        if len(first_para.split("\n")[0]) > 125:
            warns.append("the first line runs past about 125 characters, where Instagram cuts to 'more'")
    elif low_platform in ("facebook", "threads", "twitter"):
        if link and not has_link:
            warns.append("no link. Every post points to %s" % link)
        if low_platform == "twitter" and len(tags) > 2:
            warns.append("%d hashtags on X. One or none reads better" % len(tags))
    elif low_platform == "youtube":
        if not title:
            blocks.append("YouTube needs a title")
        elif len(title) > 100:
            blocks.append("title is %d characters, YouTube allows 100" % len(title))
        elif len(title) > 70:
            warns.append("title is %d characters. Under 70 shows in full" % len(title))
    if title:
        b, w = check_text(title, "", settings, rules)[:2]
        blocks += ["title: " + x for x in b]
        warns += ["title: " + x for x in w]
    return blocks, warns, length


def resolve_media(path, folder, base):
    if os.path.isabs(common.expand(path)):
        return common.expand(path)
    for root in (folder, base):
        if root:
            p = os.path.join(root, path)
            if os.path.exists(p):
                return p
    return os.path.join(folder or base, path)


def check_pack(pack, settings, rules, base):
    report = {"blocks": [], "warns": [], "posts": []}
    folder = common.expand(settings.get("handover_folder"))
    media = pack.get("media") or {}
    srt_text = None
    srt = (pack.get("source") or {}).get("srt")
    if srt:
        sp = resolve_media(srt, folder, base)
        if os.path.exists(sp):
            srt_text = srt_words(sp)
        else:
            report["warns"].append("caption file not found: %s" % srt)
    files = media.get("files") or []
    if media.get("type") in ("video", "photo", "carousel") and not files:
        report["blocks"].append("no media files listed")
    for f in files + ([media["cover"]] if media.get("cover") else []):
        if not os.path.exists(resolve_media(f, folder, base)):
            report["blocks"].append("media file not found: %s" % f)
    rel = pack.get("release") or {}
    mode = rel.get("mode", "draft")
    if mode == "scheduled":
        st_time = rel.get("scheduledTime")
        if not st_time:
            report["blocks"].append("scheduled, but no scheduledTime (UTC). Use plan.py when")
        else:
            when = datetime.strptime(st_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if when <= datetime.now(timezone.utc):
                report["blocks"].append("the scheduled time %s has already passed" % st_time)
            if rel.get("local") and rel.get("timezone"):
                local = datetime.strptime(rel["local"], "%Y-%m-%d %H:%M")
                if common.utc_iso(common.local_to_utc(local, rel["timezone"])) != st_time:
                    report["blocks"].append("local time %s %s does not match scheduledTime %s" % (rel["local"], rel["timezone"], st_time))
    accounts = settings.get("accounts", {})
    openings = {}
    for post in pack.get("posts", []):
        role = post.get("account")
        acc = accounts.get(role)
        platform = post.get("platform") or (acc or {}).get("platform")
        entry = {"account": role, "platform": platform}
        b, w, length = check_text(post.get("text", ""), platform, settings, rules, srt_text, post.get("title"))
        for i, hook in enumerate(post.get("hooks") or [], 1):
            hb, hw, _ = check_text(hook, "", settings, rules, srt_text)
            b += ["other opening %d: %s" % (i, x) for x in hb]
            w += ["other opening %d: %s" % (i, x) for x in hw]
        if acc is None:
            b.append("unknown account '%s'. It is not in the settings" % role)
        else:
            if not acc.get("on"):
                w.append("this account is switched off in the settings")
            if not acc.get("accountId"):
                w.append("no Blotato accountId in the settings yet (needed before it can post)")
            if platform != acc.get("platform"):
                b.append("platform '%s' does not match the account's platform '%s'" % (platform, acc.get("platform")))
        if media.get("type") == "carousel":
            if platform == "linkedin":
                w.append("Blotato posts the slides as a multi-image post. For the PDF document version, upload the PDF in LinkedIn by hand")
            if platform == "instagram" and any(f.lower().endswith(".mp4") for f in files):
                w.append("animated slides in an Instagram carousel are untested through Blotato. Test once, or post them by hand")
        if platform == "instagram" and media.get("type") == "video" and (post.get("fields") or {}).get("mediaType") != "reel":
            w.append("vertical clips go to Instagram as a reel: set fields.mediaType to 'reel'")
        opening = post.get("text", "").strip().split("\n")[0].strip().lower()
        if opening:
            if opening in openings:
                w.append("opens with the same line as %s. Each account gets its own opening" % openings[opening])
            openings.setdefault(opening, role)
        entry.update(blocks=b, warns=w, length=length)
        report["posts"].append(entry)
    report["release"] = rel
    return report


def is_bad(report):
    return bool(report["blocks"]) or any(p["blocks"] for p in report["posts"])


def print_report(report):
    for x in report["blocks"]:
        print("BLOCK  " + x)
    for x in report["warns"]:
        print("WARN   " + x)
    for p in report["posts"]:
        state = "BLOCK" if p["blocks"] else ("WARN " if p["warns"] else "OK   ")
        print("%s  %-20s %-10s %d characters" % (state, p["account"], p["platform"], p["length"]))
        for x in p["blocks"]:
            print("         BLOCK  " + x)
        for x in p["warns"]:
            print("         WARN   " + x)
    print("")
    bad = is_bad(report)
    print("Result: %s" % ("BLOCKED. Fix the BLOCK lines, then check again." if bad else "No blocks. Show the person the WARN lines and the captions."))
    return bad


def write_review(pack, report, path, settings=None):
    accounts = (settings or {}).get("accounts") or {}
    labels = {k: v.get("label") or k for k, v in accounts.items()}
    out = ["# %s" % (pack.get("slot") or pack.get("date", "Post")), ""]
    rel = pack.get("release") or {}
    draft = "draft, no time agreed yet"
    if rel.get("proposed_local"):
        draft += ". Proposed: %s %s (UTC %s)" % (rel["proposed_local"], rel.get("timezone", ""), rel.get("proposed_scheduledTime", ""))
    out.append("Release: %s" % {"scheduled": "scheduled for %s %s (UTC %s)" % (rel.get("local"), rel.get("timezone"), rel.get("scheduledTime")),
                                 "now": "post now"}.get(rel.get("mode"), draft))
    media = pack.get("media") or {}
    out.append("Media: %s" % ", ".join(media.get("files") or ["none"]))
    if media.get("cover"):
        out.append("Cover: %s" % media["cover"])
    out.append("Link: %s" % pack.get("link", ""))
    out.append("")
    if pack.get("notes_to_confirm"):
        out.append("To confirm before this posts:")
        out += ["- " + n for n in pack["notes_to_confirm"]]
        out.append("")
    by_role = {p["account"]: p for p in report["posts"]}
    for post in pack.get("posts", []):
        r = by_role.get(post.get("account"), {})
        off = "" if (accounts.get(post.get("account")) or {}).get("on") else ", SWITCHED OFF: do not post"
        out.append("## %s (%s, %s%s)" % (labels.get(post.get("account"), post.get("account")), post.get("account"), post.get("platform"), off))
        if post.get("title"):
            out.append("Title: " + post["title"])
            out.append("")
        out.append(post.get("text", ""))
        out.append("")
        if post.get("hooks"):
            out.append("Other openings to choose from:")
            out += ["- " + h for h in post["hooks"]]
            out.append("")
        checks = ["BLOCK: " + x for x in r.get("blocks", [])] + ["Check: " + x for x in r.get("warns", [])]
        out.append("Rules check: " + ("all clear" if not checks else "for a person to look at"))
        out += ["- " + c for c in checks]
        out.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def load_rules(settings, file=None):
    """Rules come from the last downloaded copy of the plan, so a check never needs the internet."""
    if not file and not os.path.exists(common.PLAN_CACHE):
        return []
    sheets, _ = sheet.load(settings, offline=True, file=file)
    return sheet.plan_rules(sheets)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("pack", nargs="?")
    p.add_argument("--settings")
    p.add_argument("--file", help="read the rules from a local .xlsx copy of the plan")
    p.add_argument("--review", help="write a Markdown review page here")
    p.add_argument("--platform")
    p.add_argument("--text")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    settings = common.load_settings(a.settings, required=False)
    rules = load_rules(settings, a.file)
    if not rules:
        print("NOTE: no house rules loaded (no copy of the posting plan yet). Only the platform limits are checked.", file=sys.stderr)
    if a.text is not None:
        b, w, n = check_text(a.text, a.platform or "", settings, rules)
        report = {"blocks": [], "warns": [], "posts": [{"account": "(text)", "platform": a.platform or "-", "blocks": b, "warns": w, "length": n}]}
        sys.exit(1 if print_report(report) else 0)
    if not a.pack:
        p.error("give a post_vN.json, or --text")
    with open(a.pack, encoding="utf-8") as f:
        pack = json.load(f)
    report = check_pack(pack, settings, rules, os.path.dirname(os.path.abspath(a.pack)))
    if a.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        bad = is_bad(report)
    else:
        bad = print_report(report)
    if a.review:
        write_review(pack, report, a.review, settings)
        print("Review page written: %s" % a.review)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
