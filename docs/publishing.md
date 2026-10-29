# Repository and maintenance

Public repository: [Sasambatra/smartpodbor-bot](https://github.com/Sasambatra/smartpodbor-bot).

The project is maintained on `main`. The repository contains the application,
unit and conversation tests, an offline demo, documentation, and CI configuration.

## Get a local copy

```bash
git clone https://github.com/Sasambatra/smartpodbor-bot.git
cd smartpodbor-bot
make dev
make check
```

## Publish an update

Review changes and run the checks before committing:

```bash
make check
make build
git status --short
git add .
git commit -m "Describe the behavior changed"
git push origin main
```

Use a branch and a pull request for changes that benefit from review.
Check the [Actions runs](https://github.com/Sasambatra/smartpodbor-bot/actions)
after a push; the workflow validates Python 3.11/3.14, package contents,
and an offline Docker run.

The ignore rules exclude `.env`, `.local/`, databases, virtual environments,
build output, and coverage output. Original machine-specific notes remain
under ignored `.local/`. The package check also excludes private and generated
files from distributions.

## Present the project

- Russian resume entry: [resume.ru.md](resume.ru.md).
- English resume entry: [resume.en.md](resume.en.md).
- One-page project card: [PDF](resume-project.ru.pdf) and [editable DOCX](resume-project.ru.docx).
- Architecture and trade-offs: [architecture.md](architecture.md).
- Demonstration and interview talking points: [portfolio.md](portfolio.md).

The preview in the README is generated from actual application output and
labeled as an illustration. To claim live Telegram availability, demonstrate
an interaction with your running bot separately. Catalogue prices remain
indicative, and seller listings are not verified.
