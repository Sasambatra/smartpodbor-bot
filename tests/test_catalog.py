import json
from importlib.resources import files

import pytest

from smartphone_bot.catalog import CatalogError, load_catalog


@pytest.fixture
def document():
    return json.loads(files("smartphone_bot").joinpath("data/phones.json").read_text("utf-8"))


def save_catalog(tmp_path, document):
    path = tmp_path / "phones.json"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def test_custom_catalog_matches_bundled_catalog(tmp_path, document):
    assert load_catalog(save_catalog(tmp_path, document)) == load_catalog()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("price_rub", "10000"),
        ("price_rub", True),
        ("price_rub", -100),
        ("nfc", "false"),
        ("esim", 1),
        ("camera", 11),
        ("ram_gb", -1),
        ("storage_gb", 64),
        ("screen_inches", "6.1"),
        ("screen_inches", False),
        ("strengths", "Good camera"),
        ("caveats", []),
        ("name", ""),
        ("source_url", "https:"),
        ("source_url", "https://user:password@example.com"),
        ("source_url", "javascript:alert(1)"),
        ("brand", "unknown"),
        ("id", "../unsafe"),
    ],
)
def test_invalid_specs_fail_before_recommendation(tmp_path, document, field, value):
    document["phones"][0][field] = value
    with pytest.raises(CatalogError):
        load_catalog(save_catalog(tmp_path, document))


def test_duplicate_configurations_are_rejected(tmp_path, document):
    document["phones"].append(document["phones"][0])
    with pytest.raises(CatalogError, match="Duplicate"):
        load_catalog(save_catalog(tmp_path, document))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("phones", []),
        ("phones", {}),
        ("price_note", ""),
        ("specs_checked_on", "not-a-date"),
    ],
)
def test_invalid_catalog_metadata_is_rejected(tmp_path, document, field, value):
    document[field] = value
    with pytest.raises(CatalogError):
        load_catalog(save_catalog(tmp_path, document))


def test_missing_corrupt_and_non_utf8_files_have_clear_errors(tmp_path):
    path = tmp_path / "phones.json"
    with pytest.raises(CatalogError, match="Cannot read catalog"):
        load_catalog(path)
    for content in (b'{"phones": [', b"\xff\xfe\x00"):
        path.write_bytes(content)
        with pytest.raises(CatalogError, match="Cannot read catalog"):
            load_catalog(path)


def test_missing_phone_fields_are_reported_as_catalog_errors(tmp_path, document):
    del document["phones"][0]["chipset"]
    with pytest.raises(CatalogError, match="schema"):
        load_catalog(save_catalog(tmp_path, document))
