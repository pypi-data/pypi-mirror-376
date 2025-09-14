import subprocess


def run(cmd: str) -> str:
    return subprocess.run(
        cmd,
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ).stdout


def test_version():
    out = run("bgm-labour --version")
    assert "bgm-toolkit-labour" in out


def test_ok():
    out = run("bgm-labour")
    assert "ok" in out.lower()
