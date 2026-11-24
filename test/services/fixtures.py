"""Shared fixtures for service tests."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.services.download_service import DownloadService

IMAGE_URL = "https://example.com/image"


class SubprocessRunRecorder:
    """Replacement for ``subprocess.run`` that records calls and returns or raises a configured outcome."""

    def __init__(self):
        self.calls = []
        self.result = SimpleNamespace(returncode=0, stdout="ok", stderr="")
        self.error = None

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if self.error is not None:
            raise self.error
        return self.result

    @property
    def command(self):
        """Return the command of the last call."""
        return self.calls[-1][0]

    @property
    def kwargs(self):
        """Return the keyword arguments of the last call."""
        return self.calls[-1][1]


@pytest.fixture
def certificate_discovery_error():
    """Return a certificate-only dezoomify discovery failure."""
    return (
        "[ERROR] Dezoomer error: discovery failed: no discovery candidate accepted the input\n"
        "     - custom: not a tiles.yaml file\n"
        "     - zoomify: error sending request for url (https://example.com/image): "
        "error:0A000086:SSL routines:certificate verify failed:ssl/statem/statem_clnt.c:2124:\n"
        "     - iiif: error sending request for url (https://example.com/image): "
        "error:0A000086:SSL routines:certificate verify failed:ssl/statem/statem_clnt.c:2124:\n"
        "     - krpano: failed to download krpano metadata: error sending request for url (https://example.com/image): "
        "error:0A000086:SSL routines:certificate verify failed:ssl/statem/statem_clnt.c:2124:\n"
        "    Tried all of the dezoomers, none succeeded.\n"
    )


@pytest.fixture
def image_url():
    """Fixture providing the sample image properties URL."""
    return IMAGE_URL


@pytest.fixture
def subprocess_run():
    """Fixture replacing ``subprocess.run`` with a recorder; set ``.result`` or ``.error`` to change the outcome."""
    recorder = SubprocessRunRecorder()
    with patch("subprocess.run", recorder):
        yield recorder


@pytest.fixture
def dezoomify_available():
    """Fixture making dezoomify-rs appear installed; yields a namespace recording the skipped random delays."""
    delays = SimpleNamespace(calls=[])
    with (
        patch.object(DownloadService, "check_dezoomify_rs", return_value=True),
        patch.object(
            DownloadService, "random_delay", side_effect=lambda *args, **kwargs: delays.calls.append((args, kwargs))
        ),
    ):
        yield delays


@pytest.fixture
def dezoomify_missing():
    """Fixture making dezoomify-rs appear not installed."""
    with patch.object(DownloadService, "check_dezoomify_rs", return_value=False):
        yield


@pytest.fixture
def retrieve_image(dezoomify_available, subprocess_run, image_url):
    """Fixture providing a function that downloads the sample image and returns the dezoomify-rs command used."""

    def _retrieve(**kwargs):
        DownloadService.retrieve_dezoomified_image(image_url, output_base="/tmp/out", **kwargs)
        return subprocess_run.command

    return _retrieve
