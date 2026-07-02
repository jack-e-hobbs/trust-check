# Gemini CLI setup

No native skill concept — extensions are the closest equivalent. Assumes you've done
the clone + symlink step from the main README (gives a stable path to the script even
though this tool won't auto-discover it as a skill).

**Manual:**

```
python3 ~/.claude/skills/trust-check/scan_connections.py diff --project "$(pwd)"
```

Paste the output to Gemini CLI and ask it to score anything in `new`/`changed` against
`~/.claude/skills/trust-check/RISK-RUBRIC.md`.

**Optional: nudge on every new session**

Package the scan as a Gemini CLI extension with a `hooks/hooks.json` lifecycle hook
that runs the `diff` command on session start and surfaces a message if `new`/
`changed` are non-empty.
