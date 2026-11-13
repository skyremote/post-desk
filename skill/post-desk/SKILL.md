---
name: post-desk
description: Post ready-written social captions from a posting plan sheet to every account through Blotato, each account with its own caption, on the dates in the plan. Use whenever someone says "/post-next", "/post-week", "/post-status", "/post-setup", "do the next post", "do tomorrow's post", "schedule this week's posts", "what's due", "what's been posted", "push it to Blotato", or asks to post or schedule content that is listed in the posting plan. Not for writing new captions or making videos and carousels.
---

# Post Desk

The posting plan is one Google Sheet. It holds every caption, the proposed date for each post, the accounts, and the
house rules. This skill reads the sheet, shows a person the captions for the next post, and schedules them through
Blotato (the tool that posts to all the accounts at once) only after that person has said yes and agreed a time.

**Done looks like this:** the person has seen every caption and the "to confirm" notes, has agreed the date and time,
Blotato has accepted one post per switched-on account, and the posting log shows the state of each one.

## The ground rules, and why

1. **A person approves before anything posts.** Draft it, show it, then wait. Showing the captions is never permission
   to post, and every date in the plan is a proposal.
2. **Use the captions in the plan, word for word.** Do not rewrite, shorten or "improve" them. If the person asks for a
   change, make that change only, save it as the next version of the post file, and check it again.
3. **The "to confirm" notes come first.** If a note asks a question, the post waits for the owner's answer.
4. **Never schedule into the past, and never pick a time yourself.** If a proposed date has passed, ask for a new one.
5. **One computer schedules.** The posting log lives on this computer, so Blotato's own post list is the real check
   against a double post. Look there before every scheduling run.
6. **Never ask for, paste or repeat a key or a password in the chat.** Account ids go into the `setup.py account`
   command and nowhere else: do not print them in a reply.

## The scripts

They live in this skill's `scripts` folder. Run them by full path, in quotes. On a Mac use `python3`, on Windows use
`python` (or `py`). Settings live in `~/.post-desk/settings.json`, so an updated skill never wipes them.

| Script | What it does |
|---|---|
| `setup.py` | `init --sheet "<link>"`, `show` (what is still missing), `find-folder --save`, `set`, `account`, `refresh` |
| `plan.py` | `next`, `day --date <date>`, `week`, `all`, `status`, `when --date <date>` (local time to UTC) |
| `check_post.py` | the house rules and each platform's limits, for a post file or one caption |
| `posting_log.py` | `add`, `update`, `list`: the record of what was scheduled and posted |
| `put_file.py` | uploads a local file to the address Blotato gives you, on Mac or Windows |

`plan.py next`, `day` and `week` write a post file (`post_v1.json`) and a review page (`post_v1.md`) for each post into
the posts folder. The review page holds every caption in full.

`post_v1.json` is always a fresh copy of the plan, rewritten on every run until something is agreed. Never edit it. A
change the person asks for, or an agreed time, goes in the next version (`post_v2.json`). From then on that version is
kept, and the command warns if the plan's captions no longer match it.

## /post-setup: first time on a computer

Follow `references/SETUP.md` one step at a time. It saves the posting plan link, connects Blotato, records which
Blotato account is which, and finds the synced handover folder. Finish with `setup.py show`. Until it says
"Set-up complete.", the other commands can show posts but must not schedule anything, and `plan.py` says so at the top.

## /post-next: the next post

1. Run `plan.py next`. It names the next post that is due and not yet logged, and lists any dates that have passed.
2. Read its State:
   - `DUE`: carry on.
   - `PART DONE`: some accounts are already logged. Only the others are left.
   - `DATE PASSED`: stop and ask the person for a new date.
   - A file marked `MISSING`: the handover folder has not finished syncing. Ask the person to check, then stop.
   - Any `BLOCK` line: stop and show it. Do not post around a block.
3. Open the review page and show the person, in the chat: the "to confirm" notes first, then each switched-on
   account's caption in full, the media file, and the proposed time in local time and in UTC. Leave out the accounts
   the page marks SWITCHED OFF, and say which ones you left out. Pass on every `WARN` line in plain words.
4. Ask one question: "Shall I schedule these for <day and date> at <time> <time zone>, or change anything first?"
   Then stop and wait.
5. The release clock (full rules in `references/BLOTATO.md`):
   - Schedule only once the person has agreed a date and a time. That means a yes to your question in step 4, for
     this post, sent after you showed its captions. A yes given earlier, for example in a set-up message or for
     another post, never counts.
   - "Looks good" or "approved" with no time approves the words only. Ask when it should go live, then stop.
   - Post now only when the person says "now", "post it now" or "immediately".
6. Save the agreed release as the next version of the post file (`post_v2.json` with `release` set to
   `{"mode": "scheduled", "local": "<YYYY-MM-DD HH:MM>", "timezone": "<zone>", "scheduledTime": "<UTC>"}`, from
   `plan.py when`). Run `check_post.py` on it. It must show no BLOCK.
7. If `plan.py` says the set-up is not complete, stop here and say what is missing. Otherwise push it through Blotato
   as `references/BLOTATO.md` says: check Blotato's post list for that day first, upload each
   media file once, make one `blotato_create_post` call per switched-on account, and log each result with
   `posting_log.py add` as soon as the call returns.
8. Confirm each scheduled post with `blotato_get_post_status` or `blotato_list_schedules`. Reply with a short table:
   account, state, time. Scheduled, published and failed are different states. Never call a scheduled post "posted".

## /post-week: the whole week

1. Run `plan.py week` (this week, Monday to Sunday), or `plan.py week --date <date>` for another week.
2. Show the person a table of the week first: day, content, state, and how many notes need confirming.
3. Then go through the posts one at a time, exactly as in /post-next steps 2 to 4. One post, one question, one answer.
   A yes for Monday is not a yes for Tuesday.
4. When every post has its answer, schedule the approved ones as in /post-next steps 6 to 8, and report the week in one
   table. List the posts that are waiting on an answer separately.

## /post-status: what went out

1. Run `plan.py status`.
2. Call `blotato_list_posts` for the same dates and compare. Blotato's list is the truth. Update the log where they
   differ (`posting_log.py add` or `update`).
3. Report: what is scheduled, what is published (with links), what failed and why, any date that passed with nothing
   posted, and any double post.

## Changing or cancelling

Only when the person asks. Find the post with `blotato_list_schedules`, then use `blotato_update_schedule` or
`blotato_delete_schedule`, and log the change. Never delete or hide a live post unless the person asks in so many words.

## Never

- Post or schedule before a person has agreed the date and time.
- Post content that is not in the posting plan with this skill. New content needs its captions written and added to the plan first.
- Post to an account that is switched off in the settings.
- Put a key, a password or an account id in a chat, a post file or this skill's folder.
- Set up comment-to-message automations or reply to comments unless the person asks for that as its own job.
