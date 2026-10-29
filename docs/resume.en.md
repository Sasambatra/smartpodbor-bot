# SmartPodbor — resume project entry

**SmartPodbor — Telegram Smartphone Advisor**  
Portfolio project · October 2026

**Source:** [Sasambatra/smartpodbor-bot](https://github.com/Sasambatra/smartpodbor-bot)

**Technologies:** Python, asyncio, aiogram 3, SQLite, aiosqlite, pytest,
pytest-asyncio, Ruff, Docker, GitHub Actions.

- Built an eight-question conversation that returns up to three smartphone
  recommendations, explanations, trade-offs, and marketplace search links.
- Implemented mandatory requirement filters, weighted ranking, and validated
  JSON catalog input with clear failures for malformed configuration data.
- Added persistent SQLite FSM sessions, expiration, backward navigation,
  per-session event isolation, and stale-callback protection.
- Added 82 automated tests with 86.42% combined statement/branch coverage in
  local validation, an offline CLI demo, Docker configuration, and a CI workflow
  targeting Python 3.11 and 3.14.

The project adapts aiogram's MIT-licensed FSM example; upstream attribution
is retained. Prices are indicative, marketplace links open searches, and
automated tests use a fake Telegram transport. Commercial usage, hosted uptime,
and GitHub CI success are not claimed without supporting evidence.
