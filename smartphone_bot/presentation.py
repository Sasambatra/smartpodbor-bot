from html import escape

from smartphone_bot.catalog import Catalog
from smartphone_bot.questions import QUESTIONS, answer_label
from smartphone_bot.recommendations import Recommendation


def rubles(amount: int) -> str:
    return f"{amount:,} ₽".replace(",", " ")


def summary_text(answers: dict[str, str], catalog: Catalog) -> str:
    summary = "\n".join(
        f"• {escape(answer_label(question, answers[question.key]))}" for question in QUESTIONS
    )
    return (
        "<b>🎯 Ваша подборка</b>\n\n"
        f"{summary}\n\n"
        "Ниже — до трёх разных моделей, которые проходят обязательные условия. "
        "Размер, автономность и марку учитываю как пожелания.\n\n"
        f"<b>Цены ориентировочные.</b> {escape(catalog.price_note)} "
        "Кнопки открывают поиск модели и памяти на маркетплейсах, а не проверенные предложения продавцов.\n"
        f"Характеристики сверены: {catalog.specs_checked_on:%d.%m.%Y}. "
        "Оценки для сравнения — редакционные, не результаты лабораторных тестов."
    )


def recommendation_text(item: Recommendation, rank: int) -> str:
    phone = item.phone
    heading = ("🥇 Основной вариант", "🥈 Альтернатива", "🥉 Ещё один вариант")[rank - 1]
    battery = f" · {phone.battery_mah} мА·ч" if phone.battery_mah else ""
    charging = f" · до {phone.charging_w} Вт" if phone.charging_w else ""
    reasons = "\n".join(f"✓ {escape(reason)}" for reason in item.reasons)
    compromises = "\n".join(f"• {escape(caveat)}" for caveat in item.compromises)
    payment_note = (
        "\n💳 Apple Pay с российскими картами и Mir Pay на iPhone недоступны."
        if phone.os == "ios"
        else ""
    )
    return (
        f"<b>{heading}</b>\n<b>{escape(phone.name)} · {phone.configuration}</b>\n"
        f"Ориентир: <b>≈ {rubles(phone.price_rub)}</b>\n\n"
        f"{phone.screen_inches:g}″ · {escape(phone.display)}{battery}{charging}\n"
        f"{escape(phone.chipset)} · {phone.ip_rating}\n\n"
        f"<b>Почему подходит</b>\n{reasons}\n\n"
        f"<b>Что учесть</b>\n{compromises}{payment_note}\n\n"
        f'<a href="{escape(phone.source_url, quote=True)}">Характеристики производителя</a>'
    )


BUYING_TIPS = (
    "<b>Перед покупкой</b>\n"
    "Проверьте точную модель, память, региональную версию, NFC/eSIM, "
    "рейтинг продавца, гарантию и итоговую цену с доставкой и возможной пошлиной. "
    "Защита IP не означает гарантию от повреждений водой.\n\n"
    '<a href="https://pay.mironline.ru/help/">Совместимость и условия Mir Pay</a>\n\n'
    "Изменить последний ответ: /back. Новая подборка: /choose. "
    "Удалить сохранённые ответы: /cancel."
)
