# ckanext-datagovuk: Issues & Analysis

## Current State

- **CKAN version:** 2.10.7 (with alphagov fork patches for SMTP), behind the latest 2.10.9 patch
- **Python:** 3.11 (in Docker), declared as 3.6+ in setup.py
- **SQLAlchemy:** 1.4.51
- **Setuptools:** pinned to 80 (to avoid pkg_resources removal in 81)

### Plugins loaded in production

From `production.ini`:

```
datagovuk_publisher_form datagovuk dcat harvest ckan_harvester
dcat_rdf_harvester dcat_json_harvester dcat_json_interface
spatial_metadata spatial_query spatial_harvest_metadata_api
gemini_csw_harvester gemini_waf_harvester gemini_doc_harvester
inventory_harvester
```

### Extension dependencies (pinned to Git SHAs)

| Extension | Fork | SHA |
|-----------|------|-----|
| ckanext-harvest | ckan | `9fb44f79809a1c04dfeb0e1ca2540c5ff3cacef4` |
| ckanext-dcat | ckan | `618928be5a211babafc45103a72b6aab4642e964` |
| ckanext-spatial | alphagov | `c4938431346b50209d7bcf89a1a0154698b9f9f2` |

### Extension coupling

| Extension | Coupling | Direct imports | Upgrade risk |
|-----------|----------|---------------|-------------|
| ckanext-harvest | Very tight | Yes, extensive | High — custom harvesters, direct model queries |
| ckanext-dcat | Loose | None | Low — plugin config only |
| ckanext-spatial | Moderate | None (indirect) | Medium — config + spatial data model assumptions |

**ckanext-harvest** is the deepest dependency. `DguHarvesterBase` extends `HarvesterBase`, `InventoryHarvester` implements `IHarvester`, and `plugin.py` queries `HarvestObject` directly in `after_dataset_show`. CLI tooling also imports harvest models and actions.

**ckanext-dcat** has no direct imports. Loaded as plugins only. The only trace is a Sentry error filter in `plugin.py:286`.

**ckanext-spatial** has no direct imports but is structurally depended on via config (`ckan.spatial.validator.profiles`), the inventory harvester's `spatial-coverage-url` handling, and `dgu_base.py` referencing ckanext-spatial's extent linking.

---

## Performance Issues

### 1. PII removal deep copies on every API response

**Location:** `pii_helpers.py:18`

Every call to `package_search`, `package_show`, and `organization_show` goes through PII stripping. The entry points are:

- `action/get.py:72` — `dgu_package_search` wraps CKAN's `package_search` and passes the full result dict through `remove_pii_from_api_search_dataset`
- `action/get.py:77` — `dgu_package_show` wraps `package_show` through `remove_pii`
- `action/get.py:81` — `dgu_organization_show` wraps `organization_show` through `remove_pii`
- `views/dataset.py:7` — The Flask view endpoint does it again for the v1/v3 API views

The function does `copy.deepcopy(json_data)` on the entire result, then recurses into each dataset doing another `deepcopy` per result. For a search returning N datasets, that's N+1 deep copies. On top of that, `remove_pii_block` re-serializes with `json.dumps`.

The actual PII being removed is 4 fields (`author`, `author_email`, `maintainer`, `maintainer_email`). The deep copy is massively disproportionate.

PII stripping also happens twice on the search API path — the action override at `action/get.py:71` and again in the Flask views at `views/dataset.py:7` and `views/dataset.py:14`.

**Memory impact:** This is the most likely cause of heavy memory issues. A `package_search` can return up to 1000 datasets, each with `data_dict` and `validated_data_dict` (pre-serialized JSON blobs of the full package). The deep copy multiplies this entire tree in memory. Concurrent API requests compound the effect.

**Fix:** Strip PII fields in-place (`dict.pop(key, None)`) instead of deep-copying. The callers already receive a fresh dict from CKAN's action layer.

### 2. Synchronous HTTP calls with no timeouts

**Locations:**
- `inventory_harvester.py:60` — `requests.get(harvest_job.source.url)`
- `lib/geo.py:34` — `requests.get(publisher_url)`
- `lib/geo.py:56` — `requests.get(gss_url)`

None specify a `timeout` parameter. Python's `requests.get()` with no timeout will wait indefinitely — it blocks the calling thread until the TCP connection either completes or the OS-level socket timeout fires (which can be minutes).

The geo calls are sequential — line 34 must complete before line 56 runs — so a slow external service doubles the wait. If both services are unresponsive, the harvest thread hangs for the OS socket timeout duration per dataset.

During inventory harvesting, the gather stage at `inventory_harvester.py:39` fetches the XML document. If that source URL is slow or down, the entire harvest job stalls. The geo lookups are called per-publisher, so one bad external service blocks the whole harvest pipeline.

**Fix:** Add `timeout=(10, 30)` to all `requests.get()` calls. Consider retry with backoff using `urllib3.util.Retry` or `requests.adapters.HTTPAdapter` for transient failures.

### 3. N+1 queries in harvest processing

**Gather stage** (`inventory_harvester.py:120-123`):

For every dataset node in the XML document, a separate SQL query checks if a `HarvestObject` with that GUID already exists. 500 datasets = 500 individual `SELECT` queries.

**Import stage** (`dgu_base.py:97-101`):

Per harvest object, 1-2 queries to find previous objects and reconnect orphaned packages. If the previous object has no `package_id`, it runs another query joining `Package` to `PackageExtra` to find it by GUID.

Each query is small, but the latency adds up — at ~1-2ms per query, 1000 queries adds 1-2 seconds of pure DB wait time on top of the actual import work.

**Fix:** Batch-load all current `HarvestObject` records for the source into a dict keyed by GUID before entering the loop — a single query like `model.Session.query(HarvestObject).filter_by(current=True).filter(HarvestObject.harvest_source_id == source_id).all()`, then `{obj.guid: obj for obj in results}`. The same pattern can be applied in `import_stage`.

### 4. Template helpers hit the database without caching

In `templates/package/snippets/resource_form.html`, `h.activate_upload(pkg_name)` is called 3 times and `h.is_central_gov_organogram(pkg_name)` is called 2 times. Each call runs `Package.by_name().as_dict()` — 5 identical database queries and serializations per template render.

Both helpers only need `pkg_extras.get('schema-vocabulary')`, so extract a single shared helper that fetches the extra value once per request.

**Fix:** Query the package once per request and cache the result. Use `functools.lru_cache` keyed on `pkg_name` (cleared per request), or query just the `PackageExtra` row directly instead of loading and serializing the entire package.

---

## Code Quality Findings

### Critical — Will crash at runtime

| Issue | Location | Detail |
|-------|----------|--------|
| `.iteritems()` | `dgu_base.py:171` | Python 2 dict method, crashes if `default_extras` is non-empty |
| `xrange()` | `geo.py:74` | Python 2 builtin, crashes whenever `get_boundary()` processes polygon data |
| `e.message` + tuple `raise` | `dgu_base.py:450` | Python 2 exception syntax, crashes on any error in `PackageDictDefaults.merge()` |
| `unicode()` | `bin/python_scripts/find_invalid_tags.py:99` | Python 2 type |
| `string.uppercase` | `lib/organogram_xls_splitter.py:73` | Removed in Python 3, use `string.ascii_uppercase` |

These are latent bombs — they only trigger when the specific code path executes.

### Critical — Security

| Issue | Location | Detail |
|-------|----------|--------|
| SQL injection via `.format()` | `bin/python_scripts/fix_organograms_s3_filenames.py:211,221,228` | URLs interpolated directly into SQL |
| SQL injection via `.format()` | `bin/python_scripts/remove_invalid_tags.py:49-56,71-87` | Tag IDs interpolated into DELETE statements |

These are admin/maintenance scripts rather than web-facing code, but the pattern is dangerous.

### High — Silent failures and bad error handling

| Issue | Location | Detail |
|-------|----------|--------|
| Bare `except:` swallows everything | `pii_helpers.py:16` | JSON parse failure returns `None` silently — on every API response |
| Bare `except:` blocks | `organogram_xls_splitter.py:485,491` | Catches SystemExit, KeyboardInterrupt |
| `Session.remove()` at class scope | `dgu_base.py:342` | Runs at import time, not after each harvest commit |
| `'delete'` vs `'deleted'` mismatch | `dgu_base.py:129 vs 91` | Delete branch is unreachable |
| `print()` instead of logging | `organogram_xls_splitter.py:1009,1027,1034,1081...` | 8+ print statements in production code |
| `six` import | `views/user.py:1` | Unnecessary Python 2 compatibility layer |
| `# FIXME URGENTLY` | `dgu_base.py:195-197` | Commented-out code with urgent marker, left unresolved |

### Medium — Maintainability

| Issue | Detail |
|-------|--------|
| `organogram_xls_splitter.py` is 1175 lines | Single file handles parsing, validation, CSV writing, error reporting |
| `import_stage` is 230 lines | One method handles the entire harvest import pipeline |
| Mixed test frameworks | Both `pytest` and `unittest` imported in the same test files |
| Empty test fixtures | `tests/pytest_ckan/fixtures.py` has 11 fixtures that are just `pass` |
| Inconsistent indentation | `_transfer_current` body indented 12 spaces vs 8 everywhere else |
| Legacy controllers not removed | `controllers/api.py`, `controllers/healthcheck.py`, `controllers/user.py` — dead code replaced by Flask views |

---

## Harvester Analysis

### What DguHarvesterBase reimplements from upstream

These features already exist in ckanext-harvest's `CKANHarvester` or `HarvesterBase`:

- Content validation boilerplate (null checks)
- `default_tags` / `default_groups` / `default_extras` from source config
- `owner_org` fallback to source dataset's org
- Deferred FK constraints (`SET CONSTRAINTS ... DEFERRED`)
- Current-flag transfer between harvest objects
- `_munge_title_to_name` dash collapsing
- `extras_not_overwritten` (upstream now has `ckan.harvest.not_overwrite_fields` since v1.4.0)
- `clean_tags` config support

### What's genuinely custom

| Feature | Location | Why it exists |
|---------|----------|--------------|
| Inventory XML harvesting | `inventory_harvester.py` | UK-specific LGA Inventory XML format — no upstream support |
| Resource ID preservation | `dgu_base.py:380-420` | Matches resources by URL to preserve IDs across harvests. Upstream destroys and recreates resources. |
| Metadata provenance | `dgu_base.py:344-377` | W3C PROV-inspired chain tracking every harvest hop. Needed for national aggregator role. |
| Tag schema relaxation | `dgu_base.py:238-240` | Allows non-standard tag names from harvested sources |

### Technical debt in harvesters

- **Status-via-`HOExtra`** pattern adds complexity. Upstream determines new/changed at import time.
- **Orphan repair** (`dgu_base.py:106-122`) is likely a historical data-repair workaround.
- **Storing `harvest_object_id` and `guid` as package extras** is redundant with the HarvestObject model.

---

## Upgrade Options

### Option A: Patch to 2.10.9 (minor)

Same major line. Dockerfile base image bump and testing. Lowest risk, picks up security/bug fixes.

### Option B: Upgrade to 2.11.x (significant)

Latest stable line is 2.11.4. Breaking changes affecting this codebase:

1. **Authentication refactored** — repoze.who replaced by Flask-login. The `user_auth` action in `action/get.py` needs review.
2. **Sessions refactored** — Beaker replaced by Flask-Session.
3. **`SECRET_KEY` now required** — CKAN won't start without it.
4. **Strict config parsing** — invalid config options prevent startup.
5. **CSRF protection** enabled by default on core forms.
6. **Activity plugin requires `context['user']`** — harvester actions calling `package_create`/`package_update` need to ensure this is set.
7. **PostgreSQL 12 minimum** — current PostGIS image already meets this.
8. **All three extension forks** need compatible versions for 2.11.

### Option C: Wait for 2.12

CKAN 2.12 is the planned final 2.x release and bridge to 3.0. Includes keyset pagination, new theme, and background job scheduler. Upgrading to 2.11 first would be a prerequisite.

---

## DB Investigation Queries

Queries to verify the scale of data being processed by `pii_helpers.py`. The deep-copy overhead multiplies the raw payload size — the N+1 `deepcopy` pattern means roughly `2x + N * avg_dataset_size` of additional memory on top of the original.

### Size of serialized dataset dicts

```sql
SELECT
    avg(length(validated_data_dict)) AS avg_bytes,
    max(length(validated_data_dict)) AS max_bytes,
    count(*) AS total_packages
FROM package_revision
WHERE current = true;
```

### Extras size per package

```sql
SELECT
    p.name,
    count(pe.id) AS num_extras,
    sum(length(pe.value)) AS total_extras_bytes
FROM package p
JOIN package_extra pe ON pe.package_id = p.id
WHERE p.state = 'active'
GROUP BY p.name
ORDER BY total_extras_bytes DESC
LIMIT 20;
```

### Worst-case package_search response size

```sql
SELECT
    sum(data_size) AS total_bytes,
    pg_size_pretty(sum(data_size)::bigint) AS total_pretty
FROM (
    SELECT length(validated_data_dict) + length(data_dict) AS data_size
    FROM package_revision
    WHERE current = true
    ORDER BY length(validated_data_dict) DESC
    LIMIT 1000
) sub;
```

### Resource count per package

```sql
SELECT
    p.name,
    count(r.id) AS num_resources
FROM package p
JOIN resource r ON r.package_id = p.id
WHERE p.state = 'active'
GROUP BY p.name
ORDER BY num_resources DESC
LIMIT 20;
```
