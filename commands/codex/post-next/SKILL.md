---
name: post-next
description: Show the next post in the plan and its captions, then wait for a yes and a time. Use when the person types $post-next or /post-next.
---
<!-- post-desk command. Installed by install.py. Edit the copy in the repo, not this file. -->

Do the next post. Follow the section "/post-next: the next post" of the post-desk skill exactly.

Show the "to confirm" notes and every switched-on account's caption in full, with the proposed date and time. Then ask one question and stop. Schedule nothing until the person has agreed the date and the time.

If a date or the name of a piece of content is given below, use `plan.py day --date <date>` for that date in place of `plan.py next`.

The skill is at `~/.agents/skills/post-desk/SKILL.md`. Read it first.
