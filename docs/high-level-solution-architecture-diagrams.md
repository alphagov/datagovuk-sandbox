# High level Solution Architecture diagrams

Functional architecture for options described here [high-level-solution-architecture.md](high-level-solution-architecture.md).

## Option 1 – GitHub managed static site
```mermaid
flowchart LR
    data_sources[(External Data Sources)]

    editor([Editors])

    subgraph REPO["GitHub repository"]
        content[("Markdown content & visualisation data")]
    end

    subgraph CI["GitHub actions"]
        data_jobs["Fetch/transform visualisation data"]
        url_checks["URL checks"]
        build["Render pages"]
    end

    static_site["Static site - S3 + CloudFront"]
    find_app["Find app (separate origin)"]
    visitor([Public Visitors])

    data_sources ~~~ CI
    editor -->|Edit markdown| content
    content -->|Commit to main| build
    data_jobs -->|Fetch & transform| data_sources
    data_jobs -->|Write visualisation data| content
    url_checks -->|Check front matter URLs| content
    build -->|Publish HTML/JSON| static_site
    visitor -->|View content| static_site
    visitor -->|/datasets/*| find_app

    classDef user fill:#2D6A4F,stroke:#1B4332,color:#FFFFFF
    class editor,visitor user
```

## Option 2 – Admin UI + static pages
```mermaid
flowchart LR
    subgraph AdminUI["Admin + background tasks"]
        admin_ui_app["Admin UI - Flask/Django/FastAPI"]
        queue[("Redis")]
        workers["Background Workers (ARQ/Redis)"]
        db[("PostgreSQL - content")]
    end

    subgraph STATIC["Static deployment"]
    static_site["Static site - S3 + CloudFront"]
    find_app["Find app (separate origin)"]
    end

    editor([Editors])
    visitor([Public Visitors])
    data_sources[(External Data Sources)]
    editor -->|Add pages & edit markdown| admin_ui_app
    admin_ui_app -->|Schedule tasks| queue
    admin_ui_app -->|Manage content| db
    queue -->|Process tasks| workers
    workers -->|Fetch & transform external data| data_sources
    workers -->|Fetch page content| db
    workers -->|Publish HTML| static_site
    workers -->|Validate URLs| db
    visitor -->|View content| static_site
    visitor -->|/datasets/*| find_app

    classDef user fill:#2D6A4F,stroke:#1B4332,color:#FFFFFF
    class editor,visitor user
```

## Option 3 – Admin UI + Server side rendering
```mermaid
flowchart LR
    subgraph MONO["Monolithic application with background tasks"]
        web_app["Web app Flask/Django/FastAPI"]
        db[("PostgreSQL - content")]
        workers["Background workers (ARQ/Redis or similar)"]
        queue[("Redis")]
    end

    editor([Editors])
    visitor([Public Visitors])
    find_app["Find app (separate origin)"]
    data_sources[(External Data Sources)]

    editor -->|Edit content| web_app
    visitor -->|Request pages| web_app
    visitor -->|/datasets/*| find_app
    web_app --> db
    web_app -->|Schedule/enqueue jobs| queue
    workers -->|Fetch & transform external data| data_sources
    workers -->|Store results| db
    queue -->|Process tasks| workers

    classDef user fill:#2D6A4F,stroke:#1B4332,color:#FFFFFF
    class editor,visitor user
```
