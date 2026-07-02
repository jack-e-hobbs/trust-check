# Claude Code setup

**Skill (manual audits):**

Install per the main `README.md` (clone + symlink into `~/.claude/skills/trust-check`).
Claude Code discovers skills under `~/.claude/skills/<name>/SKILL.md` automatically —
nothing else to configure. Ask "run a trust check" any time.

**Optional: nudge on every new session**

Add a `SessionStart` hook to `~/.claude/settings.json` (use the `update-config` skill
rather than hand-editing) that runs:

```
python3 ~/.claude/skills/trust-check/scan_connections.py diff --project "$CLAUDE_PROJECT_DIR"
```

If the output's `new` or `changed` arrays are non-empty, have the hook print a short
note to stdout — Claude Code feeds hook stdout into context at session start, so it'll
surface as "N new/changed connections since last audit, want me to check them?"
without you needing to remember to ask.
