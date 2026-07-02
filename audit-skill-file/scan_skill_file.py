#!/usr/bin/env python3
"""Fingerprint a skill/prompt markdown file, extract every URL it contains, and flag
crude prompt-injection language hints. Read-only, no network calls — the actual
judgement call (is this URL/phrase actually dangerous) happens live in SKILL.md, this
just surfaces candidates so nothing gets skimmed past.
"""
import json, hashlib, sys, re, argparse
from pathlib import Path

HOME = Path.home()
BASELINE_PATH = HOME / ".config" / "trust-check" / "baseline.json"

URL_RE = re.compile(r'https?://[^\s\)\]"\'<>]+')

# Crude first-pass hints only — not exhaustive, not authoritative. SKILL.md still
# requires a full read of the file; a clever attacker won't use these exact phrases.
INJECTION_HINTS = [
    "ignore previous instructions", "ignore all previous", "ignore the above",
    "disregard prior", "do not tell the user", "don't tell the user",
    "without telling the user", "without informing the user", "do not mention this",
    "do not reveal", "secretly", "this is confidential", "always call this first",
    "always run this before", "you must always", "system prompt",
]


def fingerprint(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def read_json(path):
    return json.loads(path.read_text()) if path.exists() else {}


def save_baseline(data):
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(data, indent=2, sort_keys=True))


def scan_file(path):
    text = path.read_text()
    urls = sorted(set(URL_RE.findall(text)))
    hints = sorted({h for h in INJECTION_HINTS if h in text.lower()})
    return {
        "id": f"skill-file:{path.resolve()}",
        "kind": "skill-file",
        "path": str(path.resolve()),
        "fingerprint": fingerprint(text),
        "urls_found": urls,
        "injection_hints": hints,
    }


def cmd_diff(args):
    path = Path(args.path)
    if not path.exists():
        print(json.dumps({"error": f"file not found: {path}"}))
        sys.exit(1)
    rec = scan_file(path)
    baseline = read_json(BASELINE_PATH)
    base = baseline.get(rec["id"])
    status = "new" if base is None else ("changed" if base.get("fingerprint") != rec["fingerprint"] else "unchanged")
    print(json.dumps({"status": status, "record": rec, "previous": base}, indent=2))


def cmd_commit(args):
    """Merge a scored record (JSON on stdin: {risk_score, risk_bucket, notes, ...}) into baseline."""
    path = Path(args.path)
    rec = scan_file(path)
    scored = json.loads(sys.stdin.read())

    baseline = read_json(BASELINE_PATH)
    entry = baseline.get(rec["id"], {})
    entry.update(rec)
    entry.update(scored)
    entry.setdefault("first_seen", args.today)
    entry["last_checked"] = args.today
    baseline[rec["id"]] = entry

    save_baseline(baseline)
    print(f"Baseline updated for {path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("diff")
    d.add_argument("--path", required=True)
    d.set_defaults(func=cmd_diff)

    c = sub.add_parser("commit")
    c.add_argument("--path", required=True)
    c.add_argument("--today", required=True, help="YYYY-MM-DD")
    c.set_defaults(func=cmd_commit)

    args = p.parse_args()
    args.func(args)
