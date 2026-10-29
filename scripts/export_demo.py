"""Render portfolio assets from the real questionnaire and recommendation engine."""

import argparse
from contextlib import redirect_stdout
from html import escape
from io import StringIO
from pathlib import Path
from textwrap import wrap

from smartphone_bot.catalog import Catalog, load_catalog
from smartphone_bot.demo import EXAMPLE_ANSWERS, run_demo
from smartphone_bot.presentation import rubles
from smartphone_bot.questions import QUESTIONS
from smartphone_bot.recommendations import Preferences, recommend

ROOT = Path(__file__).resolve().parents[1]


def render_preview(catalog: Catalog) -> str:
    item = recommend(catalog.phones, Preferences.from_answers(EXAMPLE_ANSWERS))[0]
    phone = item.phone
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="860" viewBox="0 0 1280 860" role="img" aria-labelledby="title desc">',
        '<title id="title">СмартПодбор — questionnaire and recommendation preview</title>',
        '<desc id="desc">Offline illustration generated from actual questions and a gaming recommendation. Prices are indicative, not live offers.</desc>',
        '<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#101427"/><stop offset="1" stop-color="#20204a"/></linearGradient></defs>',
        '<rect width="1280" height="860" rx="28" fill="url(#bg)"/>',
        '<g font-family="DejaVu Sans,Arial,sans-serif">',
    ]

    def rect(x, y, width, height, color, radius=12, stroke=None):
        border = f' stroke="{stroke}"' if stroke else ""
        elements.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{color}"{border}/>'
        )

    def text(x, y, value, size=18, color="#e8ebff", weight="400"):
        elements.append(
            f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}">{escape(str(value))}</text>'
        )

    def paragraph(x, y, value, width, size=17, color="#bdc7e5", spacing=25):
        for line in wrap(value, width=width):
            text(x, y, line, size, color)
            y += spacing
        return y

    rect(40, 35, 62, 62, "#a899ff", 18)
    text(53, 75, "СП", 24, "#15172d", "700")
    text(122, 78, "СмартПодбор", 43, weight="700")
    text(42, 128, "A smartphone decision, explained. Built for a conversation.", 23, "#bdc7e5")
    for x, width, label in (
        (40, 170, "8 questions"),
        (224, 230, f"{len({p.name for p in catalog.phones})} phone models"),
        (468, 235, "3 marketplaces"),
    ):
        rect(x, 153, width, 34, "#2b3153", 17)
        text(x + 17, 176, label, 16)
    text(1025, 176, "OFFLINE PREVIEW", 15, "#c7bfff", "700")

    rect(40, 213, 420, 574, "#171d34", 20, "#3c4265")
    text(65, 253, "01 / Вопросы в чате", 21, weight="700")
    rect(65, 274, 370, 39, "#333b65")
    text(80, 300, "Android · до 40 000 ₽", 17)
    text(65, 350, "Вопрос 3 из 8", 15, "#b2a7ff", "700")
    question = QUESTIONS[2]
    paragraph(65, 386, question.title, 30, size=22, color="#f4f5ff", spacing=29)
    for index, option in enumerate(question.options):
        y = 446 + index * 52
        chosen = option.value == EXAMPLE_ANSWERS[question.key]
        label = option.label.split(" ", 1)[1] if " " in option.label else option.label
        rect(65, y, 370, 42, "#9b8afc" if chosen else "#29314f", 9)
        text(80, y + 27, label, 16, "#10142a" if chosen else "#e8ebff", "700" if chosen else "400")
    text(65, 688, "← Назад", 16, "#b2a7ff")
    text(350, 688, "Отмена", 16, "#b2a7ff")
    paragraph(65, 733, "Ответы сохраняются между перезапусками.", 35, size=15, spacing=21)

    rect(486, 213, 754, 574, "#171d34", 20, "#3c4265")
    text(512, 253, "02 / Основной вариант", 21, weight="700")
    text(512, 301, f"{phone.name} · {phone.configuration}", 28, weight="700")
    text(512, 342, f"≈ {rubles(phone.price_rub)}", 27, "#b5f1d3", "700")
    text(512, 372, f"{phone.screen_inches:g}″ · {phone.display} · {phone.battery_mah} мА·ч", 16)
    text(512, 399, f"{phone.chipset} · {phone.ip_rating}", 16, "#bdc7e5")
    text(512, 445, "Почему подходит", 18, weight="700")
    y = 477
    for reason in item.reasons[:2]:
        y = paragraph(512, y, "✓ " + reason, 68, size=16, spacing=23) + 8
    text(512, 592, "Что учесть", 18, weight="700")
    paragraph(512, 621, item.compromises[0], 70, size=16, spacing=23)
    for x, label in ((512, "Яндекс Маркет"), (746, "Ozon"), (980, "Wildberries")):
        rect(x, 679, 208, 42, "#38325f", 9, "#7266ab")
        text(x + 17, 706, label, 16, "#e2dbff", "700")
    text(512, 759, "Ориентировочные цены · Ссылки открывают поиск", 15, "#b7c1df")
    text(
        40,
        826,
        "Generated from the real catalog and ranking engine. An illustration, not a Telegram screenshot.",
        16,
        "#c4c9e3",
    )
    elements.append("</g></svg>\n")
    return "\n".join(elements)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when generated assets are stale")
    args = parser.parse_args()
    catalog = load_catalog()
    output = StringIO()
    with redirect_stdout(output):
        run_demo(catalog, example=True)
    artifacts = {
        ROOT / "docs/assets/chat-preview.svg": render_preview(catalog),
        ROOT / "docs/demo-example.txt": output.getvalue(),
    }
    for path, content in artifacts.items():
        if args.check:
            if not path.exists() or path.read_text("utf-8") != content:
                parser.exit(1, f"Stale demo asset: {path.name}. Run make preview.\n")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print(
        "Demo artifacts are current"
        if args.check
        else "Generated SVG chat preview and example transcript"
    )


if __name__ == "__main__":
    main()
