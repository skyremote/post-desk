# The posting plan sheet

One Google Sheet, shared as "anyone with the link can view". The skill downloads it as a spreadsheet file each time it
runs and falls back to the last copy if the internet is down. Only the owner of the sheet can change it, so the
captions that get posted are the ones the owner wrote.

Tab names and column headings must match the ones below. Extra columns are ignored, so the sheet can also carry columns
that only people read.

## Tab: Captions (needed)

One row per post and account.

| Column | What it holds |
|---|---|
| Post date | The proposed date, as `2026-11-16`. Rows with no date are ignored |
| Content | The name people use for the clip, carousel or photo |
| Format | Video, Carousel or Photo |
| Type | Free text, for example Teach or Proof |
| Account key | The account's key from the Accounts tab |
| Platform | linkedin, instagram, facebook, twitter, threads, youtube, tiktok or bluesky |
| Caption | The caption, exactly as it should post, with blank lines between paragraphs |
| Title (YouTube only) | The video title |
| Other opening 1, Other opening 2 | Spare first lines for a person to choose from |
| Content key | A short name with no spaces. Rows with the same date and key make one post |
| Media type | video, carousel or photo |
| Files | The media files, one per line, as paths inside the handover folder. Carousel slides in order |
| Caption file | The clip's `.srt` file, as a path inside the handover folder. Figures in a caption are checked against it |
| Extra fields | JSON for the platform's own fields, for example `{"mediaType": "reel", "shareToFeed": true}` |

## Tab: Content and notes (optional)

One row per piece of content. The skill reads two columns: `Content key`, and the column whose heading starts with
"To confirm". Each line in that cell is one thing the owner must confirm before the post goes out.

## Tab: Settings (needed)

Two columns, `Key` and `Value`.

| Key | Example | What it is |
|---|---|---|
| brand | Acme | The name in messages |
| timezone | Australia/Sydney | Dates and times in the plan are in this time zone |
| posting_time | 07:00 | The proposed time of day for every post |
| link | https://example.com/start | Every post should point here |
| web_address | example.com | The address as written in captions |
| wrong_web_addresses | example.app, example.net | Addresses that must not appear in a caption |
| handover_markers | 06 Social Videos\|04 Launch Trailer | Folders inside the handover folder, used to find it |
| posts_folder | ~/Documents/Social Posts | Where drafts and the posting log go on each computer |
| no_emojis | TRUE | Block any caption with an emoji |
| linkedin_hashtags | FALSE | FALSE warns when a LinkedIn caption has hashtags |

## Tab: Accounts (needed)

| Column | What it holds |
|---|---|
| Account key | A short name with no spaces, used in the Captions tab and the settings file |
| Platform | As in the Captions tab |
| Name | The name shown to people |
| On by default | TRUE or FALSE. A person can switch an account on or off on their own computer later |
| Needs a page id | TRUE for a LinkedIn company page or a Facebook page |

## Tab: Rules (optional)

The house rules, checked on every caption.

| Column | What it holds |
|---|---|
| Level | BLOCK (must be fixed) or WARN (a person looks and decides) |
| Pattern | A regular expression, matched without regard to capitals |
| Message | What to tell the person when it matches |

The platform limits (characters, hashtags, a YouTube title) are built into the skill and need no rule.
