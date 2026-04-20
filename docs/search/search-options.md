# Search and discovery

This document discusses approaches to finding and accessing topic data, covering keyword, meaning based, and hybrid search. Technical prototyping has been carried out on these options. Fully generative AI approaches are not covered in depth here but are signposted in [Further investigation](#further-investigation). 

However, the intention is to experiment in the first instance with augmenting the search approaches by post processing results using LLM tools to provide more natural language responses. This approach is referred to as retrieval augmented generation (RAG).

## Terms

- **Keyword search** — finds content by matching the exact words a user types against the words in the content. More formally referred to as lexical search.
- **Meaning based search** — finds content by understanding the intent behind a query, matching concepts even when the exact words differ. This is more formally referred to as semantic search.
- **Hybrid search** — combines keyword and meaning based results to improve overall search quality.

## Choosing an approach

The approaches below are a progression rather than alternatives. Each builds on the last, and the differences between them are primarily operational — how much infrastructure is required, how much custom code is needed, and how much search quality improves as a result.

The starting point is native PostgreSQL full text search (`tsvector`), which requires no additional infrastructure. Adding `pgvector` extends that with meaning based search. Moving to OpenSearch adds richer aggregation support and native hybrid search, at the cost of a separate service to run and keep in sync.

There is an existing CKAN instance with dataset metadata searchable via Solr. Rather than migrating that data to another search solution, the recommended intial approach would be to build a new search backend using one of the options below, and have it also query the existing CKAN Solr index directly (or via CKAN API?) with the user's search terms. This would be a way to present a single search experience across both data sources while deferring decisions about CKAN's long term role. In the longer term the two indexes could be merged into a single search model, but that is dependent on what future role, if any, CKAN will play.

> [!IMPORTANT]
> Note that any integration with existing ckan catalogue search assumes that work has been done to radically clean up the current data in the catalogue. This clean up should encompass not just datasets that have been abandoned/unmaintained or have broken links but also those with poor titles and descriptions as those are part of the existing ckan solr search.

- [Keyword search](#keyword-search) — database native (`tsvector`) or OpenSearch
- [Hybrid search](#hybrid-search) — database native (`pgvector`) or OpenSearch
- [Discoverability](#discoverability)

---

## Keyword search

Keyword search matches the exact words a user types against words in the content. Two infrastructure options are available: database native using PostgreSQL's `tsvector`, or a dedicated search engine (OpenSearch).

### Database native

Uses standard relational database full text search capabilities with a weighted index. A database trigger or application logic maintains the search vector from `title` (high weight) and `body` (lower weight).

#### How it works

- User input is parsed into a search query (supporting operators like and/or and exclusion)
- Results are scored by relevance ranking
- Results are ranked by the combined score

---

### Dedicated search engine (OpenSearch)

A dedicated search engine (e.g. OpenSearch or Elasticsearch) can be used as a denormalized search index. The primary database remains the source of truth and data is projected into flat search documents and indexed.

#### Architecture

- **Write path:** data is written to the primary database, then synchronized to the search index
- **Read path:** search queries go to the search engine, which returns results, aggregation counts, and ranking
- **Document model:** one document per item, denormalized with metadata included

#### Query strategy

- Multi field matching on `title` (boosted) and `body`
- Filter clauses for categories
- Aggregations for facet counts

---

## Hybrid search

Hybrid search combines keyword and meaning based results to improve overall search quality. As with keyword search, both a database native and a dedicated search engine option are available.

### Database native

Extends native full text search with meaning based search. Both retrieval methods run against the same database using vector extensions (e.g. `pgvector`).

#### How it works

Items have vector embeddings stored in an indexed column. At query time, two ranked lists are produced:

1. **Keyword search** — matching over the text search vector
2. **Meaning based search** — distance matching between the query embedding and stored embeddings

The two lists are combined using **Reciprocal Rank Fusion (RRF)**. RRF scores items based on their position in each list rather than reconciling different scoring scales. Items appearing in both lists rank highest; items in only one list still contribute.

#### Embeddings

Embeddings are generated using a transformer model. This can be done locally via a containerized model or via a hosted API. Using a local model ensures no external dependencies and lower latency for query embedding generation.

---

### Dedicated search engine (OpenSearch)

Uses a search engine's native hybrid query to combine BM25 text matching with vector search (kNN) in a single request. Score normalization and fusion occur within the search cluster.

#### How it works

A single hybrid query sends two sub-queries:

1. **Keyword search** — text matching on title and body
2. **Meaning based search** — nearest neighbour search over vector embeddings

A search pipeline normalizes the score distributions and combines them (e.g. using RRF). This offloads the fusion complexity from the application to the search infrastructure.

#### Embeddings

Reuses the same embedding strategy as the database native approach. Embeddings are included in the search index during the indexing process.

#### Score thresholds and tuning

Hybrid queries can return a "long tail" of weakly related meaning based results. A minimum score threshold can be applied to filter out noise, and parameters like the number of nearest neighbours retrieved should be tuned against representative data to balance recall and precision.

---

## Production considerations

For a production OpenSearch deployment if the number of items to be indexes becomes large, bulk reindexing could be replaced with event-driven synchronisation. (threshold to make this decision?)

**Outbox pattern:** write an event into an outbox table in the same PostgreSQL transaction. A worker reads the outbox and updates the search index. Strong consistency, easy retries.

**Events that require reindexing:** topic field changes, collection title/slug changes (fan out to all topics in that collection).

**Reindex strategy:** use versioned indices and aliases (`topics_v1`, `topics_v2`, alias `topics_current`). Create new index, bulk reindex, validate, switch alias atomically.

**Monitoring:** search latency, indexing latency, failure rate, document count, outbox backlog, cluster health.

**AWS deployment:** develop locally against OpenSearch, stick to core query DSL features.

---

## Summary

| | DB native (PostgreSQL) | OpenSearch |
|---|---|---|
| **Operational overhead** | Low — no extra services, transactional consistency | Higher — separate service, sync pipeline, eventual consistency |
| **Custom development** | More — faceting, typo tolerance, and fusion logic need custom code | Less — aggregations, fuzzy matching, and hybrid queries are builtin |
| **Search capability** | Keyword and hybrid via `tsvector` + `pgvector` | Keyword and hybrid with more advanced relevance tuning |

---

## Discoverability

The goal is to make topic and collection data discoverable and interoperable. LLMs and modern tooling benefit most from clean, consistent JSON with a well defined schema, so a pragmatic approach could be to start with JSON + JSON Schema and layer JSON-LD on top later if machine readable discoverability (semantic discoverability) becomes important.

### JSON endpoints

Each HTML resource would have a corresponding `.json` endpoint (e.g. `/collections.json`, `/collections/{slug}.json`, `/collections/{slug}/{topic-slug}.json`). These are described by a JSON Schema definition via an OpenAPI spec, and linked from HTML pages using `<link rel="alternate">` and `<link rel="describedby">` tags. JSON responses use a `Link` header to point at the schema they conform to, keeping the JSON body free of metadata.

### JSON-LD (optional, later)

JSON-LD adds a shared vocabulary via `@context` using schema.org types. The mapping:

| Application concept | schema.org |
|---|---|
| Catalogue | `DataCatalog` |
| Collection | `DataCatalog` (nested) |
| Topic | `Dataset` |
| Link (dataset) | `distribution` → `DataDownload` |
| Title | `name` |
| Updated date | `dateModified` |

schema.org also supports fields we may want later: publisher (`Organization`), data formats (`encodingFormat`), licence (`license`), spatial/temporal coverage.

### Comparison

| | JSON + Schema | JSON-LD |
|---|---|---|
| Simplicity | High | Moderate |
| LLM/tooling compatibility | Good | Indirect |
| Machine discoverability | Limited (needs additional context) | Self describing (semantic) |
| Search engine understanding | No | Yes (standard for SEO) |
| Implementation effort | Low | Moderate |

JSON + Schema is the foundation. JSON-LD layers on top without changing the underlying data or API.

### llms.txt

[llms.txt](https://llmstxt.org/) is an emerging, low effort convention for helping LLMs understand a site, but there’s currently no strong evidence major providers use it or that it improves AI citations. It’s harmless to add, but arguably much less impactful than structured approaches like APIs or well organized content, and should be treated as experimental rather than essential.

---

## Further investigation

- **CKAN catalogue integration** — to be genuinely useful to users, search needs to surface good quality dataset metadata from the existing CKAN catalogue alongside topic content. This means executing a federated search from our backend against the CKAN Solr index. Whether results are transparently merged with collection data or not is up for discussion. The results could be labelled as distinct or merged, which is a product question. This is dependent on the data quality work noted above.

- **MCP server** — an MCP server would allow users to search and browse topics directly from their LLM client of choice, without using our search interface at all. The server would be a thin layer combining two things: the JSON endpoints (for retrieving structured topic and collection data) and the search backends (for hybrid search via OpenSearch or PostgreSQL). Together these give an LLM the ability to search, retrieve, and reason over topic content without needing a browser.

- **Evaluation framework** — a systematic way to measure search quality has not been addressed yet. Standard approaches exist but they require a set of test queries paired with human judged relevant results. Building a small set of good representative queries would allow better comparison across approaches rather than relying on manual inspection.

- **Embedding model evaluation** — the model used with local testing (`Snowflake/snowflake-arctic-embed-s`) was chosen based on size and convenience. Running representative queries against different models on bigger bodies of content would help validate model choice. There are also APIs available for embeddings.

- **Amazon Bedrock or other service** - using lexical+semantic search as a basis we could post process list based search result to produce sythesised responses. This would involve sending results + user queries to Bedrock, OpenAI (other?) to synthesise a natural language response.

- **Amazon Bedrock Knowledge Bases** — a fully managed AWS service. You point it at your content and it handles chunking, embedding, vector storage, and retrieval with no self managed embedding pipeline, vector indexes, or search tuning required. It can also pass retrieved content to an LLM to generate synthesised answers rather than returning a list of results. Worth investigating early because if the product direction favours "ask a question, get an answer" over traditional search result lists, it could remove the need to build and maintain the search infrastructure described in this document. Pay per query pricing (retrieval and LLM inference fees). The trade off is less control over ranking and presentation, and tight coupling to AWS.

- 
