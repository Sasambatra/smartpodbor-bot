import re

from smartphone_bot.catalog import Catalog
from smartphone_bot.presentation import recommendation_text, summary_text
from smartphone_bot.questions import QUESTIONS, parse_budget
from smartphone_bot.recommendations import (
    Preferences,
    marketplace_links,
    no_results_explanation,
    recommend,
)

EXAMPLE_ANSWERS = {
    "budget": "40000",
    "os": "android",
    "purpose": "gaming",
    "size": "any",
    "battery": "high",
    "storage": "256",
    "feature": "mir",
    "brand": "any",
}


def plain_text(html: str) -> str:
    from html import unescape

    return unescape(re.sub(r"<[^>]+>", "", html))


def run_demo(catalog: Catalog, example: bool = False) -> None:
    print("📱 СмартПодбор — демо без Telegram и без токена\n")
    answers = {}
    if example:
        answers = EXAMPLE_ANSWERS.copy()
    else:
        for index, question in enumerate(QUESTIONS, 1):
            print(f"\n{index}/{len(QUESTIONS)}. {question.title}\n{question.hint}")
            for number, option in enumerate(question.options, 1):
                print(f"  {number}. {option.label}")
            while True:
                answer = input("Ваш ответ (номер варианта): ").strip()
                if answer.isdecimal() and 1 <= int(answer) <= len(question.options):
                    answers[question.key] = question.options[int(answer) - 1].value
                    break
                if question.key == "budget" and (budget := parse_budget(answer)) is not None:
                    answers[question.key] = str(budget)
                    break
                print(
                    "Введите номер варианта"
                    + (" или бюджет от 5000 до 500000 ₽." if question.key == "budget" else ".")
                )
    preferences = Preferences.from_answers(answers)
    print("\n" + plain_text(summary_text(answers, catalog)))
    results = recommend(catalog.phones, preferences)
    if not results:
        print("\nНет точного совпадения. " + no_results_explanation(catalog.phones, preferences))
    for rank, item in enumerate(results, 1):
        print("\n" + plain_text(recommendation_text(item, rank)))
        for marketplace, url in marketplace_links(item.phone).items():
            print(f"  {marketplace}: {url}")
