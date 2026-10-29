"""Verify distributable contents without unpacking files or reading local secrets."""

import argparse
from pathlib import Path, PurePosixPath
from tarfile import open as open_tar
from zipfile import ZipFile


def check_paths(names: list[str]) -> None:
    for name in names:
        path = PurePosixPath(name)
        if (
            path.is_absolute()
            or any(part in {".env", ".local", ".venv", "__pycache__", ".."} for part in path.parts)
            or ".sqlite3" in path.name
            or (path.name.startswith(".env.") and path.name != ".env.example")
            or path.name.endswith(".pyc")
        ):
            raise ValueError(f"Unexpected private or generated file in distribution: {name}")


def check_distributions(directory: Path) -> None:
    wheels = list(directory.glob("*.whl"))
    sources = list(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError("Expected exactly one wheel and one source archive; clean dist/ first")
    with ZipFile(wheels[0]) as archive:
        names = archive.namelist()
    check_paths(names)
    for suffix in (
        "smartphone_bot/data/phones.json",
        "/licenses/LICENSE",
        "/licenses/third_party/aiogram/LICENSE",
        "/licenses/THIRD_PARTY_NOTICES.md",
        "/entry_points.txt",
    ):
        if not any(name.endswith(suffix) for name in names):
            raise ValueError(f"Wheel is missing {suffix}")
    with open_tar(sources[0], "r:gz") as archive:
        names = archive.getnames()
    check_paths(names)
    for suffix in (
        "/README.md",
        "/pyproject.toml",
        "/docs/assets/chat-preview.svg",
        "/third_party/aiogram/LICENSE",
        "/.env.example",
        "/.dockerignore",
        "/.github/workflows/ci.yml",
    ):
        if not any(name.endswith(suffix) for name in names):
            raise ValueError(f"Source archive is missing {suffix}")
    print(
        "Distribution checks passed: catalog, entry point, docs, licenses; no local credentials or database"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        check_distributions(args.directory)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Distribution check failed: {error}\n")


if __name__ == "__main__":
    main()
