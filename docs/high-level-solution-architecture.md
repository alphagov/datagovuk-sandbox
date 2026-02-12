# High level Solution Architecture

This note summarises three viable options for future iteration of curated dataset publishing, focusing on the major building blocks rather than very specific implementation details.

Diagrams showing the functional structure is here: [high-level-solution-architecture-diagrams.md](high-level-solution-architecture-diagrams.md)

> [!IMPORTANT]
> Out of scope in this document is any discussion of existing Find app (rails user facing front end) or CKAN instance for existing data.gov.uk datasets. The assumption is that
> they will continue to run and therefore support `/datasets/*` URL paths for now. The future place of CKAN in the overall solution can be reviewed, discussed elsewhere.
>
> Also the assumption is that the deployment target for any public facing website/application will be on NDL owned AWS, **not** within the existing GDS estate.

## Goals
- Provide a manageable editorial workflow for markdown/structured content, with previews where possible.
- Support background validation (e.g. checking of URLs) and data refresh jobs with configurable cadences.
- Keep data processing tasks pluggable so we can monitor external data sources and regenerate JSON artefacts (used by charts/graphs) on demand or via schedules.
- Stay small enough for a compact team to operate while leaving room to evolve.
- Support path based routing such that requests for existing `/datasets/*` URL paths are routed to the existing Find application.

## Terminology note
We use "Admin UI" rather than "CMS" because the intent is a very basic editing application limited to a pre-defined site structure (users can add pages, but not alter the structure), not a full CMS with expansive modelling and workflow features.

**Note** that the current design of the pages is content light with one or two paragraphs per dataset page for content editors to manage. If the number and types of pages are expected to increase substantially a more full featured CMS may be appropriate.

## Option 1 – GitHub managed static site
Markdown and scripts for site generation, validation and refresh of visualisation data live in a GitHub repository. Editors edit markdown in GitHub. GitHub Actions pull visualisation data from external sources, transform it into the formats needed for charts, and check URLs in front matter on a daily basis. Other scripts render pages from markdown, triggered by commits to `main`, and deployment pushes the generated content to S3, fronted by CloudFront.

**Benefits**
- Leverages GitHub workflows and pull requests for editorial review and change control. Editors work on draft branches and create pull requests when pages are ready for review.
- A staging/preview environment provides previews of changes before merging to main and publishing to production.
- Reproducible builds with a clear audit trail in the repository.
- Minimal runtime surface area if all rendering happens in CI.

**Trade-offs**
- Editorial UX depends on GitHub. Editors need to have familiarity with markdown and github workflows.
- Build times directly impact publishing latency. Cache invalidation is also a factor.
- Data refresh scripts need developer effort to create and maintain.
- Note: GitHub Pages is not a fit because we need path-based routing (e.g., `/datasets/*`) to a separate origin.
- Additional infrastructure setup needed to support search and redirects if needed. See section below on [redirect and search](#redirect-and-search)

## Option 2 – Admin UI + static pages
An Admin UI app (Flask/Django/FastAPI) stores content and metadata in PostgreSQL. Editors manage content there. Background workers (ARQ/Redis or similar) validate URLs, fetch/transform external data sources and write back derived JSON/content in the database. The workers then publish rendered HTML to a static site on S3, fronted by CloudFront.

**Benefits**
- Stable content that benefits from CDN performance and low hosting cost.
- Clear separation between editorial tooling and public delivery mechanism.
- Reduced attack surface area.
- 
**Trade-offs**
- Publishing waits for build runs and orchestration adds operational complexity.
- Running and maintaining the Admin UI application brings operational costs similar to Option 3 for the editorial side, while still relying on the static delivery model for the public site.
- Content lives in a database rather than in version-controlled files, so database backup and content recovery become concerns (in Option 1, Git serves as the backup and audit trail).
- Additional infrastructure setup needed to support search and redirects if needed. See section below on [redirect and search](#redirect-and-search)

## Option 3 – Admin UI + server side rendering
A single web app handles Admin UI editing and public page rendering, with background workers running alongside it. Editors can edit and view content directly in a single application. Visitors request pages from the same app. The web app schedules/enqueues jobs to Redis - workers check published URLs as well as fetch/transform external data sources and store results in PostgreSQL.

**Benefits**
- Fast iteration: one deploy updates the Admin UI, public views, and data processors.
- Previews are just draft routes - scheduling + permissions live in one database.
- Good stepping stone for additional functionality.

**Trade-offs**
- Always-on runtime requires ongoing operational commitment, maintaining uptime, patching, and monitoring compared to static hosting.
- Requires stricter hardening because the public application and admin application are the same stack.

## Cross-cutting considerations
- **Path based routing**: If specific URL patterns (e.g., `/datasets/*`) must be handled by a separate application, use CDN path-based behaviours to route those requests to an alternate origin while the rest of the site is served from S3 or the main app.
- **Automation for data and URL checks**: Use automation to validate URLs, fetch and transform small data extracts for visualisations. Keep this lean so it supports the site without becoming a major platform in its own right.
- **Background jobs**: Use scheduled workflows (GitHub Actions in Option 1) or Redis-backed queues (RQ/ARQ in Options 2/3) for URL checks and data refresh. Graduate to heavier orchestration only if needed.
- **Hosting**: All options benefit from CDN fronting. Option 1 can be just S3 + CloudFront. Option 2 adds a small Admin UI service (ECS/Fargate, App Runner or Elastic Beanstalk) plus Redis/PostgreSQL. Option 3 needs a full application tier (ECS/Fargate, App Runner or Elastic Beanstalk) plus Redis/PostgreSQL.
- **Previews**: Option 1 requires deployment to a staging environment to fully preview rendered pages. Options 2 and 3 can provide in application page previews within the Admin UI.

### Additional notes
In order to keep this document reasonably brief a number of cross cutting implemntation questions and notes are captured here: [Additional implementation notes will be captured here: [implementation-notes.md](implementation-notes.md)]()

> [!NOTE]
> With regard to hosting the assumption is this work will be done in a new AWS account, however we need to recognise that we may have to remain withing govuk AWS estate. If that's the case we can review and see what is most appropriate.

## Tech notes
- **Framework choice**: Django (without Wagtail) plus its task system offers a batteries-included route. Wagtail is a capable, mature and well supported CMS but may be heavier than needed for a narrow content model and small team. Flask remains attractive for a lightweight Admin UI if we value minimal surface area - pair it with RQ for background work. FastAPI is also a possible choice.
- **FastAPI + Redis**: If we favour async IO or want "out of the box" API capabilities, FastAPI with an ARQ/Redis worker provides an integrated API and simple task queue and makes it easy to expose both Admin UI APIs and background job control.
- **Static tooling**: A benefit of options 1 and 2. Simpler infrastructure traded off against a more complex build and deploy strategy.
- **Preview strategy**: With static options we could maintain a staging/preview environment. For a monolithic admin ui app, we could provide preview URLs on applications accessible via allow listed IP range/VPN.

### Redirect and search<a name="redirect-and-search"></a>

> [!NOTE]
> If we adopt a static deployment approach then it's worth noting that additional development and infrastucture would be needed to support redirects and search.
>
> In both cases additional moving parts would need to be specified. Both redirect and search can be implemented using core products offered in AWS, but we need to spend the time to think through the implementation.
> 
> Redirects could be handled by Cloudfront functions and Cloudfront key value store. Lamda@Edge would also a possibility, but final approach can be discussed.
>     
> Search is a more complex question in that it would mean running an indexing service and a search service callable from the static site. Both could interact with an AWS managed search index such as AWS OpenSearch. We could use AWS Lamdba to ingest data into search index. Lambda could also be used (accessible via API Gateway) to execute search on client request and return results.
>
> Importantly in order to support users with JS diabled, the search service, whether using Lambda or a longer running service, should be able to return results as HTML not just JSON.


## Recommendations

For an effective starting point, **Option 1 (GitHub managed static site)** is recommended. This approach offers the lowest operational cost and complexity, leveraging Git based workflows for content management, build and deployment. It allows the team to focus on establishing a suitable content structure and reliable maintenance, validation and data processing pipelines without the overhead of maintaining more elaborate application architecture and infrastructure.

Importantly, this choice doesn't preclude future evolution. The architecture provides a coherent migration path to **Option 2** by developing an Admin UI whose workers would take over the role of generating the static site. Similarly, the content and data transformation scripts can be readily adapted for **Option 3** if a fully dynamic, server rendered application becomes necessary. However, migration is not zero-cost: moving from Option 1 to Option 2 or 3 means shifting from "files as source of truth" to "database as source of truth", which requires content migration and changes to how content is authored and managed.

By beginning with a simple, file based source of truth, the project remains easy to understand and is well positioned to scale its infrastructure and functionality in line with future requirements.


## What factors would drive option upgrade

- Number of topics/dataset pages makes management in Github difficult - a bit vague but we need to define difficult, e.g. difficulty finding the page to work on? 
- We want outside users/publishers to be able to provide/publish datasets. In that case we may want to build an application to support that, e.g. an admin UI.
- The pages and/or site structure becomes more complex and could benefit from having some application/tooling around management of the site and pages.
