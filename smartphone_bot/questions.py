"""One questionnaire shared by Telegram, the terminal demo, and validation."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Option:
    value: str
    label: str


@dataclass(frozen=True)
class Question:
    key: str
    title: str
    hint: str
    options: tuple[Option, ...]


QUESTIONS = (
    Question(
        "budget",
        "Сколько готовы потратить?",
        "Это верхняя граница в рублях. Можно написать точную сумму: 35000 или 35 тыс.",
        tuple(
            Option(str(amount), f"До {amount:,} ₽".replace(",", " "))
            for amount in (15000, 25000, 40000, 60000, 100000, 200000)
        ),
    ),
    Question(
        "os",
        "Какая система вам подходит?",
        "Это обязательное условие.",
        (
            Option("any", "Любая"),
            Option("android", "Только Android"),
            Option("ios", "Только iPhone"),
        ),
    ),
    Question(
        "purpose",
        "Для чего смартфон в первую очередь?",
        "По этому ответу расставлю приоритеты при сравнении.",
        (
            Option("everyday", "💬 Общение и повседневные дела"),
            Option("camera", "📸 Фото и видео"),
            Option("gaming", "🎮 Игры"),
            Option("work", "💼 Работа и несколько приложений"),
        ),
    ),
    Question(
        "size",
        "Какой размер экрана удобнее?",
        "Учту как пожелание. Если придётся уступить в размере, напишу об этом.",
        (
            Option("any", "Размер не важен"),
            Option("compact", "Компактный — до 6,4″"),
            Option("large", "Большой — от 6,65″"),
        ),
    ),
    Question(
        "battery",
        "Насколько важна автономность?",
        "Ёмкость аккумулятора сама по себе не определяет время работы.",
        (
            Option("normal", "Обычный день, заряжаю вечером"),
            Option("high", "🔋 Автономность — один из приоритетов"),
        ),
    ),
    Question(
        "storage",
        "Сколько встроенной памяти нужно?",
        "Минимальный объём. Это обязательное условие; карту памяти не учитываю.",
        (
            Option("128", "От 128 ГБ — обычное использование"),
            Option("256", "От 256 ГБ — много фото и приложений"),
            Option("512", "От 512 ГБ — видео и большие игры"),
        ),
    ),
    Question(
        "feature",
        "Есть обязательная функция?",
        "Для оплаты через Mir Pay нужен Android с NFC. Наличие eSIM и NFC зависит от версии.",
        (
            Option("any", "Нет обязательной функции"),
            Option("mir", "💳 Оплата Мир через Mir Pay"),
            Option("water", "💧 Защита IP67 / IP68"),
            Option("esim", "📶 eSIM"),
        ),
    ),
    Question(
        "brand",
        "Есть любимая марка?",
        "Это предпочтение: другие марки тоже могут попасть в подборку. Система важнее марки.",
        (
            Option("any", "Любая — главное, чтобы подходил"),
            Option("samsung", "Samsung"),
            Option("xiaomi", "Xiaomi / Redmi / POCO"),
            Option("apple", "Apple"),
            Option("honor", "HONOR"),
            Option("google", "Google Pixel"),
        ),
    ),
)


def parse_budget(text: str) -> int | None:
    normalized = text.casefold().strip().replace("ё", "е")
    normalized = re.sub(r"\s+", "", normalized)
    match = re.fullmatch(r"(\d+(?:[.,]\d+)?)(тыс\.?|[kк])?(?:₽|руб\.?|рублей|р\.?)?", normalized)
    if not match:
        return None
    amount = float(match[1].replace(",", ".")) * (1000 if match[2] else 1)
    if not amount.is_integer() or not 5000 <= amount <= 500000:
        return None
    return int(amount)


def valid_answer(question: Question, value: str) -> bool:
    if question.key == "budget":
        return value.isdecimal() and 5000 <= int(value) <= 500000
    return value in {option.value for option in question.options}


def answer_label(question: Question, value: str) -> str:
    if question.key == "budget":
        return f"до {int(value):,} ₽".replace(",", " ")
    return next(option.label for option in question.options if option.value == value)
