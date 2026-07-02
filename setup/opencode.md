# OpenCode setup

**Skill (manual audits):**

Nothing to install if you've already symlinked it for Claude Code — OpenCode reads
`~/.claude/skills/<name>/SKILL.md` directly (documented Claude-compatible path). If
you only use OpenCode, symlink it under OpenCode's own skill path instead (see the main
`README.md` for the clone step):

```
ln -s "$(pwd)/trust-check" ~/.config/opencode/skills/trust-check
```

Ask "audit my connections" any time.

**Optional: nudge on every new session**

OpenCode has a real plugin system with lifecycle hooks. Add a plugin under
`~/.config/opencode/plugins/` (or `.opencode/plugins/` for project-scoped) that hooks
`session.created` and shells out to:

```
python3 ~/.claude/skills/trust-check/scan_connections.py diff --project "$PWD"
```

If `new`/`changed` are non-empty, have the plugin post a message into the session so
the agent surfaces it unprompted.
