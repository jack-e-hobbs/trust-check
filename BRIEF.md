# Trust Check — design brief

Supersedes the original `usability-brief.md` (deleted — its intent is fully captured
here plus the decisions made building it out).

## Role & objective

A friendly, non-technical security check for AI tool connections. Helps a regular
business user — not a security analyst — decide whether a new or existing MCP
server/connector/plugin is safe to keep connected to their CLI AI agent. Explains
technical risk in plain language and real-world analogies, never jargon.

## Trigger

Whenever a user asks to check, audit, or review a connection, or after they add a new
MCP server/connector/plugin and want a read on it before trusting it.

## What's audited

Two entry points, sharing `RISK-RUBRIC.md`:

- **`trust-check`** — MCP servers, connectors, plugins: anything with a config entry
  that can be fingerprinted (see `scan_connections.py` adapters for Claude Code,
  OpenCode, Codex CLI, Gemini CLI, Cursor CLI).
- **`audit-skill-file`** — the raw content of a skill/prompt file (e.g. a `SKILL.md`
  pasted from social media, which has no config to diff). Heavier — it means reading
  prose for embedded URLs and injection language rather than diffing a config — so it's
  a separate skill invoked only when a specific file is in question, not a blanket
  sweep. `scan_skill_file.py` fingerprints the file's raw text and regex-extracts
  candidate URLs and a crude injection-phrase hit-list; the actual judgement still
  requires the agent to read the full file.

Both write into the same baseline (`~/.config/trust-check/baseline.json`), so a skill
file that's already been approved and later edited on disk shows up as drift exactly
like a changed MCP connection does.

## Audit protocol

Four scored factors (`RISK-RUBRIC.md`), 0–100, higher = riskier:

- **A. Source trust** — is this from a known vendor, or an unfamiliar GitHub repo worth
  checking for account age / stars / contributors?
- **B. Network exposure** — what external URLs does this touch, and do they match what
  the tool claims to be? **Every external URL found gets named explicitly in the
  report** — this was flagged as the single highest-priority thing to surface, since a
  non-technical user copy-pasting a tool from social media is exactly the scenario
  where an unexpected external endpoint is the tell.
- **C. Permission scope** — read-only vs. write/delete/execute, credentials requested
  as parameters, scope broader than the stated purpose.
- **D. Prompt-injection red flags** — description text containing directives aimed at
  the AI rather than documentation for it. A hit here overrides the arithmetic total
  straight to Critical.

Sensitive data (personal/medical/financial info) is **not a fifth scored factor** — it
mostly overlaps with B and C, so scoring it separately double-counts the same signal.
Instead it's a **named callout only when genuinely present**: the report states
specifically what kind of sensitive data is in scope, without padding every report
with a boilerplate warning that doesn't apply.

## Rug-pull / drift detection

Beyond a point-in-time audit, every connection gets fingerprinted and saved to a
shared baseline (`~/.config/trust-check/baseline.json`). Each run diffs current state
against that baseline — a connection that was already approved and now has a different
fingerprint (different URL, command, or scope) is flagged as changed, ranked above
brand-new connections, and never silently re-approved into the baseline without the
user seeing what changed. This is the direct defence against a tool being swapped out
weeks after mass adoption.

## Output format

Internal score/bucket (0–100, Low/Medium/High/Critical) drives the baseline and
tracks whether a connection gets riskier over time — never shown to the user raw.
User-facing report always uses:

- 🟢 Safe to use / 🟡 Use with caution / 🔴 Do not use
- One-sentence plain-English description of what the tool does
- Every external URL/domain, named explicitly
- Risk bullets using real-world analogies, including the sensitive-data callout if it
  applies
- 2–3 concrete next steps — for 🟡/🔴 always a clear action; a data-hygiene reminder
  only when sensitive data was genuinely found in scope

## Explicit limitations (must be visible to the user, not buried)

- Only sees what a connection *declares* — cannot see inside a remote server's actual
  code or catch a lie in its declaration.
- Not a guarantee of a clean server, and not legal/compliance/security advice. See
  `README.md`'s disclaimer — repeat its substance whenever a user seems to be treating
  this as their only check, especially around regulated data.
