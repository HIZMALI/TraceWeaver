from pathlib import Path

from traceweaver.judge import main


def test_missing_judge_bundle_never_creates_data(tmp_path, capsys):
    assert main(["--bundle", str(tmp_path / "missing"), "--check"]) == 1
    assert "FAIL" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_actual_judge_launcher_check_preserves_store(capsys, tmp_path, monkeypatch):
    # Only static resource presence is controlled; graph verification uses the real immutable file.
    assets = tmp_path / "web_static" / "assets"
    assets.mkdir(parents=True)
    (assets.parent / "index.html").write_text("Unit resource presence input")
    (assets / "unit.js").write_text("// Unit resource presence input")
    monkeypatch.setattr("traceweaver.judge.files", lambda _: tmp_path)
    bundle = Path(__file__).resolve().parents[2] / "examples/judge-demo"
    store = bundle / "traceweaver-demo.rl"
    before = store.read_bytes()
    assert main(["--bundle", str(bundle), "--check"]) == 0
    assert '"model_invoked": false' in capsys.readouterr().out
    assert store.read_bytes() == before
