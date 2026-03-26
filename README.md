# Datagovuk data prototypes

## Test data vistualisations

The [data](data) directory is used for testing data to be used in visualisations.


## Architecture docs

Architecture [docs](docs)


## Site checks for data.gov.uk

Scripts that collect URLs from the [datagovuk_find](https://github.com/alphagov/datagovuk_find) collection pages and validate them using a real browser (Playwright).

### Setup

```
uv sync
uv run playwright install chromium
```

### Commands

**Collect collection URLs** from the datagovuk_find repo and write `data/collections/collection-urls.csv`:

```
uv run python -m scripts.cli get-collection-urls
```

**Check URLs** - uses the list of collection pages and urls, opens each collection page on data.gov.uk, verifies the URLs listed in the CSV are present on the page, and checks each URL is reachable in the browser. Writes a timestamped results CSV to `data/results/`:

```
uv run python -m scripts.cli check-urls
```

**Check link text** - reports any URLs missing a `link-text` value:

```
uv run python -m scripts.cli check-link-text
```

### Results CSV

The check produces `data/results/collection-check-<timestamp>.csv` with columns:

| Column | Description |
|--------|-------------|
| collection | Collection name (e.g. `environment`) |
| slug | Slugified topic name, matches the URL path on data.gov.uk |
| url | The URL being checked |
| link-text | Display text for the link |
| type | `website`, `api`, or `dataset` |
| on-page | Whether the URL was found as a link on the collection page |
| reachable | Whether the URL returned a successful response in the browser |

### GitHub Actions

The workflow `.github/workflows/check-collection-urls.yml` can be triggered manually to collect URLs, run checks, and commit the results.
