"""Tests for the download service orchestration."""

import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.services.download_service import DownloadService
from .fixtures import (
    certificate_discovery_error,
    dezoomify_available,
    dezoomify_missing,
    image_url,
    retrieve_image,
    subprocess_run,
)


def test_check_dezoomify_rs_should_return_true_when_binary_works(subprocess_run):
    assert DownloadService.check_dezoomify_rs("/opt/dezoomify-rs") is True
    assert subprocess_run.command == ["/opt/dezoomify-rs", "--help"]
    assert subprocess_run.kwargs["timeout"] == 5


def test_check_dezoomify_rs_should_return_false_on_non_zero_exit(subprocess_run):
    subprocess_run.result = SimpleNamespace(returncode=1, stdout="", stderr="bad")

    assert DownloadService.check_dezoomify_rs("dezoomify-rs") is False


def test_check_dezoomify_rs_should_return_false_for_missing_binary(subprocess_run):
    subprocess_run.error = FileNotFoundError("missing")

    assert DownloadService.check_dezoomify_rs("missing-rs") is False


def test_check_dezoomify_rs_should_return_false_on_subprocess_error(subprocess_run):
    subprocess_run.error = subprocess.SubprocessError("bad shell")

    assert DownloadService.check_dezoomify_rs("broken-rs") is False


def test_random_delay_should_use_uniform_delay_and_sleep():
    with (
        patch("src.services.download_service.random.uniform", return_value=3.5) as uniform,
        patch("src.services.download_service.time.sleep") as sleep,
    ):
        DownloadService.random_delay(1.0, 10.0)

    uniform.assert_called_once_with(1.0, 10.0)
    sleep.assert_called_once_with(3.5)


def test_retrieve_dezoomified_image_should_return_false_when_binary_missing(
    dezoomify_missing, subprocess_run, image_url
):
    assert DownloadService.retrieve_dezoomified_image(image_url, output_base="/tmp/out") is False
    assert subprocess_run.calls == []


def test_retrieve_dezoomified_image_should_return_false_on_subprocess_error(
    dezoomify_available, subprocess_run, image_url
):
    subprocess_run.error = subprocess.SubprocessError("shell failure")

    assert DownloadService.retrieve_dezoomified_image(image_url) is False


def test_retrieve_dezoomified_image_should_run_dezoomify_with_args(dezoomify_available, subprocess_run, image_url):
    result = DownloadService.retrieve_dezoomified_image(
        image_url,
        output_base="/tmp/out",
        dezoomify_path="/opt/dezoomify-rs",
        dezoomify_args=["--largest", "--max-width", "4000"],
    )

    assert result is True
    assert len(dezoomify_available.calls) == 1
    assert subprocess_run.command == [
        "/opt/dezoomify-rs",
        "--largest",
        "--max-width",
        "4000",
        image_url,
        "/tmp/out",
    ]
    assert subprocess_run.kwargs["check"] is False
    assert subprocess_run.kwargs["timeout"] == 5 * 60


def test_retrieve_dezoomified_image_should_return_false_on_timeout(dezoomify_available, subprocess_run, image_url):
    subprocess_run.error = subprocess.TimeoutExpired(cmd=["dezoomify-rs"], timeout=300)

    assert DownloadService.retrieve_dezoomified_image(image_url) is False


def test_retrieve_dezoomified_image_should_return_false_on_nonzero_exit(dezoomify_available, subprocess_run, image_url):
    subprocess_run.result = SimpleNamespace(returncode=2, stdout="", stderr="bad")

    assert DownloadService.retrieve_dezoomified_image(image_url) is False


def test_retrieve_dezoomified_image_should_not_add_accept_invalid_certs_by_default(retrieve_image):
    assert "--accept-invalid-certs" not in retrieve_image(dezoomify_args=["--largest"])


def test_retrieve_dezoomified_image_should_add_accept_invalid_certs_when_insecure(retrieve_image, image_url):
    command = retrieve_image(dezoomify_args=["--largest"], allow_insecure=True)

    assert command == ["dezoomify-rs", "--largest", "--accept-invalid-certs", image_url, "/tmp/out"]


@pytest.mark.parametrize("allow_insecure", [True, False])
def test_retrieve_dezoomified_image_should_keep_single_user_accept_invalid_certs(retrieve_image, allow_insecure):
    command = retrieve_image(dezoomify_args=["--accept-invalid-certs"], allow_insecure=allow_insecure)

    assert command.count("--accept-invalid-certs") == 1


def test_retrieve_dezoomified_image_should_not_modify_given_args_list(retrieve_image):
    args = ["--largest"]

    retrieve_image(dezoomify_args=args, allow_insecure=True)

    assert args == ["--largest"]


def test_retrieve_dezoomified_image_should_warn_concisely_on_certificate_failure(
    dezoomify_available, subprocess_run, image_url, certificate_discovery_error, caplog
):
    subprocess_run.result = SimpleNamespace(returncode=1, stdout="", stderr=certificate_discovery_error)
    document_url = "https://example.com/document?page=1"

    result = DownloadService.retrieve_dezoomified_image(image_url, document_url=document_url)

    assert result is False
    assert document_url in caplog.text
    assert "--allow-insecure" in caplog.text
    assert "contact the server owner" in caplog.text
    assert "certificate verify failed" not in caplog.text
    assert "Traceback" not in caplog.text


def test_retrieve_dezoomified_image_should_log_full_certificate_details_at_debug(
    dezoomify_available, subprocess_run, image_url, certificate_discovery_error, caplog
):
    subprocess_run.result = SimpleNamespace(returncode=1, stdout="", stderr=certificate_discovery_error)

    with caplog.at_level("DEBUG"):
        DownloadService.retrieve_dezoomified_image(image_url)

    assert certificate_discovery_error.strip() in caplog.text


def test_retrieve_dezoomified_image_should_not_hide_mixed_download_errors(
    dezoomify_available, subprocess_run, image_url, certificate_discovery_error, caplog
):
    stderr = certificate_discovery_error + "     - deepzoom: error sending request for url (x): connection timed out\n"
    subprocess_run.result = SimpleNamespace(returncode=1, stdout="", stderr=stderr)

    result = DownloadService.retrieve_dezoomified_image(image_url)

    assert result is False
    assert "connection timed out" in caplog.text
    assert "certificate verify failed" in caplog.text
    assert "--allow-insecure" not in caplog.text


def test_retrieve_dezoomified_image_should_not_hide_unrecognized_discovery_failure(
    dezoomify_available, subprocess_run, image_url, certificate_discovery_error, caplog
):
    stderr = certificate_discovery_error + "     - other: not a valid response\n"
    subprocess_run.result = SimpleNamespace(returncode=1, stdout="", stderr=stderr)

    DownloadService.retrieve_dezoomified_image(image_url)

    assert "not a valid response" in caplog.text
    assert "--allow-insecure" not in caplog.text


def test_retrieve_dezoomified_image_should_not_hide_whitespace_only_discovery_reason(
    dezoomify_available, subprocess_run, image_url, certificate_discovery_error, caplog
):
    stderr = certificate_discovery_error + "     - other: " + " " * 10000 + "\n"
    subprocess_run.result = SimpleNamespace(returncode=1, stdout="", stderr=stderr)

    DownloadService.retrieve_dezoomified_image(image_url)

    assert "certificate verify failed" in caplog.text
    assert "--allow-insecure" not in caplog.text


def test_retrieve_dezoomified_image_should_not_treat_other_tls_failure_as_certificate_failure(
    dezoomify_available, subprocess_run, image_url, certificate_discovery_error, caplog
):
    stderr = certificate_discovery_error.replace("certificate verify failed", "handshake failure")
    subprocess_run.result = SimpleNamespace(returncode=1, stdout="", stderr=stderr)

    DownloadService.retrieve_dezoomified_image(image_url)

    assert "handshake failure" in caplog.text
    assert "--allow-insecure" not in caplog.text
