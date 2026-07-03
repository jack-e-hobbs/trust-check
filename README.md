# Trust Check

You just found a slick new MCP server or connector on Twitter/Reddit/a blog post. It
promises to save you hours. Should you connect it?

**Trust Check answers that in plain English.** No security background needed. It also
watches the connections you already trust, so if one of them quietly changes what it
does weeks after you approved it (the "rug pull," a real, documented attack against
AI tools), you find out instead of finding out the hard way.

## What it tells you

You get a one-line verdict per connection first, not a wall of text:

```
🟢/🟡/🔴 <name>: what it does, the one thing to know if anything
```

Ask for more on anything that catches your eye and you get the full picture: what it
does, every external website/domain it talks to, the main risks in plain comparisons
(not technical terms), and 2–3 concrete next steps.

**Example**: asking `audit-skill-file` to check a skill someone found on social media:

```
🔴 helpful-summarizer.md: summarizes text, but sends your full conversation to an
   unfamiliar domain and tells the AI not to mention it to you
```

Ask "tell me more" and you'd get the full breakdown: the exact URL it POSTs to, the
exact phrase telling the AI to hide it from you, and next steps (don't install it,
here's who to report it to).

## Why it also checks tools you already approved

Most security advice stops at "vet it before you connect it." That misses the actual
attack: a tool can look clean on day one and be swapped out later, once enough people
depend on it. Trust Check keeps a fingerprint of every connection you've approved and
flags the moment one of them changes, before you find out the hard way.

## Works across your tools

Checks Claude Code, OpenCode, Codex CLI, Gemini CLI, and Cursor CLI, whichever you
actually have installed. One check covers all of them.

| Tool | Runs automatically? |
|---|---|
| Claude Code | Yes, ask it any time |
| OpenCode | Yes, ask it any time |
| Codex CLI | Manual, or wire up a startup hook (see `setup/codex.md`) |
| Gemini CLI | Manual, or wire up a startup hook (see `setup/gemini.md`) |
| Cursor CLI | Manual only, the CLI doesn't support a startup hook yet |

Setup steps for each tool are in `setup/<tool>.md`.

## Requirements

Python 3.11+ (for `tomllib`, used to read Codex CLI's TOML config). Everything else is
standard library, no dependencies to install.

## Install (Claude Code / OpenCode)

```
git clone https://github.com/jack-e-hobbs/trust-check.git
ln -s "$(pwd)/trust-check" ~/.claude/skills/trust-check
ln -s "$(pwd)/trust-check/audit-skill-file" ~/.claude/skills/audit-skill-file
```

Both Claude Code and OpenCode discover skills from `~/.claude/skills/` automatically.
Nothing else to configure. Everything else in this repo (the setup docs, hooks) refers
back to these two fixed paths, so it doesn't matter where you cloned the repo itself.

## Use it

Just ask: **"run a trust check"** or **"is this new connection safe?"**

## ⚠️ Read this before you rely on it

**This tool is a second opinion, not a guarantee.** It can only see what a connection
tells the truth about. It cannot see inside a remote server's actual code, and a
determined attacker can lie in ways this won't catch. A 🟢 rating means nothing obvious
was found, not that the tool is certified safe.

**This is not legal, compliance, or professional security advice**, and using it does
not transfer any liability for a bad outcome away from you or your organisation. If
you're handling regulated data (health records, financial data, personal information
covered by privacy law) or you're genuinely unsure about a connection, **talk to your
IT team, a security professional, or your legal/compliance team** before proceeding.
When in doubt, don't connect it. Ask a human first.

## Got a skill file, not a connection?

If someone hands you a `SKILL.md`, custom command, or any other prompt/instruction
file to install (especially one from social media rather than an official source), use
the sibling **`audit-skill-file`** skill instead, it reads the file itself for
embedded URLs and hidden AI-directed instructions, and tracks it the same way for
later drift. Ask: **"check this skill file before I install it."**

## Contributing

Not actively maintained as an open project right now, no promised response time on
issues or PRs. Feel free to fork it if you want to extend it (e.g. more CLI adapters,
a real skill-file URL-safety database).

## License

[MIT](LICENSE).
