# Posting through Blotato

Blotato's tools reach live audiences, so every call that creates, changes or deletes a post happens only after a person
has approved the captions and agreed the release time. Tool names and fields can change, so read each tool's
description before the first call of a session.

## The release clock

| Level | What is allowed |
|---|---|
| 0 Draft | Writing and checking captions. No Blotato calls except reading accounts, posts and schedules |
| 1 Ready | Captions approved. Still no upload and no post |
| 2 Scheduled | The person has agreed a date and time. Upload, schedule, verify |
| 3 Live | The person said "post now", "post it now" or "immediately". Upload, post, verify |

- Approval words ("looks good", "approved", "go ahead", "ready", "do it") stay at Ready until there is a time. Ask:
  "When should this go live? Give me the date and time, or say post now." Then stop.
- Never guess a time, never pick "the next free slot", and never use `useNextFreeSlot`.
- Turn the agreed time into UTC with `plan.py when --date <date> [--time HH:MM]` and say both back. A morning time in
  Australia is the evening before in UTC. If `in_the_past` is true, stop and ask for a new date.
- One agreed time applies to every account in the post, unless the person gives a different time for one.
- If the person says to leave a post that went out by mistake, leave it. Do not delete, hide or move it.

## Before the first call

1. `blotato_list_accounts`, to confirm each `accountId` and `pageId` in settings still exists and is the right account.
2. `blotato_list_posts` for that day, and `posting_log.py list`, to make sure nothing is already scheduled or live there.
3. `check_post.py` on the final `post_vN.json` shows no BLOCK, and the release in the file matches what was agreed.

## Uploading media

Blotato needs a public address for every image or video. For each local file, once per post:
1. `blotato_create_presigned_upload_url` with the file name. It returns `presignedUrl` and `publicUrl`.
2. `python3 scripts/put_file.py "<presignedUrl>" "<full path to the file>"` (Windows: `python scripts\put_file.py ...`).
   It prints OK when the upload is done. A long video can take a few minutes. Use this script rather
   than a plain curl upload: Blotato's storage serves a file with whatever type the upload declared, and a plain curl
   upload declares none, so the platforms can refuse the file. The script sends the real type (video/mp4, image/png).
3. Use the `publicUrl` in `mediaUrls` for every account in the post. Do not upload the same file again for each account.

For a carousel, upload each PNG slide in order and pass the public addresses in slide order.

## One call per account

`blotato_create_post` with `accountId`, `platform`, `text` and `mediaUrls`, plus `scheduledTime` (UTC, for example
`2026-11-15T20:00:00Z`) when scheduled. Leave `scheduledTime` out only for "post now". `accountId` and `pageId` come from
the settings file. Any `fields` in the post file go in as they are. Then the platform's own fields:

| Account | platform | Extra fields |
|---|---|---|
| A person's LinkedIn profile | `linkedin` | none. No `pageId`, so it posts to the profile |
| A LinkedIn company page | `linkedin` | `pageId` from settings |
| Instagram | `instagram` | video: `mediaType: "reel"`, `shareToFeed: true`. Cover: `coverImageUrl` (upload the cover first) |
| A Facebook page | `facebook` | `pageId` from settings (required). Clips under a minute: `mediaType: "reel"` |
| X | `twitter` | none |
| Threads | `threads` | none |
| YouTube | `youtube` | `title`, `privacyStatus`, `shouldNotifySubscribers` (all required). Optional `thumbnailUrl` |

LinkedIn's company page "repost" is not a Blotato action. The page gets its own post with its own caption.

## Carousels

- Instagram: the PNG slides as several `mediaUrls` make an Instagram carousel. Animated MP4 slides in a carousel have not
  been tested through Blotato. Try once with the person watching, and if it fails, post the animated version by hand.
- LinkedIn: the PNG slides as several `mediaUrls` make a multi-image post. The PDF "document" carousel (the swipeable
  version) is not offered by Blotato's tool, so for that, upload the PDF in LinkedIn by hand and log it as `posted-by-hand`.
- Facebook: several images make a multi-image post.

## After each call

- Log it straight away: `posting_log.py add --date <post date> --account <account key> --platform <platform> --submission
  <postSubmissionId> --state scheduled --scheduled <UTC time> --pack "<post file>"`.
- "Post now" calls wait up to 20 seconds. If the result is still in progress, wait at least 10 seconds and call
  `blotato_get_post_status` with the `postSubmissionId`. When it says published, log the `publicUrl` with
  `posting_log.py update`.
- Scheduled calls return the resolved `scheduledTime`. Check it matches the agreed time.

## When something fails

- Read the `errorMessage`. Blotato says most failures are permanent, so sending the same thing again rarely helps.
- Common causes: an expired platform connection (reconnect the account in Blotato), a wrong `pageId`, a video the
  platform will not take, or a caption over the limit.
- Fix the cause, tell the person what happened in one line, and ask before sending it again. Log the failure as `failed`.
- If a call times out, check `blotato_list_posts` and `blotato_list_schedules` before trying again, because the first
  call may have worked.

## Changing or cancelling a scheduled post

Only when the person asks. Find it with `blotato_list_schedules`, then use `blotato_update_schedule` (new text or
time) or `blotato_delete_schedule`. Read it back afterwards, and log it with `posting_log.py update`.

## Checking what went out

`blotato_list_posts` with `since` and `until` returns each post as scheduled, published (with `postUrl` and figures) or
failed (with `errorMessage`). Compare it with the log and the posting plan, then update the log.

## Leave alone unless asked

Blotato can also reply to comments, send direct messages and run comment-to-DM automations. None of that is part of this
skill's normal job. Do it only when the person asks for it as its own task, and never set up an automation that promises a
link or a file without checking the link works.
