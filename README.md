<img src="docs/assets/bot-avatar.png" width="96" alt="SmartPodbor smartphone mascot" align="right" />

# SmartPodbor · СмартПодбор

**A Russian-language Telegram bot that turns eight answers into an explained smartphone shortlist.**

Python 3.11–3.14 · aiogram 3 · SQLite · pytest · Docker · MIT

[![CI](https://github.com/Sasambatra/smartpodbor-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Sasambatra/smartpodbor-bot/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%E2%80%933.14-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Repository:** [Sasambatra/smartpodbor-bot](https://github.com/Sasambatra/smartpodbor-bot)

[Русская инструкция](docs/README.ru.md) · [Architecture](docs/architecture.md) · [Portfolio case study](docs/portfolio.md) · [Validation](docs/validation.md)

[Publishing guide](docs/publishing.md) · [Contributing](CONTRIBUTING.md)

[Описание для резюме](docs/resume.ru.md) · [Resume project entry](docs/resume.en.md)

[Карточка проекта PDF](docs/resume-project.ru.pdf) · [Редактируемая версия DOCX](docs/resume-project.ru.docx)

Telegram-бот на Python: восемь вопросов, объяснимый подбор смартфонов,
сохранение прогресса в SQLite и ссылки на российские маркетплейсы.

![Offline illustration of the real questionnaire and a POCO X7 Pro recommendation](docs/assets/chat-preview.svg)

*Generated from the actual questionnaire, catalog, and ranking engine. This is an offline illustration, not a Telegram screenshot.*

## What it does

The bot asks about budget, operating system, intended use, screen size,
battery priority, storage, a required feature, and preferred brand. It returns
up to three different models with reasons, compromises, manufacturer references,
and search links to **Yandex Market, Ozon, and Wildberries**.

- Applies budget, OS, storage, and required features as mandatory filters.
- Ranks eligible phones using explicit, reproducible weights.
- Explains size, brand, camera, and battery trade-offs.
- Saves progress through process restarts; supports back, restart, and deletion.
- Rejects duplicate clicks and stale buttons; isolates each private chat.
- Includes a token-free CLI demo, tests, and generated demo assets.

The bundled catalog contains **16 models in 22 memory configurations**.
Prices are manual estimates; marketplace buttons open model/configuration
searches. Live offers, availability, and sellers are not verified.

## Try it without Telegram

On Linux, macOS, or Ubuntu in WSL:

```bash
git clone https://github.com/Sasambatra/smartpodbor-bot.git
cd smartpodbor-bot
./setup.sh
./run.sh --demo --example
```

`setup.sh` creates a project-local `.venv`, installs pinned dependencies, and
creates `.env` only when it is missing. It preserves an existing `.env`.

For an interactive questionnaire:

```bash
./run.sh --demo
```

The sample asks for an Android gaming phone under 40,000 ₽, battery priority,
at least 256 GB, and NFC for Mir Pay. Its first recommendation is **POCO X7 Pro
8/256 GB**, with an indicative catalog price of 32,000 ₽. See the
[complete generated transcript](docs/demo-example.txt).

Prefer manual setup?

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m smartphone_bot --demo --example
```

The installed `smartpodbor` command provides the same CLI.

## Connect to Telegram

1. Create a bot with [@BotFather](https://t.me/BotFather) using `/newbot`.
2. Open the local `.env` created by setup and set `BOT_TOKEN` to its token.
3. Run `./run.sh`, then open your bot in Telegram and send `/start`.

Keep the process running while using the bot. Only private chats are handled.
One polling process should use a given token. Startup registers the command
menu and removes a previous webhook without discarding pending updates.

In VS Code on Windows, use an **Ubuntu (WSL)** terminal for the shell scripts.
The repository includes offline-demo and live-bot debug configurations in
`.vscode/launch.json`, plus Python test discovery settings.

| Command | Behavior |
| --- | --- |
| `/start` | Welcome screen or resume an active survey |
| `/choose` | Start a fresh questionnaire |
| `/back` | Edit the previous answer; later answers are collected again |
| `/results` | Repeat the completed shortlist |
| `/cancel` | Stop and delete the saved session |
| `/help` | Usage instructions |
| `/privacy` | Explain local storage and deletion |

## Design

| Layer | Responsibility |
| --- | --- |
| `questions.py` | Single definition of questions, options, and accepted input |
| `catalog.py` | Typed model and strict validation of bundled or custom JSON |
| `recommendations.py` | Mandatory filters, weighted ranking, deduplication, URLs |
| `handlers.py` | Telegram navigation, callback validation, and recovery |
| `storage.py` | Async SQLite FSM backend, expiration, and transaction rollback |
| `presentation.py` | Russian explanations and result cards |
| `demo.py` | Offline questionnaire using the same engine |

The recommendation engine is independent of the Telegram transport. aiogram's
session event isolation and per-question nonces protect state transitions.
SQLite keeps the project simple to run on one host. The
[architecture write-up](docs/architecture.md) explains the scoring formula,
state transitions, persistence, and trade-offs.

## Configuration and catalog

| Variable | Default | Purpose |
| --- | --- | --- |
| `BOT_TOKEN` | empty | Required only for live Telegram mode |
| `DATABASE_PATH` | `data/smartpodbor.sqlite3` | Local session database |
| `SESSION_TTL_HOURS` | `24` | Session lifetime after the last modification, 1–720 hours |
| `LOG_LEVEL` | `INFO` | Python logging level |

Environment variables override `.env` in the current working directory.
`run.sh` changes to the project root automatically.

Edit `smartphone_bot/data/phones.json` or supply a custom catalog:

```bash
./run.sh --check
./run.sh --catalog path/to/phones.json --check
./run.sh --catalog path/to/phones.json --demo
```

[Catalog format and maintenance](docs/catalog.md) documents each field and
source requirements. Invalid catalogs produce a readable error before startup.

Sessions store Telegram IDs, answers, the current step, and an update time.
Expired rows are deleted on the next database operation. `/cancel` deletes the
session from the bot's database; Telegram message history is managed separately.
Logs redact the configured bot token, and settings representations omit it.
The bot makes no external AI requests.

## Development and checks

```bash
make dev                 # isolated setup plus locked development dependencies
make check               # lint, formatting, tests, coverage, catalog, demo assets
make demo                # reproducible offline example
make preview             # regenerate the SVG and text transcript
make build               # wheel + source archive and content checks
```

`pytest` runs domain, catalog, configuration, subprocess CLI, persistence,
and real-dispatcher conversation tests with a fake Telegram transport.
`make check` emits `coverage.xml`; subprocess coverage is included.

[GitHub Actions](.github/workflows/ci.yml) is configured to check Python 3.11
and 3.14, test the installed wheel away from source files, and build/run the
Docker demo without credentials. Check the [actual workflow runs](https://github.com/Sasambatra/smartpodbor-bot/actions)
for current status. See [observed local validation](docs/validation.md).

## Docker

With `.env` configured and Docker Compose installed:

```bash
docker compose up -d --build
docker compose logs -f bot
docker compose down
```

The runtime container uses a non-root user. SQLite persists in the `bot-data`
named volume. This deployment needs a token and an Internet connection; no
incoming port, public domain, PostgreSQL, or marketplace API key is required.
Docker is configured and smoke-tested by the CI workflow; local execution
status is recorded in the validation notes.

## Scope and limitations

- The catalog is a curated snapshot, with specification references checked on
  **2026-10-25**; it does not cover the entire smartphone market.
- Prices and 1–10 comparison ratings are editorial inputs, not live offers or
  laboratory results. A budget filter operates on those indicative prices.
- NFC, eSIM, battery, and SIM support can differ by regional version. The buyer
  must verify the exact configuration and seller terms.
- Mir Pay eligibility requires more than the Android/NFC filter; consult its
  [official compatibility guidance](https://pay.mironline.ru/help/).
- The current persistence and event isolation support one polling process;
  a distributed deployment needs a shared coordination design.
- Live Telegram connectivity and hosted uptime are separate from offline
  automated test results.

## Attribution and license

MIT licensed. The starting point was aiogram's
[official FSM questionnaire example](https://github.com/aiogram/aiogram/blob/v3.27.0/examples/finite_state_machine.py).
Its original source and license are preserved in `third_party/aiogram/`.

The smartphone questionnaire, catalog, recommendation policy, persistence,
marketplace links, offline demo, and project checks are project-specific
additions. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the
[case study](docs/portfolio.md) for the contribution boundary.
