# Cursor CLI setup

No skill concept, and the CLI (unlike the IDE) has no session-start hook as of early
2026 — only `beforeShellExecution`/`afterShellExecution`. Manual only for now.

Assumes you've done the clone + symlink step from the main README (gives a stable path
to the script even though this tool won't auto-discover it as a skill).

```
python3 ~/.claude/skills/trust-check/scan_connections.py diff --project "$(pwd)"
```

Paste the output to Cursor and ask it to score anything in `new`/`changed` against
`~/.claude/skills/trust-check/RISK-RUBRIC.md`. Revisit this once Cursor adds a
session-start hook to the CLI.
