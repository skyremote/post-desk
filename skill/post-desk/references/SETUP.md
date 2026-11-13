# First-time set-up

Do this once per computer, one step at a time. Ask one question at a time and wait for the answer. It takes about
20 minutes, most of it connecting accounts inside Blotato.

Decide first which one computer does the scheduling. The posting log lives on that computer.

**How to run the commands below.** Every script sits in this skill's `scripts` folder. Write the full path each time,
for example `python3 "<this skill's folder>/scripts/setup.py" show` on a Mac, or `python "<this skill's
folder>\scripts\setup.py" show` on Windows. Use the installed copy of the skill (`~/.claude/skills/post-desk`, or
`~/.agents/skills/post-desk` in Codex), not the downloaded folder.

**If the agent has to be restarted part-way,** type `/post-setup` again afterwards. `setup.py show` lists what is still
missing, so carry on from the first missing thing. Running `setup.py init` twice is safe.

## 1. Check Python

Run `python3 --version` (Mac) or `python --version` (Windows). Python 3.8 or later is needed. On a Mac, the first use
may offer to install Apple's developer tools: say yes and let it finish. On Windows, install it from python.org and
tick "Add python.exe to PATH".

## 2. Save the posting plan link

The person has a link to the posting plan (a Google Sheet). Run:

`setup.py init --sheet "<the link>"` (the `--sheet` flag is needed)

It downloads the plan and reads the brand, the time zone, the posting time, the link every post points to, the list of
accounts and the house rules. If the download fails, the sheet is not shared as "anyone with the link can view".

If an older posting skill was set up on this computer, bring its account ids and folders across in the same step:

`setup.py init --sheet "<the link>" --import-old "<path to the older settings.json>"`

## 3. Connect the accounts inside Blotato

This step is for the person to do in their browser. Ask, then wait. The person signs in to their own Blotato account at
blotato.com. Under Accounts, they connect each account that `setup.py show` marks `ON`. The accounts marked `off` can
wait until the person wants them. A LinkedIn company page appears under the LinkedIn connection of a person who is an admin
of that page. An Instagram account must be a professional (business or creator) account. Blotato always posts to a
Facebook page, never to a personal Facebook profile.

## 4. Connect Blotato to this agent

Never paste the key into the chat, only into the terminal command below. Use the API key way unless the person
prefers to sign in through the browser.

**Claude Code, with an API key.**
1. In Blotato, open Settings, then API, and copy the API key. If it ends with one or more `=` signs, copy those too.
2. In a terminal, run this, with the key in place of `YOUR_KEY`:
   `claude mcp add --transport http --scope user blotato https://mcp.blotato.com/mcp --header "blotato-api-key: YOUR_KEY"`
3. Quit and reopen Claude Code, then type `/post-setup` again to carry on.

**Claude Code, by signing in through the browser.**
1. Run `claude mcp add --transport http --scope user blotato https://mcp.blotato.com/mcp`
2. In Claude Code, type `/mcp`, choose blotato, then Authenticate, and approve it in the browser.

**Codex.** Add Blotato as an MCP server in `~/.codex/config.toml`, with the address `https://mcp.blotato.com/mcp`, and
keep the key in an environment variable, not in the file.

Check it worked: call Blotato's `blotato_get_user` tool, then `blotato_list_accounts`. In Claude Code the tool names
carry a prefix, for example `mcp__blotato__blotato_list_accounts`. If the tools are missing, run `claude mcp list` in
the terminal and check blotato shows as connected.

## 5. Record which account is which

Call `blotato_list_accounts` and show the person the list in plain words: platform, name and username. Ask which is
which, then record each one with its key from `setup.py show`:

- `setup.py account <key> --id <accountId>`
- For a LinkedIn company page or a Facebook page: `setup.py account <key> --id <accountId> --page <page id>`. The page
  id is in the list of pages ("subaccounts") that Blotato returns under that account. A LinkedIn company page uses the
  same `accountId` as the LinkedIn connection of the person who runs it, plus the page id.
- Add `--on` or `--off` to switch an account on or off.

The account ids belong only in the settings file. Do not print them in a reply, and never put them in a post file.

## 6. Find the handover folder

The media files arrive as a shared Google Drive folder. Run `setup.py find-folder --save` first. If it finds the folder,
this step is done. If not, steps 1 to 3 are for the person to do: ask, then wait.
1. Install Google Drive for desktop and sign in.
2. In Drive in the browser, open "Shared with me", right-click the handover folder, choose Organise, then Add shortcut,
   then My Drive.
3. In Google Drive for desktop, make that folder available offline, so the videos are on the computer.
4. Run `setup.py find-folder --save` again. If it still finds nothing, ask the person where the folder is and run
   `setup.py set handover_folder "<full path>"`.

## 7. Test it without posting

1. `setup.py show`. Expect "Set-up complete."
2. `plan.py next`. Expect the next post, every file marked OK, and no BLOCK line.
3. Open the review page it names and show the person the captions of the switched-on accounts. Do not schedule
   anything in the set-up, and do not ask the scheduling question here. That belongs to `/post-next`.

Then tell the person it is ready, and give them the three commands: `/post-next`, `/post-week` and `/post-status`.
In Codex they are `$post-next`, `$post-week` and `$post-status`.
