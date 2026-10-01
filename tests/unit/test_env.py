from dsanim import env


def test_dotenv_sets_only_missing_keys(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("# comment\nDSANIM_TEST_A=hello\nDSANIM_TEST_B=\"quoted\"\nbad line\n")
    monkeypatch.setenv("DSANIM_TEST_A", "already")
    monkeypatch.delenv("DSANIM_TEST_B", raising=False)
    loaded = env.load_dotenv(f)
    assert loaded == {"DSANIM_TEST_B": "quoted"}
    import os
    assert os.environ["DSANIM_TEST_A"] == "already" and os.environ["DSANIM_TEST_B"] == "quoted"


def test_render_env_has_tex_and_overrides():
    e = env.render_env(DSANIM_VERTICAL=1)
    assert e["DSANIM_VERTICAL"] == "1"
    if env.tinytex_bin():
        assert str(env.tinytex_bin()) in e["PATH"]
