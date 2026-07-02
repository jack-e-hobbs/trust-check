#!/usr/bin/env python3
"""Enumerate MCP servers + plugins across CLI coding agents and diff against a saved
baseline. Read-only local disk scan — no network calls. Network/GitHub trust lookups
happen live, in the SKILL.md instructions, not here.

Supports: Claude Code, OpenCode, Codex CLI, Gemini CLI, Cursor CLI. Each adapter only
runs if that tool's config file actually exists — safe to run on a machine with just
one of these installed.
"""
import json, hashlib, os, sys, argparse
from pathlib import Path

try:
    import tomllib
except ImportError:
    tomllib = None  # Codex adapter degrades gracefully without it (Python <3.11)

HOME = Path.home()
BASELINE_PATH = HOME / ".config" / "trust-check" / "baseline.json"


def fingerprint(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


def read_json(path):
    return json.loads(path.read_text()) if path.exists() else {}


def mcp_record(tool, name, scope, url=None, command=None, args=None, env=None):
    if url:
        fp_input = {"type": "http", "url": url}
        source = url
    else:
        fp_input = {
            "type": "stdio",
            "command": command,
            "args": args or [],
            "env_keys": sorted((env or {}).keys()),
        }
        source = f"{command or ''} {' '.join(args or [])}".strip()
    return {
        "id": f"{tool}:{scope}:{name}",
        "kind": "mcp-server",
        "tool": tool,
        "scope": scope,
        "name": name,
        "source": source,
        "fingerprint": fingerprint(fp_input),
    }


# --- adapters -----------------------------------------------------------------

def adapt_claude_code(project_dir):
    conns = {}
    claude_json = HOME / ".claude.json"
    cfg = read_json(claude_json)

    for name, s in (cfg.get("mcpServers") or {}).items():
        r = mcp_record("claude-code", name, "user", url=s.get("url"),
                        command=s.get("command"), args=s.get("args"), env=s.get("env"))
        conns[r["id"]] = r

    proj = (cfg.get("projects") or {}).get(str(project_dir), {})
    for name, s in (proj.get("mcpServers") or {}).items():
        r = mcp_record("claude-code", name, "project", url=s.get("url"),
                        command=s.get("command"), args=s.get("args"), env=s.get("env"))
        conns[r["id"]] = r

    local_mcp = Path(project_dir) / ".mcp.json"
    for name, s in (read_json(local_mcp).get("mcpServers") or {}).items():
        r = mcp_record("claude-code", name, "repo-file", url=s.get("url"),
                        command=s.get("command"), args=s.get("args"), env=s.get("env"))
        conns[r["id"]] = r

    settings = read_json(HOME / ".claude" / "settings.json")
    for plugin_key, enabled in (settings.get("enabledPlugins") or {}).items():
        if not enabled:
            continue
        name, _, marketplace = plugin_key.partition("@")
        mp_source = (settings.get("extraKnownMarketplaces") or {}).get(marketplace, {})
        conns[f"claude-code:plugin:{plugin_key}"] = {
            "id": f"claude-code:plugin:{plugin_key}",
            "kind": "plugin",
            "tool": "claude-code",
            "scope": "user",
            "name": name,
            "source": json.dumps(mp_source.get("source", marketplace)),
            "fingerprint": fingerprint({"plugin": plugin_key, "source": mp_source}),
        }
    return conns


def adapt_opencode(project_dir):
    conns = {}
    global_cfg = read_json(HOME / ".config" / "opencode" / "opencode.json")
    for name, s in (global_cfg.get("mcp") or {}).items():
        cmd = s.get("command") or []
        r = mcp_record("opencode", name, "user", url=s.get("url"),
                        command=cmd[0] if cmd else None, args=cmd[1:] if cmd else [],
                        env=s.get("environment"))
        conns[r["id"]] = r

    for fname in ("opencode.json", "opencode.jsonc"):
        proj_cfg = read_json(Path(project_dir) / fname) if fname.endswith(".json") else {}
        for name, s in (proj_cfg.get("mcp") or {}).items():
            cmd = s.get("command") or []
            r = mcp_record("opencode", name, "project", url=s.get("url"),
                            command=cmd[0] if cmd else None, args=cmd[1:] if cmd else [],
                            env=s.get("environment"))
            conns[r["id"]] = r
    return conns


def adapt_codex(project_dir):
    conns = {}
    if not tomllib:
        return conns

    def load_toml(path):
        return tomllib.loads(path.read_text()) if path.exists() else {}

    for scope, path in (("user", HOME / ".codex" / "config.toml"),
                         ("project", Path(project_dir) / ".codex" / "config.toml")):
        cfg = load_toml(path)
        for name, s in (cfg.get("mcp_servers") or {}).items():
            r = mcp_record("codex", name, scope, url=s.get("url"),
                            command=s.get("command"), args=s.get("args"), env=s.get("env"))
            conns[r["id"]] = r
    return conns


def adapt_gemini(project_dir):
    conns = {}
    for scope, path in (("user", HOME / ".gemini" / "settings.json"),
                         ("project", Path(project_dir) / ".gemini" / "settings.json")):
        cfg = read_json(path)
        for name, s in (cfg.get("mcpServers") or {}).items():
            r = mcp_record("gemini", name, scope, url=s.get("url"),
                            command=s.get("command"), args=s.get("args"), env=s.get("env"))
            conns[r["id"]] = r
    return conns


def adapt_cursor(project_dir):
    conns = {}
    for scope, path in (("user", HOME / ".cursor" / "mcp.json"),
                         ("project", Path(project_dir) / ".cursor" / "mcp.json")):
        cfg = read_json(path)
        for name, s in (cfg.get("mcpServers") or {}).items():
            r = mcp_record("cursor", name, scope, url=s.get("url"),
                            command=s.get("command"), args=s.get("args"), env=s.get("env"))
            conns[r["id"]] = r
    return conns


ADAPTERS = {
    "claude-code": adapt_claude_code,
    "opencode": adapt_opencode,
    "codex": adapt_codex,
    "gemini": adapt_gemini,
    "cursor": adapt_cursor,
}


def load_connections(project_dir):
    conns = {}
    for adapter in ADAPTERS.values():
        conns.update(adapter(project_dir))
    return conns


def load_baseline():
    return read_json(BASELINE_PATH)


def save_baseline(data):
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(data, indent=2, sort_keys=True))


def cmd_diff(args):
    current = load_connections(args.project)
    baseline = load_baseline()

    new, changed, unchanged = [], [], []
    for cid, rec in current.items():
        base = baseline.get(cid)
        if base is None:
            new.append(rec)
        elif base.get("fingerprint") != rec["fingerprint"]:
            changed.append({"id": cid, "before": base, "after": rec})
        else:
            unchanged.append(rec)

    removed = [cid for cid in baseline if cid not in current]

    print(json.dumps({"new": new, "changed": changed, "unchanged": unchanged, "removed": removed}, indent=2))


def cmd_commit(args):
    """Merge scored records (JSON on stdin: {id: {risk_score, risk_bucket, notes, ...}}) into baseline."""
    current = load_connections(args.project)
    baseline = load_baseline()
    scored = json.loads(sys.stdin.read())

    for cid, rec in current.items():
        entry = baseline.get(cid, {})
        entry.update(rec)
        if cid in scored:
            entry.update(scored[cid])
            entry.setdefault("first_seen", args.today)
        entry["last_checked"] = args.today
        baseline[cid] = entry

    save_baseline(baseline)
    print(f"Baseline updated: {len(current)} connections tracked.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("diff")
    d.add_argument("--project", default=os.getcwd())
    d.set_defaults(func=cmd_diff)

    c = sub.add_parser("commit")
    c.add_argument("--project", default=os.getcwd())
    c.add_argument("--today", required=True, help="YYYY-MM-DD — passed in since scripts can't call datetime.now()")
    c.set_defaults(func=cmd_commit)

    args = p.parse_args()
    args.func(args)
