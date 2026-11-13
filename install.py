#!/usr/bin/env python3
"""Install or update Post Desk for Claude Code and Codex on this computer.

  python3 install.py              install, or update an earlier install (Windows: python install.py)
  python3 install.py --dry-run    show every change, write nothing
  python3 install.py --uninstall  remove what this installer added

It copies the skill and the four commands into your home folder. It is safe to run again. It never touches your
settings, your drafts or your posting log (~/.post-desk and your posts folder), and it never overwrites a file or
folder it did not install: that is reported as CONFLICT and left alone.
"""
import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
MARKER = ".post-desk-install"
COMMAND_MARK = "post-desk command"
COMMANDS = ("post-setup", "post-next", "post-week", "post-status")


def version():
    with open(os.path.join(HERE, "VERSION"), encoding="utf-8") as f:
        return f.read().strip()


class Run:
    def __init__(self, dry):
        self.dry = dry
        self.conflicts = 0

    def say(self, what, path):
        print("%-9s %s" % (("would " if self.dry and what not in ("CONFLICT", "skip") else "") + what, path))

    def copy_tree(self, src, dest):
        if os.path.exists(dest) and not os.path.exists(os.path.join(dest, MARKER)):
            self.conflicts += 1
            self.say("CONFLICT", dest + "  (a folder is already there that this installer did not make)")
            return
        self.say("update" if os.path.exists(dest) else "install", dest)
        if self.dry:
            return
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        with open(os.path.join(dest, MARKER), "w", encoding="utf-8") as f:
            f.write(version() + "\n")

    def copy_file(self, src, dest):
        if os.path.exists(dest):
            with open(dest, encoding="utf-8", errors="replace") as f:
                if COMMAND_MARK not in f.read():
                    self.conflicts += 1
                    self.say("CONFLICT", dest + "  (a file is already there that this installer did not make)")
                    return
        self.say("update" if os.path.exists(dest) else "install", dest)
        if self.dry:
            return
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src, dest)

    def remove(self, path, is_dir):
        if not os.path.exists(path):
            return
        ours = os.path.exists(os.path.join(path, MARKER)) if is_dir else COMMAND_MARK in open(path, encoding="utf-8", errors="replace").read()
        if not ours:
            self.say("skip", path + "  (not installed by this installer)")
            return
        self.say("remove", path)
        if not self.dry:
            shutil.rmtree(path) if is_dir else os.remove(path)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--uninstall", action="store_true")
    a = p.parse_args()
    if sys.version_info < (3, 8):
        sys.exit("Python 3.8 or later is needed. This is %s." % sys.version.split()[0])
    run = Run(a.dry_run)
    claude = os.path.join(HOME, ".claude")
    agents = os.path.join(HOME, ".agents")
    has_codex = os.path.isdir(os.path.join(HOME, ".codex")) or os.path.isdir(agents)
    has_claude = os.path.isdir(claude) or not has_codex  # with neither tool found, install for Claude Code
    skill = os.path.join(HERE, "skill", "post-desk")

    if a.uninstall:
        run.remove(os.path.join(claude, "skills", "post-desk"), True)
        run.remove(os.path.join(agents, "skills", "post-desk"), True)
        for c in COMMANDS:
            run.remove(os.path.join(claude, "commands", c + ".md"), False)
            run.remove(os.path.join(agents, "skills", c), True)
        print("\nYour settings, drafts and posting log were left alone (~/.post-desk and your posts folder).")
        return

    print("Post Desk %s" % version())
    if has_claude:
        run.copy_tree(skill, os.path.join(claude, "skills", "post-desk"))
        for c in COMMANDS:
            run.copy_file(os.path.join(HERE, "commands", "claude", c + ".md"), os.path.join(claude, "commands", c + ".md"))
    else:
        print("skip      Claude Code (no ~/.claude folder on this computer)")
    if has_codex:
        run.copy_tree(skill, os.path.join(agents, "skills", "post-desk"))
        for c in COMMANDS:
            run.copy_tree(os.path.join(HERE, "commands", "codex", c), os.path.join(agents, "skills", c))
    else:
        print("skip      Codex (no ~/.codex folder on this computer)")

    print("")
    if run.conflicts:
        print("%d CONFLICT line(s) above were left alone. Rename or remove those yourself if they are old copies, then run this again." % run.conflicts)
    if a.dry_run:
        print("Dry run: nothing was written.")
        return
    print("Done. Your settings in ~/.post-desk were not touched.")
    print("Next: quit and reopen Claude Code (or Codex), then type  /post-setup  followed by the link to your posting plan.")
    print("In Codex the commands start with a dollar sign:  $post-setup  $post-next  $post-week  $post-status")


if __name__ == "__main__":
    main()
