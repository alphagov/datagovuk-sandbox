# Search and discovery

This document discusses approaches to finding and accessing topic data, from keyword and full text search through to semantic and hybrid search, as well as generative AI approaches such as Amazon Bedrock. Technical prototyping has been carried out on the search and browse options (sections 1–4). The generative approach has not yet been prototyped but the aim is to investigate further.

## Strategic direction

The search and browse approaches (sections 1–4) are complementary and could be adopted incrementally as each builds on the last. However, there is a fundamental divergence between these and a generative AI approach:

- **Search and browse:** Users navigate and filter a list of results to find specific data.
- **Synthesised answers:** Users ask questions and receive a generated response grounded in the underlying content.

If the product direction favours synthesised answers (e.g. via Amazon Bedrock), it would likely remove the need for much of the custom search infrastructure described below, representing a different implementation path rather than another incremental layer. This is explored further in the [Further investigation](#further-investigation) section.

There is an existing CKAN instance with dataset metadata searchable via Solr. Rather than migrating that data to another search solution, the recommended approach is to build a new search backend using one of the options below, and have it also query the existing CKAN Solr index with the user's search terms. This would be a way to present a single search experience across both data sources while deferring decisions about CKAN's long term role. In the longer term the two indexes could be merged into a single search model, but that is dependent on what future role, if any, CKAN will play.

> [!IMPORTANT]
> Note that any integration with existing ckan catalogue search assumes that work has been done to radically clean up the current data in the catalogue. This clean up should encompass not just datasets that have been abandoned/unmaintained or have broken links but also those with poor titles and descriptions as those are part of the existing ckan solr search.

1. [Database native full text search](#1-database-native-full-text-search)
2. [Full text search with aggregations](#2-full-text-search-with-aggregations)
3. [Database native hybrid search (FTS + Vectors)](#3-database-native-hybrid-search-fts--vectors)
4. [Hybrid search (Lexical + Semantic)](#4-hybrid-search-lexical--semantic)
5. [Discoverability](#5-discoverability)

---

## 1. Database native full text search

Uses standard relational database full text search capabilities (e.g. PostgreSQL's `tsvector`) with a weighted index. A database trigger or application logic maintains the search vector from `title` (high weight) and `body` (lower weight).

Tagging can be introduced alongside full text search to provide another layer of grouping and association not purely based on body copy. Tags supplement lexical results; if a search term matches a tag, those items are included even if the term doesn't appear in the text.

### How it works

- User input is parsed into a search query (supporting operators like and/or and exclusion)
- Results are scored by relevance ranking
- Tag matching supplements lexical results
- Results are ranked by the combined score

### What it covers

- Full text search over title and body
- Tag-based supplemented search
- Relevance ranking with title boosting

### What it doesn't cover

- Aggregate filtering — possible but typically requires additional development for performance
- Fuzzy matching/typo tolerance — usually requires specialized extensions (e.g. `pg_trgm`)

### Trade offs

- No additional infrastructure beyond the primary database
- Transactional consistency — search is always up to date
- Faceting and advanced relevance tuning require more manual implementation than dedicated search engines

### Why not load content directly into a search engine?

An alternative approach would be to skip the database and index content directly into a search engine (like OpenSearch). Reasons why this might not be the best approach:

1. **Operational robustness** — a database provides a durable, queryable content store as a source of truth
2. **Future admin interface** — the database serves as the backend for content management and relational integrity
3. **Relational integrity** — the database enforces relationships (e.g. topics belonging to collections) that would be implicit and fragile if derived from a search index alone
4. **Implementation simplicity** — if data is already in the database, native full text search provides a high-quality baseline with minimal overhead

---

## 2. Full text search with aggregations

A dedicated search engine (e.g. OpenSearch or Elasticsearch) can be used as a denormalized search index. The primary database remains the source of truth and data is projected into flat search documents and indexed.

### Architecture

- **Write path:** data is written to the primary database, then synchronized to the search index
- **Read path:** search queries go to the search engine, which returns results, aggregation counts, and ranking
- **Document model:** one document per item, denormalized with metadata and tags included

### Query strategy

- Multi field matching on `title` (boosted) and `body`
- Filter clauses for categories or tags
- Aggregations for facet counts

### Tag semantics

Multiple selected tags typically use OR semantics (matching any selected tag). AND semantics (matching all selected tags) can be implemented if required.

### Trade offs

- First class filtering and aggregation support
- Advanced relevance tuning (boosting, custom analyzers)
- Requires a separate service and a synchronization/indexing step
- Eventually consistent — there may be a slight lag between database updates and search availability
- Increased operational complexity (sync monitoring, reindexing)

---

## Comparison

| | Database native | Dedicated Search Engine |
|---|---|---|
| Infrastructure | Primary DB only | DB + Search Cluster |
| Consistency | Transactional | Eventually consistent |
| Full text search | Yes | Yes |
| Faceted filtering | Requires custom dev | Builtin via aggregations |
| Relevance tuning | Basic | Advanced |
| Fuzzy / typo tolerance | Extension based | Builtin |
| Operational overhead | Lower | Higher |

---

## 3. Database native hybrid search (FTS + Vectors)

Extends native full text search with vector based semantic search. Both retrieval methods run against the same database using vector extensions (e.g. `pgvector`).

### How it works

Items have vector embeddings stored in an indexed column. At query time, two ranked lists are produced:

1. **Lexical** — Keyword matching over the text search vector
2. **Semantic** — Distance matching between the query embedding and stored embeddings

The two lists are combined using **Reciprocal Rank Fusion (RRF)**. RRF scores items based on their position in each list rather than reconciling different scoring scales. Items appearing in both lists rank highest; items in only one list still contribute.

### Embeddings

Embeddings are generated using a transformer model. This can be done locally via a containerized model or via a hosted API. Using a local model ensures no external dependencies and lower latency for query embedding generation.

### Trade offs

- No additional infrastructure beyond the primary database
- Semantic matching catches queries that don't share exact terms with the content
- Fusion logic is handled at the application level
- Retrieval quality is determined by the choice of embedding model

---

## 4. Hybrid search (Lexical + Semantic)

Uses a search engine's native hybrid query to combine BM25 text matching with vector search (kNN) in a single request. Score normalization and fusion occur within the search cluster.

### How it works

A single hybrid query sends two sub-queries:

1. **Lexical** — Text matching on title and body
2. **Semantic** — Nearest neighbour search over vector embeddings

A search pipeline normalizes the score distributions and combines them (e.g. using RRF). This offloads the fusion complexity from the application to the search infrastructure.

### Embeddings

Reuses the same embedding strategy as the database native approach. Embeddings are included in the search index during the indexing process.

### Score thresholds and tuning

Hybrid queries can return a "long tail" of weakly related semantic results. A minimum score threshold can be applied to filter out noise, and parameters like the number of nearest neighbours retrieved should be tuned against representative data to balance recall and precision.

### Trade offs

- Native fusion handled by the search engine
- Retrieval and fusion in a single request
- Requires modern search engine versions that support RRF as a combination technique
- Thresholds and retrieval parameters require ongoing tuning as content grows

---

## Production considerations

For a production OpenSearch deployment, bulk reindexing should be replaced with event-driven synchronisation:

**Outbox pattern:** write an event into an outbox table in the same PostgreSQL transaction. A worker reads the outbox and updates the search index. Strong consistency, easy retries.

**Events that require reindexing:** topic field changes, topic tag changes, collection title/slug changes (fan out to all topics in that collection), tag name changes (fan out to all topics with that tag).

**Reindex strategy:** use versioned indices and aliases (`topics_v1`, `topics_v2`, alias `topics_current`). Create new index, bulk reindex, validate, switch alias atomically.

**Monitoring:** search latency, indexing latency, failure rate, document count, outbox backlog, cluster health.

**AWS deployment:** develop locally against OpenSearch, stick to core query DSL features.

---

## 5. Discoverability

The goal is to make topic and collection data discoverable and interoperable. LLMs and modern tooling benefit most from clean, consistent JSON with a well defined schema, so a pragmatic approach could be to start with JSON + JSON Schema and layer JSON-LD on top later if semantic discoverability becomes important.

### JSON endpoints

Each HTML resource would have a corresponding `.json` endpoint (e.g. `/collections.json`, `/collections/{slug}.json`, `/collections/{slug}/{topic-slug}.json`). These are described by a JSON Schema definition via an OpenAPI spec, and linked from HTML pages using `<link rel="alternate">` and `<link rel="describedby">` tags. JSON responses use a `Link` header to point at the schema they conform to, keeping the JSON body free of metadata.

### JSON-LD (optional, later)

JSON-LD adds a shared vocabulary via `@context` using schema.org types. The mapping:

| Application concept | schema.org |
|---|---|
| Catalogue | `DataCatalog` |
| Collection | `DataCatalog` (nested) |
| Topic | `Dataset` |
| Tag | `keywords` |
| Link (dataset) | `distribution` → `DataDownload` |
| Title | `name` |
| Updated date | `dateModified` |

schema.org also supports fields we may want later: publisher (`Organization`), data formats (`encodingFormat`), licence (`license`), spatial/temporal coverage.

### Trade offs

| | JSON + Schema | JSON-LD |
|---|---|---|
| Simplicity | High | Moderate |
| LLM/tooling compatibility | Strong | Indirect |
| Machine discoverability | No | Yes |
| Search engine understanding | No | Yes |
| Implementation effort | Low | Moderate |

JSON + Schema is the foundation. JSON-LD layers on top without changing the underlying data or API.

### llms.txt

[llms.txt](https://llmstxt.org/) is an emerging, low effort convention for helping LLMs understand a site, but there’s currently no strong evidence major providers use it or that it improves AI citations. It’s harmless to add, but arguably much less impactful than structured approaches like APIs or well organized content, and should be treated as experimental rather than essential.

---

## Further investigation

- **CKAN catalogue integration** — to be genuinely useful to users, search needs to surface good quality dataset metadata from the existing CKAN catalogue alongside topic content. This means executing a federated search from our backend against the CKAN Solr index and merging results. Dependent on the data quality work noted above.

- **MCP server** — an MCP server would allow users to search and browse topics directly from their LLM client of choice, without using our search interface at all. The server would be a thin layer combining two things: the JSON endpoints (for retrieving structured topic and collection data) and the search backends (for hybrid search via OpenSearch or PostgreSQL). Together these give an LLM the ability to search, retrieve, and reason over topic content without needing a browser.

- **Evaluation framework** — systematic way to measure search quality haven't been addressed yet. Standard approaches exist but they require a set of test queries paired with human judged relevant results. Building a small set of good representative queries would allow better comparison across approaches rather than relying on manual inspection.

- **Embedding model evaluation** — the model used with local testing (`Snowflake/snowflake-arctic-embed-s`) was chosen based on size and convenience. Running representative queries against different models on bigger bodies of content would help validate model choice. There are also API's available for embeddings.

- **Amazon Bedrock** — a fully managed AWS service. You point it at your content and it handles chunking, embedding, vector storage, and retrieval with no self managed embedding pipeline, vector indexes, or search tuning required. It can also pass retrieved content to an LLM to generate synthesised answers rather than returning a list of results. Worth investigating early because if the product direction favours "ask a question, get an answer" over traditional search result lists, it could remove the need to build and maintain the search infrastructure described in this document. Pay per query pricing (retrieval and LLM inference fees). The trade off is less control over ranking and presentation, and tight coupling to AWS.
