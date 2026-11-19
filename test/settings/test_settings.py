"""Tests for the settings module (config file loading and settings resolution)."""

from argparse import ArgumentTypeError

import pytest

from src.settings.settings import (
    ConfigError,
    Settings,
    find_config,
    is_positive_int,
    load_config,
    resolve_settings,
)
from .fixtures import LIBRARY_NAME, known_libraries, write_config, cli_args


@pytest.mark.parametrize(
    "input_value, expected_value",
    [
        (5, 5),
        (1, 1),
        ("5", 5),
        ("1", 1),
        (None, None),
    ],
)
def test_is_positive_int_should_return_value_for_valid_input(input_value, expected_value):
    """Tests that is_positive_int returns correct value when the validation succeeds."""
    assert is_positive_int(input_value) == expected_value


@pytest.mark.parametrize(
    "input_value",
    [
        "abc",
        2.3,
        -1,
        -2.1,
        0,
    ],
)
def test_is_positive_int_should_raise_for_invalid_input(input_value):
    """Tests that is_positive_int raises when the validation does not succeed."""
    with pytest.raises(ArgumentTypeError):
        is_positive_int(input_value)


def test_find_config_should_return_explicit_path_when_file_exists(write_config, tmp_path):
    """Tests that an existing explicit config path is returned."""
    config_path = write_config("", "custom.toml")

    assert find_config(str(config_path), tmp_path / "elsewhere") == config_path


def test_find_config_should_raise_when_explicit_file_is_missing(tmp_path):
    """Tests that a missing explicitly given config file is an error."""
    missing_path = str(tmp_path / "missing.toml")

    with pytest.raises(ConfigError, match="Config file not found"):
        find_config(missing_path, tmp_path)


def test_find_config_should_return_default_file_when_no_explicit_path_given(write_config, tmp_path):
    """Tests that document_retrieval.toml in the default directory is auto-discovered."""
    config_path = write_config("")

    assert find_config(None, tmp_path) == config_path


def test_find_config_should_return_none_when_default_file_is_missing(tmp_path):
    """Tests that a missing default config file is silently ignored."""
    assert find_config(None, tmp_path) is None


def test_load_config_should_return_validated_values_for_valid_file(write_config, known_libraries):
    """Tests that valid top-level values are loaded."""
    config_path = write_config(
        'verbose = true\nprocesses = 3\npages = ["a", "b"]\n'
        'dezoomify_path = "/usr/bin/dezoomify-rs"\ndezoomify_args = ["--x", "1"]\n'
    )

    assert load_config(config_path, known_libraries) == {
        "verbose": True,
        "processes": 3,
        "pages": ["a", "b"],
        "dezoomify_path": "/usr/bin/dezoomify-rs",
        "dezoomify_args": ["--x", "1"],
    }


def test_load_config_should_return_empty_dict_for_empty_file(write_config, known_libraries):
    """Tests that an empty config file yields no values."""
    assert not load_config(write_config(""), known_libraries)


@pytest.mark.parametrize("key", ["documents_file", "output"])
def test_load_config_should_resolve_relative_path_against_config_directory(
    write_config, known_libraries, tmp_path, key
):
    """Tests that relative paths are resolved against the config file's directory."""
    config = load_config(write_config(f'{key} = "sub/value"'), known_libraries)

    assert config[key] == str(tmp_path / "sub" / "value")


@pytest.mark.parametrize("key", ["documents_file", "output"])
def test_load_config_should_keep_absolute_path_unchanged(write_config, known_libraries, key):
    """Tests that absolute paths are not changed."""
    config = load_config(write_config(f'{key} = "/abs/value"'), known_libraries)

    assert config[key] == "/abs/value"


def test_load_config_should_load_library_table_values(write_config, known_libraries):
    """Tests that [library.<library_name>] values are loaded."""
    config = load_config(write_config(f'[library.{LIBRARY_NAME}]\ndezoomify_args = ["-l", "2"]'), known_libraries)

    assert config == {"library": {LIBRARY_NAME: {"dezoomify_args": ["-l", "2"]}}}


def test_load_config_should_raise_for_unknown_top_level_key(write_config, known_libraries):
    """Tests that an unknown top-level key is an error."""
    config_path = write_config("verfy = true")

    with pytest.raises(ConfigError, match="Unknown config key: 'verfy'"):
        load_config(config_path, known_libraries)


def test_load_config_should_raise_for_unknown_library_table(write_config, known_libraries):
    """Tests that an unknown library table is an error."""
    config_path = write_config('[library.dsmo]\ndezoomify_args = ["x"]')

    with pytest.raises(ConfigError, match="Unknown library: 'dsmo'"):
        load_config(config_path, known_libraries)


def test_load_config_should_raise_for_unknown_key_in_library_table(write_config, known_libraries):
    """Tests that an unknown key inside a library table is an error."""
    config_path = write_config(f'[library.{LIBRARY_NAME}]\nbrowser = "firefox"')

    with pytest.raises(ConfigError, match="Unknown key 'browser'"):
        load_config(config_path, known_libraries)


def test_load_config_should_raise_when_library_is_not_a_table(write_config, known_libraries):
    """Tests that a non-table 'library' value is an error."""
    config_path = write_config("library = 1")

    with pytest.raises(ConfigError, match="'library' must be a table"):
        load_config(config_path, known_libraries)


def test_load_config_should_raise_when_library_entry_is_not_a_table(write_config, known_libraries):
    """Tests that a non-table library entry is an error."""
    config_path = write_config(f"[library]\n{LIBRARY_NAME} = 1")

    with pytest.raises(ConfigError, match="must be a table"):
        load_config(config_path, known_libraries)


@pytest.mark.parametrize(
    "content",
    [
        'verbose = "yes"',
        "verbose = 1",
        'processes = "3"',
        "processes = 0",
        "processes = -2",
        "processes = 1.5",
        "processes = true",
        "pages = []",
        'pages = "a"',
        "pages = [1]",
        "dezoomify_args = 5",
        "dezoomify_args = [1, 2]",
        "dezoomify_path = 1",
        'dezoomify_path = ""',
        "documents_file = 1",
        'documents_file = ""',
        "output = 1",
        'output = "bad\\u0000path"',
    ],
)
def test_load_config_should_raise_for_invalid_value(write_config, known_libraries, content):
    """Tests that wrong types and invalid values are errors."""
    config_path = write_config(content)

    with pytest.raises(ConfigError):
        load_config(config_path, known_libraries)


def test_load_config_should_raise_for_invalid_library_value(write_config, known_libraries):
    """Tests that an invalid value inside a library table is an error."""
    config_path = write_config(f"[library.{LIBRARY_NAME}]\ndezoomify_args = 5")

    with pytest.raises(ConfigError, match="must be a list of strings"):
        load_config(config_path, known_libraries)


def test_load_config_should_raise_for_malformed_toml(write_config, known_libraries):
    """Tests that a syntax error in the file is reported as a ConfigError."""
    config_path = write_config("this is = = not toml")

    with pytest.raises(ConfigError, match="Cannot read config file"):
        load_config(config_path, known_libraries)


def test_load_config_should_raise_when_file_is_unreadable(tmp_path, known_libraries):
    """Tests that an unreadable file is reported as a ConfigError."""
    missing_path = tmp_path / "missing.toml"

    with pytest.raises(ConfigError, match="Cannot read config file"):
        load_config(missing_path, known_libraries)


def test_resolve_settings_should_use_defaults_when_nothing_given(cli_args):
    """Tests that built-in defaults are used without CLI options or config."""
    assert resolve_settings(cli_args()) == Settings()


def test_resolve_settings_should_use_config_values_when_cli_not_given(cli_args):
    """Tests that config values apply when the CLI does not give the option."""
    config = {"output": "/out", "processes": 2, "verbose": True, "pages": ["p"], "dezoomify_path": "/dz"}

    settings = resolve_settings(cli_args(), config)

    assert (settings.output, settings.processes, settings.verbose, settings.pages, settings.dezoomify_path) == (
        "/out",
        2,
        True,
        ["p"],
        "/dz",
    )


def test_resolve_settings_should_prefer_cli_values_over_config(cli_args):
    """Tests that CLI values override config values."""
    config = {"output": "/out", "processes": 2, "dezoomify_path": "/dz"}

    settings = resolve_settings(cli_args(output="cli_out", processes=5, dezoomify_path="cli_dz"), config)

    assert (settings.output, settings.processes, settings.dezoomify_path) == ("cli_out", 5, "cli_dz")


def test_resolve_settings_should_replace_config_list_with_cli_list(cli_args):
    """Tests that a CLI list replaces (does not extend) the config list."""
    settings = resolve_settings(
        cli_args(pages=["c"], dezoomify_args=["--c"]), {"pages": ["a"], "dezoomify_args": ["--a"]}
    )

    assert (settings.pages, settings.dezoomify_args) == (["c"], ["--c"])


def test_resolve_settings_should_let_verbose_flag_override_config(cli_args):
    """Tests that --verbose on the CLI wins over verbose = false in the config."""
    assert resolve_settings(cli_args(verbose=True), {"verbose": False}).verbose is True


def test_resolve_settings_should_ignore_library_args_when_cli_dezoomify_args_given(cli_args):
    """Tests that CLI dezoomify args also override per-library config values."""
    config = {"library": {LIBRARY_NAME: {"dezoomify_args": ["--lib"]}}}

    settings = resolve_settings(cli_args(dezoomify_args=["--cli"]), config)

    assert settings.dezoomify_args_for(LIBRARY_NAME) == ["--cli"]


def test_dezoomify_args_for_should_prefer_library_args_over_global(cli_args):
    """Tests that library-table dezoomify args win over top-level config args."""
    config = {"dezoomify_args": ["--global"], "library": {LIBRARY_NAME: {"dezoomify_args": ["--lib"]}}}

    assert resolve_settings(cli_args(), config).dezoomify_args_for(LIBRARY_NAME) == ["--lib"]


def test_dezoomify_args_for_should_fall_back_to_global_args_for_other_library(cli_args):
    """Tests that libraries without their own table use the global dezoomify args."""
    config = {"dezoomify_args": ["--global"], "library": {LIBRARY_NAME: {"dezoomify_args": ["--lib"]}}}

    assert resolve_settings(cli_args(), config).dezoomify_args_for("Other") == ["--global"]


def test_dezoomify_args_for_should_return_copy_of_args():
    """Tests that mutating the returned list does not change the settings."""
    settings = Settings(dezoomify_args=["--a"])

    settings.dezoomify_args_for("Any").append("--b")

    assert settings.dezoomify_args == ["--a"]
