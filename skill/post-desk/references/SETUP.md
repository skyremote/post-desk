# First-time set-up

Do this once per computer, one step at a time. Ask one question at a time and wait for the answer. It takes about
20 minutes, most of it connecting accounts inside Blotato.

Decide first which one computer does the scheduling. The posting log lives on that computer.

## 1. Check Python

Run `python3 --version` (Mac) or `python --version` (Windows). Python 3.8 or later is needed. On a Mac, the first use
may offer to install Apple's developer tools: say yes and let it finish. On Windows, install it from python.org and
tick "Add python.exe to PATH".

## 2. Save the posting plan link

The person has a link to the posting plan (a Google Sheet). Run:

`setup.py init --sheet "<the link>"`

It downloads the plan and reads the brand, the time zone, the posting time, the link every post points to, the list of
accounts and the house rules. If the download fails, the sheet is not shared as "anyone with the link can view".

If an older posting skill was set up on this computer, bring its account ids and folders across in the same step:

`setup.py init --sheet "<the link>" --import-old "<path to the older settings.json>"`

## 3. Connect the accounts inside Blotato

The person signs in to their own Blotato account at blotato.com. Under Accounts, they connect each account in the list
that `setup.py show` prints. A LinkedIn company page appears under the LinkedIn connection of a person who is an admin
of that page. An Instagram account must be a professional (business or creator) account. Blotato always posts to a
Facebook page, never to a personal Facebook profile.

## 4. Connect Blotato to this agent

Never paste the key into the chat, only into the terminal command below.

**Claude Code, with an API key.**
1. In Blotato, open Settings, then API, and copy the API key. If it ends with one or more `=` signs, copy those too.
2. In a terminal, run this, with the key in place of `YOUR_KEY`:
   `claude mcp add --transport http --scope user blotato https://mcp.blotato.com/mcp --header "blotato-api-key: YOUR_KEY"`
3. Quit and reopen Claude Code.

**Claude Code, by signing in through the browser.**
1. Run `claude mcp add --transport http --scope user blotato https://mcp.blotato.com/mcp`
2. In Claude Code, type `/mcp`, choose blotato, then Authenticate, and approve it in the browser.

**Codex.** Add Blotato as an MCP server in `~/.codex/config.toml`, with the address `https://mcp.blotato.com/mcp`, and
keep the key in an environment variable, not in the file.

Check it worked: call `blotato_get_user`, then `blotato_list_accounts`. If the tools are missing in Claude Code, run
`claude mcp list` in the terminal and check blotato shows as connected.

## 5. Record which account is which

Call `blotato_list_accounts` and show the person the list in plain words: platform, name and username. Ask which is
which, then record each one with its key from `setup.py show`:

- `setup.py account <key> --id <accountId>`
- For a LinkedIn company page or a Facebook page: `setup.py account <key> --id <accountId> --page <the page id from subaccounts>`
- Add `--on` or `--off` to switch an account on or off.

The account ids belong only in the settings file. They never go into a post file or the chat summary.

## 6. Find the handover folder

The media files arrive as a shared Google Drive folder. To use it here:
1. Install Google Drive for desktop and sign in.
2. In Drive in the browser, open "Shared with me", right-click the handover folder, choose Organise, then Add shortcut,
   then My Drive.
3. In Google Drive for desktop, make that folder available offline, so the videos are on the computer.
4. Run `setup.py find-folder --save`. If it finds nothing, ask the person where the folder is and run
   `setup.py set handover_folder "<full path>"`.

## 7. Test it without posting

1. `setup.py show`. Expect "Set-up complete."
2. `plan.py next`. Expect the next post, every file marked OK, and no BLOCK line.
3. Open the review page it names and show the person the captions. Do not schedule anything in the set-up.

Then tell the person it is ready, and give them the three commands: `/post-next`, `/post-week` and `/post-status`.
In Codex they are `$post-next`, `$post-week` and `$post-status`.
