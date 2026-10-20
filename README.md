# cadrates

Summarizes Canadian dollar (CAD) exchange rates against USD, EUR and GBP for January to June 2024 from the [Frankfurter API](https://api.frankfurter.dev): the monthly average, the largest daily change per month, and a small seeded sample of featured days.

## Setup

```
conda env create -f environment.yml
conda activate cadrates
pip install -r requirements.txt
pip install -e .
```

## Run

```
python -m cadrates.main
python -m cadrates.main --config config/cadrates.toml
```

Run both from the repository root: the default settings path is relative. A run writes `summary.json` and `run_info.json` to the `output_dir` from the settings file (`data/processed/` by default).

## Check it

```
python -m ruff format --check .
python -m ruff check .
python -m mypy
python -m pytest
```

## Settings

All settings live in `config/cadrates.toml` and are read once into a frozen `Settings` object.

- `source_url`: the API address to download, including the base currency and the currencies to fetch.
- `start_date`: first day to keep, as `YYYY-MM-DD`.
- `end_date`: last day to keep (inclusive), as `YYYY-MM-DD`. It may not be before `start_date`.
- `timeout`: seconds to wait for the API before giving up (a number above 0).
- `output_dir`: folder that receives `summary.json` and `run_info.json`. It is created if needed.
- `seed`: whole number that fixes which days are chosen for `featured_days`.
- `sample_size`: how many days go into `featured_days` (0 or more; capped at the number of days available).
- `log_level`: `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. Messages go to stderr.

## Errors and exit codes

Every expected failure is a subclass of `CadRatesError` and is caught in one place, `main()`.

| Error class | Raised when | What the user sees |
|---|---|---|
| `SettingsError` | the settings file is missing, is not valid TOML, lacks a setting, or has a bad value (for example `timeout = 0` or `end_date` before `start_date`) | `Error: Settings file not found: nope.toml` |
| `SourceError` | the download fails: no network, timeout, or an HTTP error status | `Error: Could not reach <url>: <reason>` |
| `ResponseFormatError` | the API answers, but the body is not JSON or has no `rates` object | `Error: Unexpected response format: expected an object with a 'rates' object` |
| `OutputError` | the output folder or a result file cannot be created or written | `Error: Could not write <path>: <reason>` |

- Exit code `0`: the run finished and both files were written.
- Exit code `1`: an expected failure from the table. The error is logged at ERROR level, one `Error: ...` line goes to stderr, and there is no traceback.
- Exit code `2` comes from `argparse` for a mistake on the command line, such as an unknown option.

## Reproducing a run

The seed is the `seed` line in `config/cadrates.toml`. `run_info.json` is written next to `summary.json` and records the settings used (including the seed, `sample_size`, the URL and the period), the Python version, and the versions of pytest, mypy and ruff.

To get exactly the same `featured_days`, a classmate needs:

- the same `seed` and `sample_size`;
- the same set of days, so the same `source_url`, `start_date` and `end_date`, and the same data from the API (past rates should not change, but the API could revise them);
- the same Python minor version, because `random.Random(seed).sample` is only guaranteed to repeat within a Python release series (`run_info.json` shows which one was used).

The days are sorted before sampling, so the order in which the API returns them does not matter.

## What the tests cover

The suite has no network access: `requests.get` is replaced with `monkeypatch`.

- `DailyRate`: a normal record, a missing currency, a missing value, unreadable dates and rates.
- Both aggregations, with hand-made records, including missing values, a single day, unsorted input and empty input.
- `RateSource`: a failed download, an HTTP error, bad JSON, unexpected shapes, bad dates being skipped and logged, and the period filter.
- Settings: a valid file, a frozen object, every setting being required, and unusable values.
- `featured_days`: the same seed gives the same list, whatever the input order; the sample size is capped.
- Output: `summary.json` and `run_info.json` written to `tmp_path`, an unwritable folder.
- `main()`: exit code 0 and 1, the `Error:` line on stderr with no traceback, the ERROR log record, the default settings path, and argparse's exit code 2.

Not tested: the real call to the Frankfurter API. It needs the internet and would make the suite fail whenever the wifi or the service is down. The price is that nothing here notices if the API changes its response format; `ResponseFormatError` is what the user would see.

## Known limitations

- `CURRENCIES` (USD, EUR, GBP) is the shape of a record, so it stays in `config.py` instead of the settings file. Changing the currencies means editing `config.py` and the `to=` part of `source_url`.
- `source_url` repeats the period that `start_date` and `end_date` describe. The program does not check that they agree.
- The data has days, not shows, so `featured_days` takes the place of the lab's `featured_shows`.
- Dates are stored as tuples such as `(2024, 1, 2)` instead of `datetime.date`.
- The settings path and `output_dir` are relative, so the program must be run from the repository root.
- A network error message includes the long text from `requests`.
- The seed is not a command line option; to try another seed, edit the settings file.
