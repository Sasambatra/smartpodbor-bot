from dataclasses import dataclass
from urllib.parse import urlencode

from smartphone_bot.catalog import Phone
from smartphone_bot.questions import QUESTIONS, valid_answer


@dataclass(frozen=True)
class Preferences:
    budget: int
    os: str
    purpose: str
    size: str
    battery: str
    storage: int
    feature: str
    brand: str

    @classmethod
    def from_answers(cls, answers: dict[str, str]) -> "Preferences":
        for question in QUESTIONS:
            if question.key not in answers or not valid_answer(
                question, str(answers[question.key])
            ):
                raise ValueError(f"Invalid or missing answer: {question.key}")
        return cls(
            **{**answers, "budget": int(answers["budget"]), "storage": int(answers["storage"])}
        )


@dataclass(frozen=True)
class Recommendation:
    phone: Phone
    score: float
    reasons: tuple[str, ...]
    compromises: tuple[str, ...]


def marketplace_links(phone: Phone) -> dict[str, str]:
    return {
        "Яндекс Маркет": "https://market.yandex.ru/search?"
        + urlencode({"text": phone.search_query}),
        "Ozon": "https://www.ozon.ru/search/?" + urlencode({"text": phone.search_query}),
        "Wildberries": "https://www.wildberries.ru/catalog/0/search.aspx?"
        + urlencode({"search": phone.search_query}),
    }


def meets_requirements(
    phone: Phone, preferences: Preferences, *, check_budget: bool = True
) -> bool:
    return (
        (not check_budget or phone.price_rub <= preferences.budget)
        and (preferences.os == "any" or phone.os == preferences.os)
        and phone.storage_gb >= preferences.storage
        and (preferences.feature != "mir" or (phone.os == "android" and phone.nfc))
        and (preferences.feature != "water" or phone.ip_rating in {"IP67", "IP68"})
        and (preferences.feature != "esim" or phone.esim)
    )


def _rank(phone: Phone, preferences: Preferences) -> Recommendation:
    weights = {"camera": 2, "performance": 2, "endurance": 2, "screen": 1, "software": 2}
    weights.update(
        {
            "everyday": {"software": 4, "endurance": 3},
            "camera": {"camera": 9, "screen": 2},
            "gaming": {"performance": 10, "screen": 3},
            "work": {"performance": 4, "software": 6, "endurance": 3},
        }[preferences.purpose]
    )
    if preferences.battery == "high":
        weights["endurance"] += 7
    score = sum(getattr(phone, key) * weight for key, weight in weights.items()) / sum(
        weights.values()
    )
    reasons = [phone.strengths[0]]
    compromises = list(phone.caveats)
    if preferences.purpose == "camera":
        if phone.camera >= 8:
            reasons.append("Камера — сильная сторона модели в этом каталоге")
        else:
            compromises.append("Для сложного света и видео камера — компромисс")
    elif preferences.purpose == "gaming":
        if phone.performance >= 8:
            reasons.append(f"Производительный чип: {phone.chipset}")
        else:
            compromises.append("Тяжёлые игры потребуют снижения настроек графики")
    elif preferences.purpose == "work":
        reasons.append(f"Встроенная память {phone.storage_gb} ГБ для файлов и приложений")
    if preferences.battery == "high":
        if phone.endurance >= 8:
            reasons.append("Высокая оценка автономности в каталоге")
        else:
            compromises.append("Автономность уступает моделям с упором на батарею")
    compact = phone.screen_inches <= 6.4
    large = phone.screen_inches >= 6.65
    if preferences.size != "any":
        size_match = compact if preferences.size == "compact" else large
        score += 1.4 if size_match else -1.4
        if size_match:
            reasons.append("Размер экрана соответствует пожеланию")
        else:
            compromises.append(f"Экран {phone.screen_inches:g}″ — другой размер, чем вы предпочли")
    if preferences.brand != "any":
        if phone.brand == preferences.brand:
            score += 0.8
            reasons.append("Предпочитаемая марка")
        else:
            compromises.append("Другая марка: остальные условия соблюдены")
    # Small value bonus; a larger budget is a ceiling, not a target to spend.
    score += 0.5 * (1 - phone.price_rub / preferences.budget)
    if preferences.feature == "mir":
        reasons.append("Android с NFC; совместимость версии и банка с Mir Pay нужно проверить")
    elif preferences.feature == "water":
        reasons.append(f"Защита корпуса {phone.ip_rating}")
    elif preferences.feature == "esim":
        reasons.append("Есть версия с eSIM — проверьте региональный номер модели")
    return Recommendation(
        phone, round(score, 3), tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(compromises))
    )


def recommend(
    phones: tuple[Phone, ...], preferences: Preferences, limit: int = 3
) -> tuple[Recommendation, ...]:
    ranked = sorted(
        (_rank(phone, preferences) for phone in phones if meets_requirements(phone, preferences)),
        key=lambda item: (-item.score, item.phone.price_rub, item.phone.id),
    )
    chosen = []
    seen_models = set()
    for item in ranked:
        if item.phone.name not in seen_models:
            chosen.append(item)
            seen_models.add(item.phone.name)
        if len(chosen) >= limit:
            break
    return tuple(chosen) if limit > 0 else ()


def no_results_explanation(phones: tuple[Phone, ...], preferences: Preferences) -> str:
    if preferences.os == "ios" and preferences.feature == "mir":
        return "Mir Pay не работает на iPhone. Выберите Android или уберите требование оплаты Мир."
    matching = [
        phone for phone in phones if meets_requirements(phone, preferences, check_budget=False)
    ]
    if matching:
        minimum = min(phone.price_rub for phone in matching)
        formatted = f"{minimum:,}".replace(",", " ")
        return f"Модели с этой системой, памятью и обязательной функцией есть в каталоге примерно от {formatted} ₽. Увеличьте бюджет или измените условия."
    return "В небольшом каталоге нет сочетания этой системы, объёма памяти и обязательной функции. Измените одно из этих условий."
