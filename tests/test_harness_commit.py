from membench.harness_commit import harness_commit


def test_it_reports_this_repository_s_commit():
    result = harness_commit()
    assert len(result["commit"]) == 40
    assert set(result["commit"]) <= set("0123456789abcdef")
    assert isinstance(result["dirty"], bool)


def test_it_admits_ignorance_outside_a_repository(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = harness_commit()
    assert result == {"commit": "unknown", "dirty": True}
