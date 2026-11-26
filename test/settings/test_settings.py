"""Tests for the settings module (config file loading and settings resolution)."""

from argparse import ArgumentTypeError
from pathlib import Path

import pytest

from src.settings.settings import (
    ConfigError,
    Settings,
    find_config,
    is_positive_int,
    load_config,
    resolve_settings,
    validate_images_subfolder_arg,
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


@pytest.mark.parametrize("value", ["./bin/dezoomify-rs", "bin/dezoomify-rs", "../dezoomify-rs"])
def test_load_config_should_resolve_relative_dezoomify_path_against_config_directory(
    write_config, known_libraries, tmp_path, value
):
    """Tests that a dezoomify_path with a directory part is resolved against the config file's directory."""
    config = load_config(write_config(f'dezoomify_path = "{value}"'), known_libraries)

    assert config["dezoomify_path"] == str(tmp_path / value)


@pytest.mark.parametrize("value", ["dezoomify-rs", "/usr/bin/dezoomify-rs"])
def test_load_config_should_keep_bare_or_absolute_dezoomify_path_unchanged(write_config, known_libraries, value):
    """Tests that a bare command name (PATH lookup) and an absolute path are not changed."""
    config = load_config(write_config(f'dezoomify_path = "{value}"'), known_libraries)

    assert config["dezoomify_path"] == value


def test_load_config_should_expand_home_in_dezoomify_path(write_config, known_libraries):
    """Tests that ~ in dezoomify_path is expanded to an absolute path."""
    config = load_config(write_config('dezoomify_path = "~/bin/dezoomify-rs"'), known_libraries)

    assert config["dezoomify_path"] == str(Path("~/bin/dezoomify-rs").expanduser())


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


def test_load_config_should_raise_for_non_toml_extension(write_config, known_libraries):
    """Tests that a file without a .toml extension is rejected."""
    config_path = write_config("", name="secrets.txt")

    with pytest.raises(ConfigError, match=r"\.toml extension"):
        load_config(config_path, known_libraries)


def test_load_config_should_raise_for_non_utf8_file(tmp_path, known_libraries):
    """Tests that a file in a non-UTF-8 encoding is reported as a ConfigError."""
    config_path = tmp_path / "windows.toml"
    config_path.write_bytes('output = "příliš"\n'.encode("cp1250"))

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


def test_resolve_settings_should_validate_certificates_by_default(cli_args):
    settings = resolve_settings(cli_args())

    assert settings.allow_insecure is False
    assert settings.allow_insecure_for(LIBRARY_NAME) is False


def test_resolve_settings_should_use_top_level_allow_insecure_from_config(cli_args):
    settings = resolve_settings(cli_args(), {"allow_insecure": True})

    assert settings.allow_insecure_for(LIBRARY_NAME) is True


def test_resolve_settings_should_prefer_library_allow_insecure_over_top_level(cli_args):
    config = {"allow_insecure": False, "library": {LIBRARY_NAME: {"allow_insecure": True}}}

    settings = resolve_settings(cli_args(), config)

    assert settings.allow_insecure is False
    assert settings.allow_insecure_for(LIBRARY_NAME) is True
    assert settings.allow_insecure_for("Other") is False


def test_resolve_settings_should_not_override_library_value_with_default(cli_args):
    config = {"library": {LIBRARY_NAME: {"allow_insecure": True}}}

    assert resolve_settings(cli_args(), config).allow_insecure_for(LIBRARY_NAME) is True


@pytest.mark.parametrize("cli_value", [True, False])
def test_resolve_settings_should_let_cli_allow_insecure_override_library_tables(cli_args, cli_value):
    config = {"allow_insecure": not cli_value, "library": {LIBRARY_NAME: {"allow_insecure": not cli_value}}}

    settings = resolve_settings(cli_args(allow_insecure=cli_value), config)

    assert settings.allow_insecure is cli_value
    assert settings.allow_insecure_for(LIBRARY_NAME) is cli_value


def test_load_config_should_read_allow_insecure_at_top_level_and_in_library(write_config, known_libraries):
    config_path = write_config(f"allow_insecure = true\n[library.{LIBRARY_NAME}]\nallow_insecure = false\n")

    config = load_config(config_path, known_libraries)

    assert config["allow_insecure"] is True
    assert config["library"][LIBRARY_NAME]["allow_insecure"] is False


@pytest.mark.parametrize("value", ['"yes"', "1", "[true]"])
@pytest.mark.parametrize(
    "template", ["allow_insecure = {value}\n", f"[library.{LIBRARY_NAME}]\nallow_insecure = {{value}}\n"]
)
def test_load_config_should_reject_non_boolean_allow_insecure(write_config, known_libraries, template, value):
    config_path = write_config(template.format(value=value))

    with pytest.raises(ConfigError, match="allow_insecure"):
        load_config(config_path, known_libraries)


def test_load_config_should_still_reject_unknown_library_key(write_config, known_libraries):
    config_path = write_config(f"[library.{LIBRARY_NAME}]\nallow_insecur = true\n")

    with pytest.raises(ConfigError, match="Unknown key"):
        load_config(config_path, known_libraries)


def test_resolve_settings_should_warn_when_global_validation_disabled(cli_args, caplog):
    with caplog.at_level("WARNING"):
        resolve_settings(cli_args(allow_insecure=True))

    assert "Certificate validation is disabled for global settings" in caplog.text


def test_resolve_settings_should_warn_for_library_with_validation_disabled(cli_args, caplog):
    config = {"library": {LIBRARY_NAME: {"allow_insecure": True}}}

    with caplog.at_level("WARNING"):
        resolve_settings(cli_args(), config)

    assert f"Certificate validation is disabled for library {LIBRARY_NAME}" in caplog.text


def test_resolve_settings_should_not_warn_when_validating(cli_args, caplog):
    with caplog.at_level("WARNING"):
        resolve_settings(cli_args())

    assert caplog.text == ""


def test_resolve_settings_should_warn_when_accept_invalid_certs_contradicts_setting(cli_args, caplog):
    with caplog.at_level("WARNING"):
        settings = resolve_settings(cli_args(dezoomify_args=["--accept-invalid-certs"]))

    assert "--accept-invalid-certs" in caplog.text
    assert settings.dezoomify_args == ["--accept-invalid-certs"]


def test_resolve_settings_should_warn_for_contradicting_library_dezoomify_args(cli_args, caplog):
    config = {"library": {LIBRARY_NAME: {"dezoomify_args": ["--accept-invalid-certs"]}}}

    with caplog.at_level("WARNING"):
        settings = resolve_settings(cli_args(), config)

    assert f"library {LIBRARY_NAME}" in caplog.text
    assert settings.dezoomify_args_for(LIBRARY_NAME) == ["--accept-invalid-certs"]


def test_resolve_settings_should_not_warn_about_contradiction_when_insecure(cli_args, caplog):
    with caplog.at_level("WARNING"):
        resolve_settings(cli_args(allow_insecure=True, dezoomify_args=["--accept-invalid-certs"]))

    assert "passed unchanged" not in caplog.text


def test_validate_images_subfolder_arg_should_return_plain_name():
    assert validate_images_subfolder_arg("images") == "images"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "  ",
        ".",
        "..",
        "a/b",
        "a\\b",
        "/abs",
        None,
        5,
        "CON",
        "nul",
        "a:b",
        "a?b",
        "a*b",
        "a<b",
        "name.",
        "name ",
        "a|b",
        "properties.txt",
        "Properties.TXT",
    ],
)
def test_validate_images_subfolder_arg_should_raise_for_invalid_name(value):
    with pytest.raises(ArgumentTypeError):
        validate_images_subfolder_arg(value)


def test_load_config_should_read_images_subfolder_at_top_level_and_in_library(write_config, known_libraries):
    config_path = write_config(f'images_subfolder = "img"\n[library.{LIBRARY_NAME}]\nimages_subfolder = "lib_img"\n')

    config = load_config(config_path, known_libraries)

    assert config["images_subfolder"] == "img"
    assert config["library"][LIBRARY_NAME]["images_subfolder"] == "lib_img"


@pytest.mark.parametrize(
    "value",
    ['""', '".."', '"a/b"', '"/abs"', "1", "[1]", '"CON"', '"a:b"', '"name."', '"properties.txt"', '"PROPERTIES.txt"'],
)
@pytest.mark.parametrize(
    "template", ["images_subfolder = {value}\n", f"[library.{LIBRARY_NAME}]\nimages_subfolder = {{value}}\n"]
)
def test_load_config_should_reject_invalid_images_subfolder(write_config, known_libraries, template, value):
    config_path = write_config(template.format(value=value))

    with pytest.raises(ConfigError, match="images_subfolder"):
        load_config(config_path, known_libraries)


def test_resolve_settings_should_default_images_subfolder_to_none(cli_args):
    settings = resolve_settings(cli_args())

    assert settings.images_subfolder is None
    assert settings.images_subfolder_for(LIBRARY_NAME) is None


def test_resolve_settings_should_prefer_library_images_subfolder_over_top_level(cli_args):
    config = {"images_subfolder": "top", "library": {LIBRARY_NAME: {"images_subfolder": "lib"}}}

    settings = resolve_settings(cli_args(), config)

    assert settings.images_subfolder_for(LIBRARY_NAME) == "lib"
    assert settings.images_subfolder_for("Other") == "top"


def test_resolve_settings_should_let_cli_images_subfolder_override_library_tables(cli_args):
    config = {"images_subfolder": "top", "library": {LIBRARY_NAME: {"images_subfolder": "lib"}}}

    settings = resolve_settings(cli_args(images_subfolder="cli"), config)

    assert settings.images_subfolder == "cli"
    assert settings.images_subfolder_for(LIBRARY_NAME) == "cli"
