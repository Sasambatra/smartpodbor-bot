# Catalog format and maintenance

The bundled source of model facts is
[`smartphone_bot/data/phones.json`](../smartphone_bot/data/phones.json).
One object describes one memory configuration. Configurations of the same
model use the same `name` and distinct `id` values.

## Metadata

| Field | Type | Meaning |
| --- | --- | --- |
| `specs_checked_on` | ISO date string | Date manufacturer specification references were reviewed |
| `price_note` | Nonempty string | Visible explanation of the price source and limitations |
| `rating_note` | String, informational | Explanation of editorial scores; retained in the JSON source |
| `phones` | Nonempty array | Phone configuration objects |

## Phone fields

| Fields | Type and validation |
| --- | --- |
| `id` | Unique lowercase letters/digits/hyphens, e.g. `pocox7pro-256` |
| `name` | Nonempty model name, shared across configurations |
| `brand` | `xiaomi`, `samsung`, `honor`, `google`, or `apple` |
| `os` | `android` or `ios` |
| `ram_gb` | Positive integer, or `null` if not supplied |
| `storage_gb` | Integer, at least 128 |
| `price_rub` | Positive integer; indicative price of this exact configuration |
| `screen_inches` | Number strictly between 4 and 9 |
| `display`, `chipset` | Nonempty human-readable specifications |
| `battery_mah`, `charging_w` | Positive integers, or `null` if not supplied |
| `nfc`, `esim` | JSON booleans; strings such as `"false"` are rejected |
| `ip_rating` | Nonempty description; `IP67` or `IP68` satisfies the water-protection filter |
| `camera`, `performance`, `endurance`, `screen`, `software` | Editorial integer ratings from 1–10 |
| `strengths`, `caveats` | Nonempty arrays of nonempty strings |
| `source_url` | Absolute HTTPS manufacturer reference, without URL credentials |
| `search_query` | Nonempty model/configuration query used for all three marketplaces |

Unexpected phone fields and missing required fields are rejected. Unknown
brands require updating the questionnaire and accepted classification too.
`IP65M`, `IP66`, and standalone `IP69` do not satisfy the specified IP67/IP68
requirement. A regional version must be checked independently: a model-level
feature flag does not guarantee the feature exists in every seller's variant.

## Update procedure

1. Identify the exact device, memory configuration, and intended region.
2. Review the manufacturer's specification page and set `source_url`.
3. Describe meaningful strengths and compromises in Russian. Avoid marketing
   superlatives unsupported by the facts.
4. Set the indicative price and disclose its basis in `price_note`. Do not
   label a manual estimate as a live marketplace price.
5. Apply editorial ratings consistently with existing models. These are
   relative judgments; do not present them as measured benchmarks.
6. Update `specs_checked_on` only after reviewing the changed references.
7. Run `./run.sh --check`, `make preview`, and `make check`.

The demo illustration and transcript are generated from the same catalog.
CI fails when they become stale after a catalog or policy change.

## Use a private experiment

```bash
mkdir -p .local
cp smartphone_bot/data/phones.json .local/phones.json
./run.sh --catalog .local/phones.json --check
./run.sh --catalog .local/phones.json --demo
```

The `.local/` directory is ignored by Git and excluded from distributables.
Keep the complete JSON structure when editing a private copy.
