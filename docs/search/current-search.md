# data.gov.uk - current directory search

Based review of [ckanext-datagovuk](https://github.com/alphagov/ckanext-datagovuk).

## Solr schema

Standard CKAN 2.8 schema (`docker/solr/schema.xml`). Default query field is `text`, a catch all copy field that aggregates titles, notes, tags, URLs, resource fields, and extras on indexing.

Default operator is AND.

Other fields beyond CKAN defaults:
- `harvest` — text, multiValued (DGU specific)
- Dynamic fields: `extras_*`, `res_extras_*`, `vocab_*`

## How data gets indexed

Three routes into Solr:

1. **Standard CKAN indexing** — automatic on dataset create/update via `PackageSearchIndex.index_package()`
2. **CLI: `reindex_recent`** — re-indexes datasets modified in the last N minutes (configurable via `CKAN_REINDEX_MINUTES_BEFORE` env var)
3. **CLI: `reindex_organisations`** — writes org documents directly to Solr via pysolr with a separate `site_id: dgu_organisations`

Batch reindex scripts also exist in `bin/python_scripts/` for targeted reindexing by package ID or date.

## Search config (`ckan.ini`)

```ini
search.facets = organization groups tags res_format license_id
search.facets.limit = 50
search.facets.default = 10
ckan.search.default_package_sort = score desc, metadata_modified desc
ckan.search.rows_max = 1000
ckan.search.default_include_private = true
solr_timeout = 60
```

Five facets, all using CKAN's builtin faceting, no custom `IFacets` implemented.

## Customisations

The plugin (`ckanext/datagovuk/plugin.py`) implements `IPackageController` with a `before_dataset_index` hook that truncates string fields to 15,000 chars before indexing (to stay within Solr 6's string field limit).

Limit set in `ckanext/datagovuk/schema.py`

Safe fields like `notes`, `text`, `extras_*`, and `harvest` are excluded from truncation. See `ckanext/datagovuk/schema.py`.

Three other search related customisations:

- **PII removal** (`action/get.py`) — wraps `package_search` to strip author/maintainer emails from API responses
- **Injection blocking** (`ckan_patches/query.py`) — rejects queries containing `{!xmlparser` / `<!doctype` patterns
- **Custom search API views** (`views/dataset.py`) — `/api/search/dataset` and `/api/3/search/dataset` with PII removal applied

## Summary

This is a thin layer on top of CKAN's standard Solr integration. CKAN handles the core indexing and querying. The extension adds defensive measures (string truncation, injection blocking, PII scrubbing) rather than custom search behaviour or novel facets.
