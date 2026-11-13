# Post Desk

One sheet of captions, every account, each with its own caption, scheduled through Blotato.

Post Desk is a skill for Claude Code and Codex. Your captions, your dates and your house rules live in one Google
Sheet (the posting plan). You type one command, the agent shows you the next post and its captions, and it schedules
them through [Blotato](https://www.blotato.com) only after you have said yes and agreed a time.

Nothing posts until you have seen the captions and said when it goes live.

## Install

You need Python 3.8 or later, and Claude Code or Codex.

Paste this to your agent:

> Install Post Desk from https://github.com/skyremote/post-desk. Download the repository into a folder called
> `post-desk` in my home folder, run its `install.py` with `--dry-run` first and show me the output, then run it
> without `--dry-run`. Tell me to restart when it is done.

Or do it yourself in a terminal:

```
git clone https://github.com/skyremote/post-desk.git ~/post-desk
python3 ~/post-desk/install.py
```

No git? Download the ZIP from the green Code button, unzip it, and run `python3 install.py` inside the folder.
On Windows, type `python` in place of `python3`.

To update later, run `git pull` in the folder and run `install.py` again. Your settings stay as they are.

## The commands

| What it does | Claude Code | Codex |
|---|---|---|
| Set up this computer, once | `/post-setup <link to your posting plan>` | `$post-setup <link>` |
| Show the next post and its captions, then wait for your yes and a time | `/post-next` | `$post-next` |
| Go through this week's posts one by one, then schedule the approved ones | `/post-week` | `$post-week` |
| What is scheduled, published, failed or overdue | `/post-status` | `$post-status` |

Codex no longer reads custom slash commands, so there the commands are skills: type `$` and the name.

## What you need before set-up

- The link to your posting plan sheet, shared as "anyone with the link can view".
- Your own Blotato account, with your social accounts connected in it.
- The media files on the computer, usually a shared Google Drive folder synced with Google Drive for desktop.

`/post-setup` walks you through the rest, one step at a time. It takes about 20 minutes. Never paste your Blotato key
into the chat. The set-up shows you a terminal command to paste it into.

## What it will not do

- Post or schedule anything before a person has agreed the date and the time.
- Rewrite your captions. It uses the words in the sheet.
- Schedule into the past. If a date in the plan has passed, it asks you for a new one.
- Post to an account you have switched off.
- Post content that is not in the posting plan.

## Where things go on your computer

- Settings: `~/.post-desk/settings.json`. The installer never touches them.
- Drafts and the log: the posts folder named in your plan (by default `Documents/Social Posts`). One folder per post,
  with `post_v1.json` (the captions), `post_v1.md` (a page a person can read), and `posting-log.csv`.
- The skill: `~/.claude/skills/post-desk` and, for Codex, `~/.agents/skills/post-desk`.

Use one computer for scheduling. The posting log lives on that computer, and Blotato's own post list is the check
against a double post.

## Making a posting plan sheet

`skill/post-desk/references/SHEET.md` lists the tabs and columns. The sheet is the one source: change a caption or a
date there, and every computer picks it up on the next command.

## Remove it

`python3 install.py --uninstall`. Your settings, drafts and posting log stay.

## Tested and not tested

Tested on a Mac: the installer (fresh install, update, dry run, uninstall, conflicts), reading a real posting plan
through the sheet download, the dates and the time-zone conversion, the house-rules check, the post files and review
pages, and the posting log. Not tested yet: Windows, and a full scheduled post through Blotato from these commands.
Watch the first scheduled post go out.

Made by [NavAIgate](https://navaigate.dev).
