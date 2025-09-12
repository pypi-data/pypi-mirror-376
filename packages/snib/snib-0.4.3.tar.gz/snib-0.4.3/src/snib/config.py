from importlib import resources
from pathlib import Path

import toml

from . import presets  # reference to snib.presets
from .logger import logger

SNIB_DEFAULT_CONFIG = {
    "config": {
        "description": "Default snibconfig.toml",
        "author": "patmllr",
        "version": "1.0",
    },
    "project": {"path": ".", "description": ""},
    "instruction": {
        "task": "",
        "task_dict": {
            "debug": "Debug: Analyze the code and highlight potential errors, bugs, or inconsistencies.",
            "comment": "Comment: Add comments or explain existing functions and code sections.",
            "refactor": "Refactor: Suggest refactorings to make the code cleaner, more readable, and maintainable.",
            "optimize": "Optimize: Improve efficiency or performance of the code.",
            "summarize": "Summarize: Provide a concise summary of the files or modules.",
            "document": "Document: Generate documentation for functions, classes, or modules.",
            "test": "Test: Create unit tests or test cases for the code.",
            "analyze": "Analyze: Perform static analysis or security checks on the code.",
        },
    },
    "filters": {
        "include": [],
        "exclude": [],
        "smart_include": [
            "*.py",
            "*.js",
            "*.ts",
            "*.java",
            "*.cpp",
            "*.c",
            "*.cs",
            "*.go",
            "*.rb",
            "*.php",
            "*.html",
            "*.css",
            "*.scss",
            "*.less",
            "*.json",
            "*.yaml",
            "*.yml",
            "*.xml",
            "*.sh",
            "*.bat",
            "*.ps1",
            "*.pl",
            "*.swift",
            "*.kt",
            "*.m",
            "*.r",
            "*.sql",
        ],
        "smart_exclude": [
            "*.log",
            "*.zip",
            "*.tar",
            "*.gz",
            "*.bin",
            "*.exe",
            "*.dll",
            "*.csv",
        ],
        "default_exclude": [
            "venv",
            "prompts",
            "__pycache__",
            ".git",
            "snibconfig.toml",
        ],
        "no_default_exclude": False,
        "smart": False,
    },
    "output": {
        "chunk_size": 30000,
        "force": False,
    },
    "ai": {
        "model": "gpt-4"
    },  # TODO: add for later use with APIs (delete this for now)!
}

SNIB_CONFIG_FILE = "snibconfig.toml"
SNIB_PROMPTS_DIR = "prompts"


def write_config(
    path: Path = Path(SNIB_CONFIG_FILE), content: str = SNIB_DEFAULT_CONFIG
):
    """
    Write a new snib configuration file in TOML format.

    If the file already exists, raises a FileExistsError.

    Args:
        path (Path, optional): Path to write the config file. Defaults to SNIB_CONFIG_FILE.
        content (dict, optional): Dictionary representing the configuration. Defaults to SNIB_DEFAULT_CONFIG.

    Raises:
        FileExistsError: If the config file already exists.
    """
    if path.exists():
        raise FileExistsError(f"{path} already exists.")
    toml.dump(
        content, path.open("w")
    )  # TODO: Trailing Comma -> clean dump for presets (needs fix) -> tomli-w, tomlkit


def load_config(path: Path = Path(SNIB_CONFIG_FILE)) -> dict:
    """
    Load a snib configuration from a TOML file.

    Args:
        path (Path, optional): Path to the config file. Defaults to SNIB_CONFIG_FILE.

    Returns:
        dict | None: Loaded configuration dictionary or None if the file does not exist.
    """
    if not path.exists():
        return None  # TODO: raise FileNotFoundError(f"{path} does not exist.") -> is there sense in returning None?
    return toml.load(path.open("r"))


def load_preset(name: str) -> dict:
    """
    Load a preset configuration from the built-in `presets`.

    Args:
        name (str): Name of the preset (without '.toml').

    Returns:
        dict: Preset configuration dictionary.

    Raises:
        ValueError: If the preset file does not exist in the `presets`.
    """
    preset_file = f"{name}.toml"
    try:
        with resources.open_text(presets, preset_file) as f:
            return toml.load(f)
    except FileNotFoundError:
        raise ValueError(f"Preset '{name}' not found")
