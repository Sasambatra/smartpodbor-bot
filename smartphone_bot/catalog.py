import json
import re
from dataclasses import dataclass
from datetime import date
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Phone:
    id: str
    name: str
    brand: str
    os: str
    ram_gb: int | None
    storage_gb: int
    price_rub: int
    screen_inches: float
    display: str
    chipset: str
    battery_mah: int | None
    charging_w: int | None
    nfc: bool
    esim: bool
    ip_rating: str
    camera: int
    performance: int
    endurance: int
    screen: int
    software: int
    strengths: tuple[str, ...]
    caveats: tuple[str, ...]
    source_url: str
    search_query: str

    @property
    def configuration(self) -> str:
        return f"{self.ram_gb}/{self.storage_gb} ГБ" if self.ram_gb else f"{self.storage_gb} ГБ"


@dataclass(frozen=True)
class Catalog:
    specs_checked_on: date
    price_note: str
    phones: tuple[Phone, ...]


class CatalogError(ValueError):
    """An invalid or unreadable catalog that can be reported without a traceback."""


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_phone(item: object) -> Phone:
    if not isinstance(item, dict):
        raise CatalogError("Each phone must be a JSON object")
    for key in ("strengths", "caveats"):
        values = item.get(key)
        if not isinstance(values, list) or not values or not all(_text(value) for value in values):
            raise CatalogError(f"{key} must be a nonempty array of strings")
    try:
        phone = Phone(
            **{**item, "strengths": tuple(item["strengths"]), "caveats": tuple(item["caveats"])}
        )
    except TypeError as error:
        raise CatalogError("Phone fields do not match the documented schema") from error
    for key in (
        "id",
        "name",
        "brand",
        "os",
        "display",
        "chipset",
        "ip_rating",
        "source_url",
        "search_query",
    ):
        if not _text(getattr(phone, key)):
            raise CatalogError(f"{key} must be a nonempty string")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", phone.id):
        raise CatalogError("Phone IDs must use lowercase letters, digits, and hyphens")
    if phone.os not in {"android", "ios"} or phone.brand not in {
        "xiaomi",
        "samsung",
        "honor",
        "google",
        "apple",
    }:
        raise CatalogError(f"Invalid phone classification: {phone.id}")
    for key in (
        "price_rub",
        "storage_gb",
        "camera",
        "performance",
        "endurance",
        "screen",
        "software",
    ):
        if type(getattr(phone, key)) is not int:
            raise CatalogError(f"{phone.id}/{key} must be an integer")
    for key in ("ram_gb", "battery_mah", "charging_w"):
        value = getattr(phone, key)
        if value is not None and (type(value) is not int or value <= 0):
            raise CatalogError(f"{phone.id}/{key} must be a positive integer or null")
    if type(phone.nfc) is not bool or type(phone.esim) is not bool:
        raise CatalogError(f"{phone.id}: nfc and esim must be JSON booleans")
    if (
        phone.price_rub <= 0
        or phone.storage_gb < 128
        or type(phone.screen_inches) not in {float, int}
        or not 4 < phone.screen_inches < 9
    ):
        raise CatalogError(f"Invalid specifications: {phone.id}")
    for key in ("camera", "performance", "endurance", "screen", "software"):
        if not 1 <= getattr(phone, key) <= 10:
            raise CatalogError(f"Invalid editorial score: {phone.id}/{key}")
    try:
        url = urlsplit(phone.source_url)
        valid_url = (
            url.scheme == "https" and bool(url.hostname) and not url.username and not url.password
        )
    except ValueError:
        valid_url = False
    if not valid_url or any(character.isspace() for character in phone.source_url):
        raise CatalogError(
            f"{phone.id}: source_url must be an absolute HTTPS URL without credentials"
        )
    return phone


def load_catalog(path: Path | None = None) -> Catalog:
    """Load the bundled catalog, or validate an explicit file before starting the bot."""
    source = path if path is not None else files("smartphone_bot").joinpath("data/phones.json")
    try:
        document = json.loads(source.read_text("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CatalogError("Cannot read catalog: provide an existing UTF-8 JSON file") from error
    if not isinstance(document, dict):
        raise CatalogError("The catalog must be a JSON object")
    if not _text(document.get("price_note")):
        raise CatalogError("price_note must explain how the indicative prices were obtained")
    try:
        checked_on = date.fromisoformat(document["specs_checked_on"])
    except (KeyError, TypeError, ValueError) as error:
        raise CatalogError("specs_checked_on must be an ISO date: YYYY-MM-DD") from error
    if not isinstance(document.get("phones"), list) or not document["phones"]:
        raise CatalogError("phones must be a nonempty array")
    phones = []
    seen = set()
    for item in document["phones"]:
        phone = _validate_phone(item)
        if phone.id in seen:
            raise CatalogError(f"Duplicate phone ID: {phone.id}")
        seen.add(phone.id)
        phones.append(phone)
    return Catalog(checked_on, document["price_note"], tuple(phones))
