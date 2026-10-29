from dataclasses import replace
from itertools import product
from urllib.parse import parse_qs, urlsplit

import pytest

from smartphone_bot.catalog import load_catalog
from smartphone_bot.demo import EXAMPLE_ANSWERS
from smartphone_bot.presentation import recommendation_text, summary_text
from smartphone_bot.questions import QUESTIONS, parse_budget
from smartphone_bot.recommendations import (
    Preferences,
    marketplace_links,
    no_results_explanation,
    recommend,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("35000", 35000),
        ("35 000 ₽", 35000),
        ("35 тыс.", 35000),
        ("35к", 35000),
        ("35.5k", 35500),
        ("35,5 тыс рублей", 35500),
        ("5000", 5000),
        ("500000", 500000),
        ("4999", None),
        ("500001", None),
        ("-50000", None),
        ("<script>", None),
        ("1e6", None),
        ("nan", None),
        ("35.1", None),
        ("пять тысяч", None),
        ("", None),
    ],
)
def test_budget_parser(text, expected):
    assert parse_budget(text) == expected


def test_all_budget_os_storage_and_feature_combinations_keep_hard_constraints():
    catalog = load_catalog()
    base = Preferences.from_answers(EXAMPLE_ANSWERS)
    for budget, os, storage, feature in product(
        (15000, 40000, 200000),
        ("any", "android", "ios"),
        (128, 256, 512),
        ("any", "mir", "water", "esim"),
    ):
        preferences = replace(base, budget=budget, os=os, storage=storage, feature=feature)
        results = recommend(catalog.phones, preferences)
        assert len(results) <= 3
        assert len({item.phone.name for item in results}) == len(results)
        for item in results:
            phone = item.phone
            assert phone.price_rub <= budget
            assert phone.storage_gb >= storage
            assert os == "any" or phone.os == os
            assert feature != "mir" or (phone.os == "android" and phone.nfc)
            assert feature != "water" or phone.ip_rating in {"IP67", "IP68"}
            assert feature != "esim" or phone.esim


def test_gaming_example_prioritizes_poco_and_deduplicates_storage_variants():
    result = recommend(load_catalog().phones, Preferences.from_answers(EXAMPLE_ANSWERS))
    assert result[0].phone.name == "POCO X7 Pro"
    assert result[0].phone.storage_gb == 256
    assert len({item.phone.name for item in result}) == 3


def test_purpose_and_size_change_the_top_pick():
    catalog = load_catalog()
    camera = Preferences.from_answers(
        {
            **EXAMPLE_ANSWERS,
            "budget": "60000",
            "purpose": "camera",
            "size": "compact",
            "battery": "normal",
            "storage": "128",
            "feature": "any",
        }
    )
    assert recommend(catalog.phones, camera)[0].phone.name == "Google Pixel 9a"
    gaming = replace(camera, purpose="gaming", size="large")
    assert recommend(catalog.phones, gaming)[0].phone.name == "POCO X7 Pro"


def test_impossible_iphone_mir_combination_has_actionable_explanation():
    catalog = load_catalog()
    preferences = replace(Preferences.from_answers(EXAMPLE_ANSWERS), os="ios", budget=200000)
    assert recommend(catalog.phones, preferences) == ()
    assert "Mir Pay не работает на iPhone" in no_results_explanation(catalog.phones, preferences)


def test_low_budget_has_no_over_budget_fallback():
    catalog = load_catalog()
    preferences = replace(Preferences.from_answers(EXAMPLE_ANSWERS), budget=5000, feature="any")
    assert not recommend(catalog.phones, preferences)
    assert "примерно от" in no_results_explanation(catalog.phones, preferences)


def test_urls_preserve_exact_model_configuration_and_no_telegram_data():
    for phone in load_catalog().phones:
        links = marketplace_links(phone)
        assert len(links) == 3
        for url in links.values():
            parsed = urlsplit(url)
            assert parsed.scheme == "https"
            assert parsed.hostname in {"market.yandex.ru", "www.ozon.ru", "www.wildberries.ru"}
            parameters = parse_qs(parsed.query)
            assert list(parameters) in [["text"], ["search"]]
            assert next(iter(parameters.values())) == [phone.search_query]
            assert str(phone.storage_gb) in phone.search_query


def test_bad_answers_are_rejected():
    with pytest.raises(ValueError, match="os"):
        Preferences.from_answers({**EXAMPLE_ANSWERS, "os": "windows"})
    with pytest.raises(ValueError, match="budget"):
        Preferences.from_answers(
            {key: value for key, value in EXAMPLE_ANSWERS.items() if key != "budget"}
        )


def test_telegram_messages_and_callback_payloads_fit_limits():
    from smartphone_bot.handlers import question_keyboard

    catalog = load_catalog()
    assert len(summary_text(EXAMPLE_ANSWERS, catalog)) < 4096
    preferences = replace(Preferences.from_answers(EXAMPLE_ANSWERS), budget=500000)
    for phone in catalog.phones:
        from smartphone_bot.recommendations import _rank

        item = _rank(phone, preferences)
        assert len(recommendation_text(item, 1)) < 4096
    for index, _ in enumerate(QUESTIONS):
        markup = question_keyboard(index, "01234567")
        for row in markup.inline_keyboard:
            for button in row:
                assert 1 <= len(button.callback_data.encode()) <= 64
