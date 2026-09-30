#!/usr/bin/env bash
# PreToolUse (Edit|Write): any edit to a topic's script.md needs Nitish's explicit approval.
# script.md is his master document — narration and equations are his words (AGENTS.md §5, §9).
# Uses python3 (always present on macOS) rather than jq so a missing tool cannot silently
# disable it. The payload arrives on stdin, so the script is passed with -c, not a heredoc.
python3 -c "
import json, sys
try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)
f = (payload.get('tool_input') or {}).get('file_path') or ''
parts = f.replace(chr(92), '/').split('/')
if len(parts) >= 3 and parts[-1] == 'script.md' and 'topics' in parts[:-2] and parts[-2] != 'TIER' and '_template' not in parts:
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'ask',
        'permissionDecisionReason': 'script.md is Nitish' + chr(39) + 's master document (AGENTS.md 5.1/9): approve this edit to ' + f,
    }}))
"
exit 0
