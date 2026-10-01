"""Skill 3am-safety: lo script di preflight su repository costruiti con i problemi noti dentro."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "3am-safety" / "scripts" / "preflight.py"
FAKE_KEY = "sk-" + "A1b2C3d4" * 4                  # costruita qui: nessuna chiave vera nel repository


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "t")
    (r / "app.py").write_text("print('ok')\n", encoding="utf-8")
    git(r, "add", ".")
    git(r, "commit", "-q", "-m", "init")
    return r


def run(repo, *extra):
    p = subprocess.run([sys.executable, str(SCRIPT), str(repo), "--json", *extra], capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout), p


def levels(rep, check):
    return [f["level"] for f in rep["findings"] if f["check"] == check]


def test_clean_repo_is_not_blocked(repo):
    code, rep, _ = run(repo, "--min-free-gb", "0")
    assert "BLOCK" not in {f["level"] for f in rep["findings"]}
    assert code in (0, 1)                            # i processi della macchina possono dare un avviso


def test_secret_in_untracked_file_is_blocked_and_never_printed(repo):
    (repo / "config.py").write_text(f'API = "{FAKE_KEY}"\n', encoding="utf-8")
    code, rep, p = run(repo, "--min-free-gb", "0")
    assert code == 2 and rep["verdict"] == "NO-GO"
    hit = [f for f in rep["findings"] if f["check"] == "secrets"]
    assert hit and hit[0]["file"] == "config.py" and hit[0]["line"] == 1
    assert FAKE_KEY not in p.stdout and FAKE_KEY not in p.stderr
    human = subprocess.run([sys.executable, str(SCRIPT), str(repo), "--min-free-gb", "0"], capture_output=True, text=True)
    assert FAKE_KEY not in human.stdout


def test_env_file_not_ignored_is_blocked_but_ignored_one_is_not(repo):
    (repo / ".env").write_text("X=1\n", encoding="utf-8")
    assert run(repo, "--min-free-gb", "0")[0] == 2
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    code, rep, _ = run(repo, "--min-free-gb", "0")
    assert "BLOCK" not in levels(rep, "secrets")


def test_uncommitted_and_new_files_warn(repo):
    (repo / "app.py").write_text("print('changed')\n", encoding="utf-8")
    (repo / "notes.md").write_text("x\n", encoding="utf-8")
    code, rep, _ = run(repo, "--min-free-gb", "0")
    msgs = " ".join(f["message"] for f in rep["findings"] if f["check"] == "git")
    assert "uncommitted" in msgs and "never committed" in msgs and code >= 1


def test_index_lock_blocks(repo):
    (repo / ".git" / "index.lock").write_text("", encoding="utf-8")
    assert run(repo, "--min-free-gb", "0")[0] == 2


def test_low_disk_blocks(repo):
    code, rep, _ = run(repo, "--min-free-gb", "100000000")      # soglia irraggiungibile = disco "pieno"
    assert code == 2 and "BLOCK" in levels(rep, "disk")


def test_big_untracked_file_warns(repo):
    (repo / "dump.bin").write_bytes(b"0" * (2 * 1024 * 1024))
    code, rep, _ = run(repo, "--min-free-gb", "0", "--big-file-mb", "1")
    assert any("large untracked" in f["message"] for f in rep["findings"])


def test_not_a_repo_is_a_warning_not_a_crash(tmp_path):
    code, rep, _ = run(tmp_path, "--min-free-gb", "0")
    assert "not a git repository" in json.dumps(rep) and code in (1, 2)


def test_iteration2_advice_branch_gitignore_backup(repo):
    """v1.1 (dall'eval con baseline senza skill): ramo dedicato, .gitignore, copia unica del repository."""
    code, rep, _ = run(repo, "--min-free-gb", "0")
    text = json.dumps(rep)
    assert "no .gitignore" in text and "its own branch" in text and "one copy only" in text


def test_private_secret_file_names_come_from_the_command_line(repo):
    """Il nome del file privato delle chiavi non sta nel codice (il codice e' pubblicabile): si passa da riga di comando."""
    (repo / "mykeys").write_text("x\n", encoding="utf-8")
    assert run(repo, "--min-free-gb", "0")[0] != 2
    assert run(repo, "--min-free-gb", "0", "--secret-file", "mykeys")[0] == 2
    (repo / "api_keys.txt").write_text("x\n", encoding="utf-8")
    assert run(repo, "--min-free-gb", "0")[0] == 2
