# Portfolio case study: SmartPodbor

## Project summary

A Russian-language Telegram assistant that turns eight answers into an
explainable smartphone shortlist with links to Ozon, Wildberries, and
Yandex Market. It combines an asynchronous conversation, persistent sessions,
and a deterministic recommendation policy in a small deployable Python app.

Repository: [Sasambatra/smartpodbor-bot](https://github.com/Sasambatra/smartpodbor-bot).

Resume-ready entries: [Russian](resume.ru.md) · [English](resume.en.md).

Repository description:

> Russian-language Telegram smartphone advisor with an explainable ranking
> engine, SQLite sessions, offline demo, tests, and Docker support.

Suggested topics: `python`, `telegram-bot`, `aiogram`, `sqlite`,
`recommendation-engine`, `asyncio`, `pytest`, `docker`.

## The problem

Smartphone specifications are difficult to translate into a buying decision.
A user might know their budget and priorities without knowing which chipset,
storage configuration, or feature trade-off matters. A short conversation
collects that information and turns it into a small, understandable shortlist.

## The implementation

The user selects a maximum budget, operating system, main use case, screen
size preference, battery priority, minimum storage, required feature, and
preferred brand. The engine applies mandatory constraints before ranking.
It then explains the strengths and compromises of up to three distinct models.
The user can edit answers, resume after a restart, or delete their session.

## What was adapted and what was added

The starting point is aiogram's MIT-licensed `finite_state_machine.py` example.
That upstream example supplies the basic async bot, router, FSM, and polling
pattern. Its original source and license remain in `third_party/aiogram/`.

Project-specific additions include the smartphone questionnaire, typed catalog
and validation, weighted recommendation policy, marketplace URLs, inline
navigation with stale-button protection, persistent SQLite FSM storage, an
offline demo, tests, packaging checks, and CI configuration.

This is an adaptation with documented original work, not a claim that the
Telegram framework or initial bot pattern was written from scratch.

## Engineering decisions to discuss

| Decision | Reason | Trade-off |
| --- | --- | --- |
| Explicit rules and weights | Reproducible ranking with readable reasons | Ratings and weights need editorial maintenance |
| Mandatory filters before ranking | Budget and essential features cannot be traded away silently | Some requests return no results |
| One question definition | Telegram, demo, and generated assets stay consistent | Changing a question can affect stored sessions |
| SQLite FSM backend | Local persistence without a separate database service | One polling process; no distributed coordination |
| Per-session event isolation and nonces | Prevent duplicate and outdated answers from advancing the form | Old buttons require returning to the current question |
| Marketplace searches | Link to the requested model/configuration without listing API credentials | Results and seller offers are not verified |
| Fake Telegram transport in tests | Real dispatcher behavior can be tested without credentials | Does not validate a real BotFather token or Telegram network access |

## Demonstration script

1. Show the generated preview in the README. Explain that it is an offline
   illustration based on actual output, not a Telegram screenshot.
2. Run `make demo`: Android for gaming, 40,000 ₽ maximum, battery priority,
   at least 256 GB, and Android with NFC for Mir Pay.
3. Show the first recommendation, its limitations, and the three search links.
4. Run `./run.sh --demo` with a conflicting iPhone + Mir Pay request. Explain
   why the bot offers no exact match rather than dropping a requirement.
5. Run `make check` and point to the conversation and persistence tests.
6. If a bot token is configured, demonstrate the same flow in a private
   Telegram chat. Keep credentials out of screen recordings.

## Honest scope

This is a working prototype suitable for demonstrating Python application
design. The catalog is curated and finite; prices are indicative. The project
does not measure recommendation accuracy, claim real-world user adoption,
or provide verified marketplace offers. Hosted uptime, a real Telegram
walkthrough, and GitHub CI results must be demonstrated separately if claimed.

Useful next improvements are a licensed offer/price API, a maintained catalog
update process, and user feedback to evaluate recommendation quality.
