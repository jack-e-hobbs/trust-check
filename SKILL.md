---
name: trust-check
description: Audit every MCP server, connector, and plugin the current CLI agent is wired to — fingerprint each one, diff against the last approved baseline, and run a plain-English trust check on anything new or changed. Use when the user says "audit my connections", "is this tool/MCP safe", "check this new connector", "run a safety check on X", or after they've added a new MCP server/skill/plugin and want a trustworthiness read before trusting it. Built for non-technical users who could be duped into approving a malicious or later-swapped external tool.
---

# Trust Check

Defends against two real threats: (1) a user approves a shiny new MCP server or
connector that's malicious or overreaching from day one, and (2) a tool they already
trust gets its remote definition silently swapped weeks after approval (the "rug
pull"). Neither is hypothetical — it's a documented MCP attack pattern.

**Hard limit, say this if asked:** this only sees what a server *declares* (its tool
names, descriptions, schemas, and its config on disk). A malicious remote server can
lie in its declaration or change server-side behaviour without changing anything
visible locally. This catches drift, overreach, and sloppy/obvious attacks — it is not
a guarantee of a clean server, and it is not legal or professional security advice
(see README's disclaimer — repeat its substance if the user seems to be relying on
this as their only check).

**Multi-tool:** the scan script auto-detects config for Claude Code, OpenCode, Codex
CLI, Gemini CLI, and Cursor CLI, and scans whichever are actually installed on this
machine. Findings from all of them are reported together with which tool each
connection belongs to.

## Step 1 — scan

```
python3 <this skill's directory>/scan_connections.py diff --project "$(pwd)"
```

Returns `{new, changed, unchanged, removed}`. Disk-only — no network calls.

`changed` is the highest-priority signal: a connection that was already approved has a
different fingerprint now (different URL, command, args, or env keys). Lead the report
with these, explicitly labelled "previously approved, now different" — do not treat
them like ordinary new-tool scoring, and do not silently fold them into the new
baseline without telling the user what changed.

## Step 2 — pull full tool detail for anything new or changed

For an MCP server surfaced through the current session's tools, use `ToolSearch` with
`select:mcp__<server_name>__*` (or a keyword match) to load the live tool
schemas/descriptions. Compare that against what the connection claims to do. If the
connection belongs to a different tool than the one currently running (e.g. auditing
Codex's config from inside Claude Code), score from the config + a web lookup of the
server's source instead — you won't have live schemas for it.

**Call out every external URL by name.** Any domain the connection talks to — the
server's own endpoint, or any URL a tool's parameters/description reference — gets
named explicitly in the report, not folded silently into a score. This is the single
most important thing a non-technical user should see: exactly where their data could
go, in plain terms, before they decide anything else.

## Step 3 — score every `new` and `changed` connection

Read `RISK-RUBRIC.md` in this same directory and apply it. Compute all four scored
factors (A source trust, B network exposure, C permission scope, D prompt-injection
red flags); factor D can override the arithmetic total straight to Critical.

Separately — not scored, just noted — check whether the connection's scope genuinely
touches sensitive data (personal info, medical/health records, financial/payment
data). If it does, name the specific data types in the report. If it doesn't, say
nothing about this — don't pad every report with a boilerplate data-hygiene warning
that doesn't apply.

## Step 4 — write back the baseline

Build a JSON object keyed by connection `id` (from Step 1) with `{risk_score,
risk_bucket, notes}` for every `new`/`changed` entry, then:

```
echo '<that json>' | python3 <this skill's directory>/scan_connections.py commit --project "$(pwd)" --today <YYYY-MM-DD>
```

This updates the shared baseline (`~/.config/trust-check/baseline.json`) for *all*
current connections across all tools (refreshing `last_checked`), recording a score
only for what was actually assessed. Never silently overwrite a `changed` entry's
baseline without first surfacing the diff to the user — the whole point is they see
the rug-pull, not that it gets quietly re-approved.

## Step 5 — report

Two tiers. Default to the summary — most users just want the verdict. Never dump the
full breakdown unprompted.

**Summary (always shown first):** one line per connection, ranked worst-first
(changed/drifted first, then new by severity, then a single line for "everything else
looks unchanged"):

```
🟢/🟡/🔴 <name> — <what it does, ~6 words> [— <the one biggest reason, only if 🟡/🔴>]
```

Example:
```
🔴 acme-crm-sync — reads your CRM data — sends it to an unfamiliar domain
🟡 weather-widget — fetches forecasts — asks for more file access than it needs
🟢 clickup — task management, official ClickUp endpoint
Everything else (6 connections) — unchanged since last check.
```

Close with one line offering more: *"Want the full breakdown on any of these — what
data it touches, the exact URLs, next steps? Just ask."*

**Full breakdown (only on request — "tell me more," "what about X," "give me details"):**
For the specific connection(s) asked about, give:

- **Trust rating:** 🟢/🟡/🔴, same mapping (Low→🟢, Medium→🟡, High or Critical→🔴).
- **What this tool does:** one plain-English sentence.
- **Where your data could go:** every external URL/domain involved, named explicitly.
- **The main risks:** short bullets in real-world analogies ("this is like handing a
  stranger a spare key to your filing cabinet"), including the sensitive-data callout
  from Step 3 if it applies.
- **Next steps:** 2–3 concrete, non-technical actions. For anything 🟡/🔴, always
  include a clear action (question the vendor, watch it, or disconnect it). Only add a
  data-hygiene reminder ("scrub customer emails before this tool sees them") when Step
  3 found genuinely sensitive data in scope.

The internal 0–100 score/bucket is for the baseline file and tracking drift over
time — never show the raw number even in the full breakdown, unless explicitly asked.

No jargon dump either way — this is for someone who doesn't know what an MCP server
is. If the user wants something to share with a team, offer to render the full
breakdown as an Artifact rather than defaulting to it.

## Automatic checking — availability varies by tool

- **Claude Code & OpenCode:** both discover this skill natively (OpenCode reads
  `~/.claude/skills/<name>/SKILL.md` directly). Neither has a "new MCP server added"
  event, but Claude Code's `SessionStart` hook and OpenCode's `session.created` plugin
  hook can each run Step 1 automatically and nudge the user if anything's new or
  changed — see `setup/claude-code.md` / `setup/opencode.md`.
- **Codex CLI:** has a real `SessionStart` hook (`hooks.json`) — see
  `setup/codex.md`.
- **Gemini CLI:** extensions can bundle lifecycle hooks — see `setup/gemini.md`.
- **Cursor CLI:** no session-start hook exists in the CLI as of early 2026 (only in the
  IDE) — see `setup/cursor.md`. Scanning still works, just not automatically nudged.

Don't add a hook to any tool's config as a side effect of running this skill — ask the
user first (use the `update-config` skill for Claude Code's `settings.json`).

## Out of scope — skill-file content scanning

This skill only understands MCP-style connections (things with a config entry it can
fingerprint). A plain skill/prompt file (e.g. a `SKILL.md` copy-pasted from social
media) has no config to diff — auditing it means reading its actual prose for embedded
URLs and injection language, which is a different and more token-intensive job. Use the
sibling `audit-skill-file` skill for that instead of attempting a shallow version here.
