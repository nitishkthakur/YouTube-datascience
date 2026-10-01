from conftest import load_tool

approve = load_tool("approve")

DOC = "# Shot list\n\nStatus: draft\n\n## Scene 1\n- a thing\n"


def test_approve_binds_hash_and_edits_are_detected(tmp_path):
    tier = tmp_path
    (tier / "shotlist.md").write_text(DOC)
    assert approve.main([str(tier)]) == 0
    text = (tier / "shotlist.md").read_text()
    state, detail = approve.approval_state(text)
    assert state == "approved" and len(detail) == 8
    edited = text.replace("- a thing", "- a changed thing")
    assert approve.approval_state(edited)[0] == "edited"
    assert approve.approval_state(text.replace(f"approved {detail}", "approved"))[0] == "unbound"


def test_revoke_and_missing_status(tmp_path):
    (tmp_path / "shotlist.md").write_text(DOC)
    approve.main([str(tmp_path)])
    approve.main([str(tmp_path), "--revoke"])
    assert approve.approval_state((tmp_path / "shotlist.md").read_text())[0] == "draft"
    assert approve.approval_state("no status here")[0] == "none"
    assert "Status: approved x" in approve.set_status("body\n", "approved x")
