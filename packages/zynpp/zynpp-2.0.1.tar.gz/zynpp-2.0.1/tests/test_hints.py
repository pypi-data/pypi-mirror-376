from pathlib import Path

from zpp.hints_rule import generate_hints


def test_reserve_hint(tmp_path: Path) -> None:
    code = (
        "#include <vector>\nusing namespace std;\nint main(){ vector<int> a; for(int i=0;i<n;i++) a.push_back(i); }\n"
    )
    p = tmp_path / "m.cpp"
    p.write_text(code, encoding="utf-8")
    hints = generate_hints(p)
    assert any("Reserve" in h.title for h in hints)


