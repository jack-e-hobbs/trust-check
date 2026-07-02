# Codex CLI setup

No skill/extension concept — this is manual or hook-driven only.

Assumes you've done the clone + symlink step from the main README (gives a stable path to the script even though this tool won't auto-discover it as a skill).

**Manual:**

```
python3 ~/.claude/skills/trust-check/scan_connections.py diff --project "$(pwd)"
```

Paste the output to Codex and ask it to score anything in `new`/`changed` against
`~/.claude/skills/trust-check/RISK-RUBRIC.md`.

**Optional: nudge on every new session**

Codex CLI supports a `hooks.json` with an explicit `SessionStart` event (JSON over
stdin/stdout). Point it at the same `diff` command; if `new`/`changed` are non-empty,
have the hook emit a message for Codex to relay to you at session start.
