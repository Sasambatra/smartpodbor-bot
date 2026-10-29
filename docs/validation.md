# Validation record

Local verification date: **2026-10-29**.
Environment: **Python 3.14.4 on Ubuntu in WSL**.

## Observed automated results

| Check | Result |
| --- | --- |
| `make check` | Passed |
| pytest | **82 passed** |
| Overall statement/branch coverage | **86.42%**, including CLI subprocesses |
| Coverage regression threshold | **80%** minimum |
| Ruff lint and formatting | Passed for application, tests, and scripts |
| Bundled catalog validation | 16 models / 22 configurations |
| Generated illustration and transcript | Match current questionnaire and recommendation output |
| `pip check` | No broken requirements |
| Shell syntax | `run.sh` and `setup.sh` passed `bash -n` |

Coverage is a report of exercised code, not a guarantee of correct behavior.
Live polling startup and some Telegram error paths remain outside the offline
test suite. The runtime engine, catalog, state storage, and full conversations
are exercised without real credentials.

## Distribution and configuration checks

`make build` builds the source archive and wheel and checks their contents.
The checks require the bundled catalog, installed command entry point, README,
demo asset, MIT license, and original aiogram license. They reject local
credentials, SQLite files, private notes, and generated Python bytecode.

The built wheel is additionally smoke-tested outside the source directory
using the catalog check and offline example. Workflow, Compose, issue form,
and VS Code configuration files are parsed as YAML/JSON during local review.

Git ignore rules were checked for the real `.env`, `.local/`, session database,
virtual environment, and coverage reports. The publishable `.env.example`
and bundled `smartphone_bot/data/phones.json` remain eligible for tracking.

## Observed GitHub Actions results

The public [CI run 40934558688](https://github.com/Sasambatra/smartpodbor-bot/actions/runs/40934558688)
completed successfully on **2026-10-29**, validating commit
`90a34add520aba1ee1a3235e6546ea71234ec650`.

| Job | Observed result |
| --- | --- |
| Python 3.11 | Passed: dependencies, style, tests, catalog, packaging, installed-wheel smoke test |
| Python 3.14 | Passed: dependencies, style, tests, catalog, packaging, installed-wheel smoke test |
| Docker offline smoke test | Passed: runtime image build, catalog validation, offline demo |

The README badge links to the workflow's current status; the linked run above
is a fixed record of this validation. Local execution used Python 3.14;
Python 3.11 and Docker were additionally verified on GitHub-hosted runners.

## Runtime boundaries

- **Live Telegram conversation:** requires a real BotFather token and working
  Telegram connectivity. Offline tests use a fake transport and do not prove
  a token is valid or a bot is publicly available.
- **Marketplace offers:** URLs are model/configuration searches. Seller
  availability, live prices, and regional feature support are not verified.
