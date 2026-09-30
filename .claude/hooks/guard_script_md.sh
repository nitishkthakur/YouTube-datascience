#!/usr/bin/env bash
# PreToolUse (Edit|Write): any edit to a topic's script.md needs Nitish's explicit approval.
# script.md is his master document — narration and equations are his words (AGENTS.md §5, §9).
f=$(jq -r '.tool_input.file_path // empty')
case "$f" in
  */topics/*/script.md)
    jq -n --arg f "$f" '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "ask",
      permissionDecisionReason: ("script.md is Nitish'"'"'s master document (AGENTS.md §5.1/§9): approve this edit to " + $f)}}'
    ;;
esac
exit 0
