# Upstream bot template

СмартПодбор основан на готовом примере бота с пошаговым опросом из проекта aiogram:

- Repository: https://github.com/aiogram/aiogram
- Pinned release: `v3.27.0`
- Original bot: https://github.com/aiogram/aiogram/blob/v3.27.0/examples/finite_state_machine.py
- Original license: https://github.com/aiogram/aiogram/blob/v3.27.0/LICENSE
- Copyright (c) 2017 - present Alex Root Junior
- License: MIT; полный текст сохранён в `third_party/aiogram/LICENSE`.

Копия исходного бота сохранена без изменений в
`third_party/aiogram/finite_state_machine.py`. Рабочая версия переработана в
`smartphone_bot/handlers.py` и `smartphone_bot/__main__.py`: вместо вопросов
из примера добавлены русскоязычная анкета, inline-кнопки, ранжирование
смартфонов, маркетплейсы, сохранение сессий и обработка ошибок.

Выполнение использует aiogram 3.31.0. Остальные зависимости перечислены
в `requirements.lock` и распространяются на условиях своих лицензий.

Характеристики каталога изложены своими словами; первоисточники производителей
указаны у каждой модели. Ориентировочные цены и сравнительные оценки заданы
автором проекта и не получены из API магазинов.

The portfolio avatar in `docs/assets/bot-avatar.png` is reused unchanged from
the existing project asset `output/imagegen/telegram-phone-quiz-avatar.png`.
The SVG chat preview is rendered by `scripts/export_demo.py` from the project
questionnaire and recommendation output; it is not a Telegram screenshot.
