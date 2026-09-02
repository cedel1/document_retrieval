"""Reusable download services for document/page retrieval."""

from __future__ import annotations

import logging
import random
import subprocess
import time
from typing import List, Optional

logger = logging.getLogger(__name__)


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
    def retrieve_dezoomified_image(
        properties_download_url: str,
        output_base: str = "output",
        dezoomify_path: str = "dezoomify-rs",
        dezoomify_args: Optional[List[str]] = None,
    ) -> bool:
        """Download the dezoomified image for one page UUID.

        Args:
            properties_download_url: UUID of the page to download.
            output_base: Base output path to use when storing the downloaded image.
            dezoomify_path: Path or command name of the dezoomify executable.
            dezoomify_args: Optional additional command-line arguments.

        Returns:
            bool: True when the image download succeeds, otherwise False.
        """
        if not DownloadService.check_dezoomify_rs(dezoomify_path):
            logger.error("Error: dezoomify-rs not found at '%s'.", dezoomify_path)
            logger.error("Please install it using: brew install dezoomify-rs")
            logger.error("Or specify the correct path using --dezoomify-path")
            logger.error("Or download from: https://github.com/lovasoa/dezoomify-rs/releases")
            return False

        if dezoomify_args is None:
            dezoomify_args = []

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
            logger.exception(
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
