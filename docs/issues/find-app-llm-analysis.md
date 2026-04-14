# datagovuk_find: Performance & Architectural Analysis

---

## Claude Analysis

### Critical: Thread-Unsafe Shared State in `Search::Solr`

**File:** `app/services/search/solr.rb` (entire class)

The `Search::Solr` class stores request-specific data in class-level instance variables (`@page`, `@query`, `@filter_query`, `@sort_query`, `@organisations_list`) inside `self.*` methods. These variables are shared across all requests in the process.

With Puma configured for 3 threads (`config/puma.rb`), concurrent requests overwrite each other's state. For example, Request A sets `@query`, then Request B overwrites it before A calls `query_solr` — returning incorrect search results for A.

**Affected variables:**
- `@page` (line 8) — pagination offset
- `@query` (line 22, 27) — the Solr search query
- `@filter_query` (line 42) — active filters
- `@sort_query` (line 15) — sort order
- `@organisations_list` (line 90) — organisation lookup map

**Recommendation:** Refactor to use instance methods with `new`, passing state through method parameters or a short-lived instance per request.

### High: N+1 Solr Queries in `SearchPresenter`

**File:** `app/presenters/search_presenter.rb`, lines 32-34

For each organisation slug returned in search facets, a separate Solr query is made:

```ruby
slugs.map do |slug|
  org = Search::Solr.get_organisation(slug)["response"]["docs"].first
  org.present? ? org["title"] : slug
end
```

Each call goes through `Rails.cache.fetch` with a 10-minute TTL, but on cold cache or expiry this fires N individual Solr round-trips. Search results can include many distinct publishers.

**Recommendation:** Batch-fetch organisations in a single Solr query using `name:(slug1 OR slug2 OR slug3 ...)`.

### Medium: `@organisations_list` is nil on Cache Hit

**File:** `app/services/search/solr.rb`, lines 87-106

The `get_organisations` method assigns `@organisations_list` inside the `Rails.cache.fetch` block. On a cache hit, the block does not execute, so `@organisations_list` is never set. However, `publisher_filter` (line 46) reads `@organisations_list` directly:

```ruby
def self.publisher_filter(organisation)
  return "" if @organisations_list.nil?
  "organization:#{@organisations_list[organisation]}"
end
```

On cache hit, `@organisations_list` may be `nil` (or stale from a previous request in multi-threaded mode), causing publisher filters to silently return an empty string and be ignored.

**Recommendation:** Use the return value of `get_organisations` rather than relying on the side-effect of setting a class variable.

### Medium: Static Data Structures Recreated Every Request

**File:** `app/controllers/application_controller.rb`, lines 26-134

Three `before_action` callbacks (`set_collections`, `set_data_manual_pages`, `set_data_manual_menu_items`) allocate identical arrays of hashes on every request. The data is static and never changes at runtime.

**Recommendation:** Define these as frozen constants at the class level:

```ruby
COLLECTIONS = [
  { title: "Business and economy", slug: "business-and-economy", ... }.freeze,
  ...
].freeze
```

### Medium: Uncached File I/O on Every Page Load

**File:** `app/controllers/v2/pages_controller.rb`, `average_house_prices` and `fuel_and_oil_prices` methods

These methods call `File.read` and `JSON.parse` on JSON data files for every request to the components page. The underlying files only change between deployments.

**Recommendation:** Load and parse the JSON once at boot time, or cache the parsed result at the class level.

### Low: No Connection Pooling for Faraday (Preview)

**File:** `app/models/preview.rb`

Each preview request creates a new `Faraday` connection via `build_connection`. There is no connection reuse or pooling. Under load this creates excessive short-lived TCP connections.

**Recommendation:** Use a shared, thread-safe Faraday connection or connection pool.

### Low: Stale Solr Client Connection

**File:** `app/services/search/solr.rb`, line 175

```ruby
def self.client
  @client ||= RSolr.connect(url: ENV["SOLR_URL"])
end
```

A single RSolr connection is memoised for the lifetime of the process. If the connection drops or Solr restarts, the stale connection is never refreshed, potentially causing errors until the process is restarted.

**Recommendation:** Add connection health checks or periodic reconnection logic.

### Claude Summary

| Severity | Issue | Location |
|----------|-------|----------|
| Critical | Thread-unsafe class-level state in Solr service | `app/services/search/solr.rb` |
| High | N+1 Solr queries per search | `app/presenters/search_presenter.rb:32-34` |
| Medium | `@organisations_list` nil on cache hit | `app/services/search/solr.rb:87-106` |
| Medium | Static data re-allocated every request | `app/controllers/application_controller.rb:26-134` |
| Medium | Uncached JSON file reads | `app/controllers/v2/pages_controller.rb` |
| Low | No Faraday connection pooling | `app/models/preview.rb` |
| Low | Stale Solr client connection | `app/services/search/solr.rb:175` |

---

## Gemini Analysis

### 1. Critical: Thread Safety & State Corruption

**Severity: High**

The `Search::Solr` class uses class instance variables (e.g., `@query`, `@filter_query`, `@page`) to store request-specific state.

- **The Risk:** Since `Puma` is a multi-threaded web server, these variables are shared across all threads in a process. If two users search simultaneously, Thread A may overwrite Thread B's query parameters mid-execution.
- **Impact:** Users may see search results for queries they didn't perform, or the application may crash with 500 errors due to inconsistent state.
- **Location:** `app/services/search/solr.rb`

### 2. Performance: N+1 Solr Queries (Network Bottleneck)

**Severity: Medium-High**

The application exhibits a classic N+1 problem, but over the network to Solr rather than a database.

- **The Problem:** In `SearchPresenter#organisations`, the code iterates over every "organization" facet returned by Solr and performs a new synchronous Solr request for each one.
- **Impact:** If a search returns 50 organization facets, the app makes 51 network calls to Solr to render a single page. This significantly increases latency and Solr load.
- **Location:** `app/presenters/search_presenter.rb` (specifically the `organisations` method).

### 3. Performance: Synchronous External I/O in Views

**Severity: Medium**

The "Preview" feature for CSV files performs synchronous network requests during the template rendering phase.

- **The Problem:** `SolrDatafile#preview` calls `Preview.new`, which immediately executes a `Faraday.get` to an external URL.
- **Impact:** If an external server (e.g., an ONS or local authority server) is slow or unresponsive, the Rails worker thread is held open for up to 5 seconds. This can quickly exhaust the Puma thread pool, leading to a site-wide outage.
- **Location:** `app/models/preview.rb#fetch_raw` and `app/views/previews/show.html.erb`.

### 4. CPU Efficiency: Redundant JSON Parsing

**Severity: Low-Medium**

The field `validated_data_dict` contains a large JSON string that is parsed repeatedly.

- **The Problem:** In `app/views/search/search.html.erb`, `JSON.parse(dataset["validated_data_dict"])` is called twice inside the loop for every search result.
- **Impact:** For a page of 20 results, the app performs 40 expensive JSON parsing operations on every request.
- **Location:** `app/views/search/search.html.erb` and `app/models/solr_dataset.rb`.

### 5. Logical Bug: Broken Publisher Filtering (Cache Side-Effect)

**Severity: Medium**

There is a bug in how organization data is cached in `Search::Solr.get_organisations`.

- **The Problem:** The instance variable `@organisations_list` is only assigned inside the `Rails.cache.fetch` block. On a cache hit, the block does not execute, and `@organisations_list` remains `nil`.
- **Impact:** This causes the `publisher_filter` method to return an empty string, effectively breaking the "Filter by Publisher" feature for all requests until the cache expires or is cleared.
- **Location:** `app/services/search/solr.rb#get_organisations`.

### 6. Architectural: Static Data Overhead

**Severity: Low**

The `ApplicationController` uses `before_action` to set `@collections` and `@data_manual_pages` on every single request.

- **The Problem:** These are hardcoded arrays that never change.
- **Impact:** Unnecessary object allocation and memory pressure on every request (including search, dataset views, and static pages).
- **Location:** `app/controllers/application_controller.rb`.

### Gemini Recommended Next Steps

1. **Thread Safety Fix:** Refactor `Search::Solr` to remove all class instance variables. Use local variables or pass a configuration object between methods.
2. **Batch Organisation Lookups:** Update the search query to include organization titles in the initial result set or fetch all required organization details in a single bulk Solr query using the `OR` operator.
3. **Model Memoization:** Move the parsing of `validated_data_dict` into `SolrDataset#initialize` and store the result in an instance variable.
4. **Async Previews:** Fetch CSV previews via client-side JavaScript (AJAX) after the page has loaded to ensure Rails worker threads are released immediately.
5. **Move Static Data to Constants:** Convert hardcoded arrays in `ApplicationController` to frozen constants defined at the class level or in an initializer.
