import runpy

import reporting
from main import main

EASY_PUZZLE = (
    "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
)


def test_main_reads_input_and_prints_result(monkeypatch, capsys):
    reporting.reset()
    monkeypatch.setattr("builtins.input", lambda: EASY_PUZZLE)

    main()

    captured = capsys.readouterr()
    assert "---result---" in captured.out
    assert "ans_cnt: 1" in captured.out


def test_running_as_script_invokes_main(monkeypatch, capsys):
    reporting.reset()
    monkeypatch.setattr("builtins.input", lambda: EASY_PUZZLE)

    runpy.run_path("main.py", run_name="__main__")

    captured = capsys.readouterr()
    assert "---result---" in captured.out
