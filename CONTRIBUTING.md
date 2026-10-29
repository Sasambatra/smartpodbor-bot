# Contributing

Use Python 3.11–3.14. From the repository root:

```bash
./setup.sh
.venv/bin/python -m pip install -r requirements-dev.lock
make check
```

Work on a branch and describe the user-visible behavior in your pull request.
`make format` applies Python formatting; `make check` runs style checks, tests
with coverage, catalog validation, and generated-demo validation. All tests
run without a real Telegram token. `make build` creates and checks source and
wheel distributions.

For catalog updates, include a manufacturer specification URL, the exact
memory configuration, and regional caveats. Treat prices as manual estimates
unless a real price source is implemented. Keep editorial ratings consistent
with the documented policy. Run `make preview` whenever demo output changes.

Keep secrets and local user data in ignored files. `.env.example` documents
settings without credentials. Original upstream attribution and MIT notices
must stay with adapted code and distributable packages.
