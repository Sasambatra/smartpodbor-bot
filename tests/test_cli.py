import os
import subprocess
import sys

import pytest


def run_cli(tmp_path, *arguments, input=None):
    # The demo and check must also work outside the repository, without a real token.
    environment = {**os.environ, "BOT_TOKEN": ""}
    return subprocess.run(
        [sys.executable, "-m", "smartphone_bot", *arguments],
        cwd=tmp_path,
        input=input,
        text=True,
        capture_output=True,
        timeout=20,
        env=environment,
    )


def test_check_uses_packaged_catalog_without_credentials(tmp_path):
    result = run_cli(tmp_path, "--check")
    assert result.returncode == 0
    assert "Каталог OK" in result.stdout


def test_demo_example_is_usable_without_telegram(tmp_path):
    result = run_cli(tmp_path, "--demo", "--example")
    assert result.returncode == 0
    assert "POCO X7 Pro" in result.stdout
    assert result.stdout.count("Ориентир:") == 3
    assert result.stdout.count("https://") == 9


def test_interactive_demo_accepts_custom_budget_and_answers(tmp_path):
    result = run_cli(tmp_path, "--demo", input="35 тыс.\n2\n3\n1\n2\n2\n2\n1\n")
    assert result.returncode == 0
    assert "35 000 ₽" in result.stdout
    assert "POCO X7 Pro" in result.stdout


@pytest.mark.parametrize("arguments", [(), ("--example",), ("--demo", "--check")])
def test_invalid_configuration_or_modes_show_help_without_traceback(tmp_path, arguments):
    result = run_cli(tmp_path, *arguments)
    assert result.returncode == 2
    assert result.stderr
    assert "Traceback" not in result.stderr


def test_malformed_custom_catalog_stops_with_clear_error(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("not JSON", encoding="utf-8")
    result = run_cli(tmp_path, "--check", "--catalog", str(path))
    assert result.returncode == 2
    assert "Каталог:" in result.stderr
    assert "Traceback" not in result.stderr
