"""Loading, validation and merging of the optional TOML configuration file.

The configuration file mirrors the command-line options. Values are resolved with the following precedence
(highest first):

1. command-line options,
2. the ``[library.<library_name>]`` table of the config file (library-dependent settings),
3. top-level keys of the config file,
4. built-in defaults.

Relative paths written inside the config file are resolved against the directory of the config file. This
includes ``dezoomify_path`` when it has a directory part; a bare command name such as ``dezoomify-rs`` is kept
for ``PATH`` lookup.
"""

from __future__ import annotations

import argparse
import logging
import tomllib
from functools import partial
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from pathvalidate.argparse import validate_filepath_arg

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_NAME = "document_retrieval.toml"
DEFAULT_OUTPUT = "output"
DEFAULT_DEZOOMIFY_PATH = "dezoomify-rs"

LIBRARY_TABLE_KEY = "library"
ACCEPT_INVALID_CERTS_ARG = "--accept-invalid-certs"
LIBRARY_KEYS = frozenset({"dezoomify_args", "allow_insecure"})


class ConfigError(ValueError):
    """Raised when the configuration file is missing, unreadable or invalid."""


def is_positive_int(value: Any):
    """Validate that a value is a positive integer (usable as an argparse ``type``).

    Args:
        value: Value to validate; ``None`` is passed through unchanged.

    Returns:
        The value converted to ``int``, or ``None`` when ``None`` was given.

    Raises:
        argparse.ArgumentTypeError: If the value is not a positive integer.
    """
    if value is None:
        return None
    try:
        int_value = int(value)
        if 0 < int_value == float(value):
            return int_value
    except (ValueError, TypeError):
        pass

    raise argparse.ArgumentTypeError("Value must be a positive integer")


def _validate_str(key: str, value: Any) -> str:
    """Validate a non-empty string value."""
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{key}' must be a non-empty string")
    return value


def _validate_path(key: str, value: Any, base_dir: Path) -> str:
    """Validate a path string and resolve a relative path against ``base_dir``."""
    _validate_str(key, value)
    path = Path(value).expanduser()
    return str(path if path.is_absolute() else base_dir / path)


def _validate_path_or_bare_name(key: str, value: Any, base_dir: Path) -> str:
    """Validate a path that may also be a bare name, and resolve a relative path against ``base_dir``.

    A bare name (no directory part, e.g. ``dezoomify-rs``) is kept unchanged so it can be looked up later
    (for example on ``PATH``). ``~`` is expanded and a relative path with a directory part
    (e.g. ``./bin/dezoomify-rs``) becomes relative to the config file's directory. Existence is not checked.
    """
    _validate_str(key, value)
    if not value.startswith("~") and Path(value).name == value:
        return value
    return _validate_path(key, value, base_dir)


def _validate_output(key: str, value: Any, base_dir: Path) -> str:
    """Validate an output directory path using the same rules as the ``--output`` option."""
    path = _validate_path(key, value, base_dir)
    try:
        validate_filepath_arg(value)
    except argparse.ArgumentTypeError as e:
        raise ConfigError(f"'{key}' is not a valid path: {e}") from e
    return path


def _validate_processes(key: str, value: Any) -> int:
    """Validate the number of processes using the same rules as the ``--processes`` option."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"'{key}' must be a positive integer")
    try:
        return is_positive_int(value)
    except argparse.ArgumentTypeError as e:
        raise ConfigError(f"'{key}' must be a positive integer") from e


def _validate_bool(key: str, value: Any) -> bool:
    """Validate a boolean value."""
    if not isinstance(value, bool):
        raise ConfigError(f"'{key}' must be true or false")
    return value


def _validate_str_list(key: str, value: Any) -> list[str]:
    """Validate a list of strings."""
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"'{key}' must be a list of strings")
    return list(value)


def _validate_pages(key: str, value: Any) -> list[str]:
    """Validate a non-empty list of page identifiers (the ``--pages`` option requires at least one)."""
    pages = _validate_str_list(key, value)
    if not pages:
        raise ConfigError(f"'{key}' must contain at least one item")
    return pages


def _top_level_validators(base_dir: Path) -> dict[str, Callable[[str, Any], Any]]:
    """Return the validators for top-level keys; path validators are bound to ``base_dir``."""
    return {
        "documents_file": partial(_validate_path, base_dir=base_dir),
        "output": partial(_validate_output, base_dir=base_dir),
        "processes": _validate_processes,
        "verbose": _validate_bool,
        "pages": _validate_pages,
        "dezoomify_path": partial(_validate_path_or_bare_name, base_dir=base_dir),
        "dezoomify_args": _validate_str_list,
        "allow_insecure": _validate_bool,
    }


_LIBRARY_VALIDATORS: dict[str, Callable[[str, Any], Any]] = {
    "dezoomify_args": _validate_str_list,
    "allow_insecure": _validate_bool,
}


def find_config(explicit_path: Optional[str], default_dir: Path) -> Optional[Path]:
    """Locate the configuration file.

    Args:
        explicit_path: Path given with ``--config``; when set, the file must exist.
        default_dir: Directory searched for ``document_retrieval.toml`` when no explicit path was given.

    Returns:
        The path of the configuration file, or ``None`` when no explicit path was given and the default file
        does not exist.

    Raises:
        ConfigError: If an explicit path was given and it is not an existing file.
    """
    if explicit_path is not None:
        path = Path(explicit_path)
        if not path.is_file():
            raise ConfigError(f"Config file not found: {explicit_path}")
        return path

    default_path = default_dir / DEFAULT_CONFIG_NAME
    return default_path if default_path.is_file() else None


def load_config(config_path: Path, known_libraries: Iterable[str]) -> dict[str, Any]:
    """Read and validate a TOML configuration file.

    Args:
        config_path: Path of the configuration file.
        known_libraries: Valid ``library_name`` values accepted as ``[library.<name>]`` table names (exact match).

    Returns:
        A dictionary with validated top-level values (paths already resolved against the config file's directory)
        and, when present, a ``library`` dictionary mapping library names to their validated settings.

    Raises:
        ConfigError: If the file cannot be read, is not valid UTF-8 or TOML, contains unknown keys or library
            tables, or holds invalid values.
    """
    try:
        with open(config_path, "rb") as config_file:
            raw = tomllib.load(config_file)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise ConfigError(f"Cannot read config file {config_path}: {e}") from e

    base_dir = config_path.resolve().parent
    validators = _top_level_validators(base_dir)
    config: dict[str, Any] = {}

    for key, value in raw.items():
        if key == LIBRARY_TABLE_KEY:
            config[LIBRARY_TABLE_KEY] = _load_library_tables(value, set(known_libraries))
        elif key in validators:
            config[key] = validators[key](key, value)
        else:
            raise ConfigError(f"Unknown config key: '{key}'")

    return config


def _load_library_tables(value: Any, known_libraries: set[str]) -> dict[str, dict[str, Any]]:
    """Validate the ``[library]`` table and every ``[library.<name>]`` table inside it."""
    if not isinstance(value, dict):
        raise ConfigError(f"'{LIBRARY_TABLE_KEY}' must be a table")

    libraries: dict[str, dict[str, Any]] = {}
    for library_name, table in value.items():
        if library_name not in known_libraries:
            raise ConfigError(f"Unknown library: '{library_name}'")
        if not isinstance(table, dict):
            raise ConfigError(f"'{LIBRARY_TABLE_KEY}.{library_name}' must be a table")
        libraries[library_name] = {}
        for key, item in table.items():
            if key not in LIBRARY_KEYS:
                raise ConfigError(f"Unknown key '{key}' in [{LIBRARY_TABLE_KEY}.{library_name}]")
            libraries[library_name][key] = _LIBRARY_VALIDATORS[key](f"{library_name}.{key}", item)
    return libraries


@dataclass(frozen=True)
class Settings:  # pylint: disable=too-many-instance-attributes
    """Application settings after merging command-line options, config file and defaults.

    Attributes:
        documents_file: Path to the file with document URLs (``None`` when neither CLI nor config provided it).
        output: Base output directory.
        processes: Number of processes for parallel processing (``None`` means one per processor core).
        verbose: Whether debug logging is enabled.
        pages: Page identifiers overriding automatic discovery (``None`` when not set).
        dezoomify_path: Path of the dezoomify-rs executable.
        dezoomify_args: Global additional dezoomify-rs arguments.
        library_dezoomify_args: Per-library dezoomify-rs arguments keyed by ``library_name``.
        allow_insecure: Whether certificate validation is disabled (``False`` means certificates are validated).
        library_allow_insecure: Per-library ``allow_insecure`` values keyed by ``library_name``.
    """

    documents_file: Optional[str] = None
    output: str = DEFAULT_OUTPUT
    processes: Optional[int] = None
    verbose: bool = False
    pages: Optional[list[str]] = None
    dezoomify_path: str = DEFAULT_DEZOOMIFY_PATH
    dezoomify_args: list[str] = field(default_factory=list)
    library_dezoomify_args: dict[str, list[str]] = field(default_factory=dict)
    allow_insecure: bool = False
    library_allow_insecure: dict[str, bool] = field(default_factory=dict)

    def dezoomify_args_for(self, library_name: str) -> list[str]:
        """Return the dezoomify-rs arguments for a library.

        Args:
            library_name: ``library_name`` of the library.

        Returns:
            The library-specific arguments when configured, otherwise the global arguments.
        """
        return list(self.library_dezoomify_args.get(library_name, self.dezoomify_args))

    def allow_insecure_for(self, library_name: str) -> bool:
        """Return whether certificate validation is disabled for a library.

        Args:
            library_name: ``library_name`` of the library.

        Returns:
            The library-specific value when configured, otherwise the global value.
        """
        return self.library_allow_insecure.get(library_name, self.allow_insecure)


def resolve_settings(args: argparse.Namespace, config: Optional[dict[str, Any]] = None) -> Settings:
    """Merge command-line options over the config file over the built-in defaults.

    A command-line option counts as given when its value is not ``None``. A ``--dezoomify-args`` value
    replaces the global config value and also all per-library values, because the command line always wins.
    The same holds for ``--allow-insecure`` / ``--no-allow-insecure``. The built-in default ``False`` only applies
    when neither the command line nor the config file set a value; it never overrides a library table.

    Args:
        args: Parsed command-line options; options not given must be ``None``.
        config: Validated config returned by :func:`load_config`, or ``None`` when there is no config file.

    Returns:
        The resolved settings.
    """
    config = config or {}

    def pick(name: str, default: Any = None) -> Any:
        cli_value = getattr(args, name, None)
        return cli_value if cli_value is not None else config.get(name, default)

    cli_dezoomify_args = getattr(args, "dezoomify_args", None)
    library_args = {} if cli_dezoomify_args is not None else _library_dezoomify_args(config)

    cli_allow_insecure = getattr(args, "allow_insecure", None)
    library_insecure = {} if cli_allow_insecure is not None else _library_allow_insecure(config)

    settings = Settings(
        documents_file=pick("documents_file"),
        output=pick("output", DEFAULT_OUTPUT),
        processes=pick("processes"),
        verbose=pick("verbose", False),
        pages=pick("pages"),
        dezoomify_path=pick("dezoomify_path", DEFAULT_DEZOOMIFY_PATH),
        dezoomify_args=pick("dezoomify_args", []),
        library_dezoomify_args=library_args,
        allow_insecure=pick("allow_insecure", False),
        library_allow_insecure=library_insecure,
    )
    _warn_about_settings(settings, config)
    return settings


def _library_dezoomify_args(config: dict[str, Any]) -> dict[str, list[str]]:
    """Extract per-library dezoomify-rs arguments from a validated config."""
    return {
        name: table["dezoomify_args"]
        for name, table in config.get(LIBRARY_TABLE_KEY, {}).items()
        if "dezoomify_args" in table
    }


def _library_allow_insecure(config: dict[str, Any]) -> dict[str, bool]:
    """Extract per-library ``allow_insecure`` values from a validated config."""
    return {
        name: table["allow_insecure"]
        for name, table in config.get(LIBRARY_TABLE_KEY, {}).items()
        if "allow_insecure" in table
    }


def _warn_about_settings(settings: Settings, config: dict[str, Any]) -> None:
    """Log warnings for disabled certificate validation and for contradicting dezoomify-rs arguments.

    The global values are checked once; libraries are checked only when their config table sets a relevant value,
    since all other libraries inherit the global values.
    """
    _warn_about_scope("global settings", settings.allow_insecure, settings.dezoomify_args)
    for name in config.get(LIBRARY_TABLE_KEY, {}):
        if name in settings.library_allow_insecure or name in settings.library_dezoomify_args:
            _warn_about_scope(f"library {name}", settings.allow_insecure_for(name), settings.dezoomify_args_for(name))


def _warn_about_scope(scope: str, allow_insecure: bool, dezoomify_args: list[str]) -> None:
    """Log the certificate-related warnings for one scope (global settings or a single library)."""
    if allow_insecure:
        logger.warning("Certificate validation is disabled for %s (allow_insecure).", scope)
    elif ACCEPT_INVALID_CERTS_ARG in dezoomify_args:
        logger.warning(
            "dezoomify_args for %s contain %s, but allow_insecure is false; the argument is passed unchanged.",
            scope,
            ACCEPT_INVALID_CERTS_ARG,
        )
