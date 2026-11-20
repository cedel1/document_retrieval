"""Reusable download services for document/page retrieval."""

from __future__ import annotations

import logging
import random
import re
import subprocess
import time
from typing import List, Optional
from urllib.parse import urlparse

from src.helper_services.base_getter import SSL_ERROR_HINT
from src.settings.settings import ACCEPT_INVALID_CERTS_ARG

logger = logging.getLogger(__name__)


def _is_certificate_discovery_failure(stderr: str) -> bool:
    """Recognize dezoomify discovery failures containing only certificate errors and format mismatches."""
    if "Dezoomer error: discovery failed: no discovery candidate accepted the input" not in stderr:
        return False
    # Extract `- candidate: reason` lines to distinguish certificate-only failures from other errors.
    # The lookahead leaves at least one character for the reason, even if it is whitespace.
    reasons = []
    for line in stderr.split("\n"):
        match = re.match(r"[ \t]*-[ \t]+\w+:[ \t]+(?=.)", line, flags=re.ASCII)
        if match:
            reasons.append(line[match.end() :])
    certificate_failures = [
        reason
        for reason in reasons
        if reason.startswith(
            ("error sending request for url (", "failed to download krpano metadata: error sending request for url (")
        )
        and "): error:" in reason
        and ":SSL routines:" in reason.partition("): ")[2]
        and ":certificate verify failed:" in reason.partition("): ")[2]
    ]
    return bool(certificate_failures) and all(
        reason in certificate_failures
        or (reason.startswith(("not a ", "not an ")) and reason.endswith((" URL", " file", " template")))
        for reason in reasons
    )


class DownloadService:
    """General-purpose dezoomify download orchestration."""

    @staticmethod
    def check_dezoomify_rs(dezoomify_path: str = "dezoomify-rs") -> bool:
        """Check whether dezoomify-rs is available at the configured executable path.

        Args:
            dezoomify_path: Path or command name of the dezoomify executable.

        Returns:
            bool: True when the executable responds successfully, otherwise False.
        """
        try:
            # pylint: disable-next=subprocess-run-check
            result = subprocess.run([dezoomify_path, "--help"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
            logger.debug("dezoomify-rs --help returned non-zero: stdout=%s stderr=%s", result.stdout, result.stderr)
            return False
        except FileNotFoundError:
            logger.debug("dezoomify-rs not found at path: %s", dezoomify_path)
            return False
        except subprocess.SubprocessError as exc:
            logger.debug("Error running dezoomify-rs --help: %s", exc)
            return False

    @staticmethod
    def random_delay(min_seconds: float = 1.0, max_seconds: float = 10.0) -> None:
        """Sleep for a random delay to avoid hammering the remote service.

        Args:
            min_seconds: Lower bound for the random delay in seconds.
            max_seconds: Upper bound for the random delay in seconds.

        Returns:
            None: The method pauses execution for a random interval.
        """
        delay = random.uniform(min_seconds, max_seconds)
        logger.info("Waiting %.2f seconds before next download...", delay)
        time.sleep(delay)

    @staticmethod
    # pylint: disable-next=too-many-arguments
    def retrieve_dezoomified_image(
        properties_download_url: str,
        output_base: str = "output",
        dezoomify_path: str = "dezoomify-rs",
        dezoomify_args: Optional[List[str]] = None,
        allow_insecure: bool = False,
        *,
        document_url: Optional[str] = None,
    ) -> bool:
        """Download the dezoomified image for one page UUID.

        Args:
            properties_download_url: UUID of the page to download.
            output_base: Base output path to use when storing the downloaded image.
            dezoomify_path: Path or command name of the dezoomify executable.
            dezoomify_args: Optional additional command-line arguments.
            allow_insecure: When True, ``--accept-invalid-certs`` is passed to dezoomify-rs (unless already
                present in ``dezoomify_args``); otherwise certificates are validated, which is its default.
            document_url: Document or page URL used to identify certificate failures in warnings.

        Returns:
            bool: True when the image download succeeds, otherwise False.
        """
        if not DownloadService.check_dezoomify_rs(dezoomify_path):
            logger.error("Error: dezoomify-rs not found at '%s'.", dezoomify_path)
            logger.error("Please install it using: brew install dezoomify-rs")
            logger.error("Or specify the correct path using --dezoomify-path")
            logger.error("Or download from: https://github.com/lovasoa/dezoomify-rs/releases")
            return False

        dezoomify_args = list(dezoomify_args or [])
        if allow_insecure and ACCEPT_INVALID_CERTS_ARG not in dezoomify_args:
            dezoomify_args.append(ACCEPT_INVALID_CERTS_ARG)

        logger.info("Using dezoomify-rs to download image from: %s", properties_download_url)

        try:
            DownloadService.random_delay()  # Random delay to avoid hammering the server
            logger.debug("Dezoomify-args: %s", dezoomify_args)
            result = subprocess.run(
                [dezoomify_path, *dezoomify_args, properties_download_url, output_base],
                capture_output=True,
                text=True,
                check=False,
                timeout=5 * 60,
            )
            if result.returncode == 0:
                logger.info("Image with output base %s downloaded successfully.", output_base)
                return True
            if not result.stdout.strip() and _is_certificate_discovery_failure(result.stderr):
                logger.warning(
                    SSL_ERROR_HINT, urlparse(properties_download_url).hostname, document_url or properties_download_url
                )
                logger.debug("dezoomify-rs certificate failure: %s", result.stderr)
                return False
            logger.error(
                "Error running dezoomify-rs (returncode=%s). stdout=%s stderr=%s",
                result.returncode,
                result.stdout,
                result.stderr,
            )
            return False
        except subprocess.TimeoutExpired as exc:
            logger.exception("Error: dezoomify-rs timed out: %s", exc)
            return False
        except subprocess.SubprocessError as exc:
            logger.exception("Error running dezoomify-rs: %s", exc)
            return False
