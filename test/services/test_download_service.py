"""Tests for the download service orchestration."""

import subprocess
from types import SimpleNamespace

import pytest

from src.services.download_service import DownloadService


def test_check_dezoomify_rs_returns_true_when_binary_works(monkeypatch):
    captured = {}

    def fake_run(command, capture_output, text, timeout):
        captured["command"] = command
        captured["timeout"] = timeout
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert DownloadService.check_dezoomify_rs("/opt/dezoomify-rs") is True
    assert captured["command"] == ["/opt/dezoomify-rs", "--help"]
    assert captured["timeout"] == 5


def test_check_dezoomify_rs_returns_false_on_non_zero_exit(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr="bad"))

    assert DownloadService.check_dezoomify_rs("dezoomify-rs") is False


def test_check_dezoomify_rs_returns_false_for_missing_binary(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert DownloadService.check_dezoomify_rs("missing-rs") is False


def test_check_dezoomify_rs_returns_false_on_subprocess_error(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.SubprocessError("bad shell")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert DownloadService.check_dezoomify_rs("broken-rs") is False


def test_random_delay_uses_uniform_delay_and_sleep(monkeypatch):
    captured = {}
    monkeypatch.setattr("src.services.download_service.random.uniform", lambda min_value, max_value: 3.5)

    def fake_sleep(seconds):
        captured["seconds"] = seconds

    monkeypatch.setattr("src.services.download_service.time.sleep", fake_sleep)

    DownloadService.random_delay(1.0, 10.0)

    assert captured["seconds"] == 3.5


def test_retrieve_dezoomified_image_returns_false_when_binary_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(DownloadService, "check_dezoomify_rs", lambda path="dezoomify-rs": False)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)) or SimpleNamespace(returncode=0))

    assert DownloadService.retrieve_dezoomified_image("https://example.com/image", output_base="/tmp/out") is False
    assert calls == []


def test_retrieve_dezoomified_image_returns_false_on_subprocess_error(monkeypatch):
    monkeypatch.setattr(DownloadService, "check_dezoomify_rs", lambda path="dezoomify-rs": True)
    monkeypatch.setattr(DownloadService, "random_delay", lambda *args, **kwargs: None)

    def fake_run(*args, **kwargs):
        raise subprocess.SubprocessError("shell failure")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert DownloadService.retrieve_dezoomified_image("https://example.com/image") is False


def test_retrieve_dezoomified_image_runs_dezoomify_with_args(monkeypatch):
    captured = {}
    monkeypatch.setattr(DownloadService, "check_dezoomify_rs", lambda path="dezoomify-rs": True)
    monkeypatch.setattr(DownloadService, "random_delay", lambda *args, **kwargs: captured.setdefault("delay_called", True))

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = DownloadService.retrieve_dezoomified_image(
        "https://example.com/image",
        output_base="/tmp/out",
        dezoomify_path="/opt/dezoomify-rs",
        dezoomify_args=["--largest", "--max-width", "4000"],
    )

    assert result is True
    assert captured["delay_called"] is True
    assert captured["command"] == ["/opt/dezoomify-rs", "--largest", "--max-width", "4000", "https://example.com/image", "/tmp/out"]
    assert captured["kwargs"]["check"] is False
    assert captured["kwargs"]["timeout"] == 5 * 60


def test_retrieve_dezoomified_image_returns_false_on_timeout(monkeypatch):
    monkeypatch.setattr(DownloadService, "check_dezoomify_rs", lambda path="dezoomify-rs": True)
    monkeypatch.setattr(DownloadService, "random_delay", lambda *args, **kwargs: None)

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["dezoomify-rs"], timeout=300)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert DownloadService.retrieve_dezoomified_image("https://example.com/image") is False


def test_retrieve_dezoomified_image_returns_false_on_nonzero_exit(monkeypatch):
    monkeypatch.setattr(DownloadService, "check_dezoomify_rs", lambda path="dezoomify-rs": True)
    monkeypatch.setattr(DownloadService, "random_delay", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=2, stdout="", stderr="bad"),
    )

    assert DownloadService.retrieve_dezoomified_image("https://example.com/image") is False
