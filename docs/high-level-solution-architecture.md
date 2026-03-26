# High Level Solution Architecture

## Architecture overview

The solution is a full-stack Django web application with a deliberately minimal footprint:

- **No database** - there is no persistence layer needed at this stage.
- **No admin interface** - content is not managed through the application.
- **Markdown as content** - pages are authored as markdown files that live in the application repository. The Django app renders them dynamically on each request.
- **Content editing happens in Github** - editors work with markdown files directly in the Github, using pull requests for review.

```mermaid
flowchart LR
    editor([Editors])
    repo[("Github repository\n(application + markdown content)")]
    app["Django app\n(renders markdown dynamically)"]
    visitor([Visitors])

    editor -->|Edit markdown via PR| repo
    repo -->|Content bundled in app| app
    visitor -->|Request pages| app

    classDef user fill:#2D6A4F,stroke:#1B4332,color:#FFFFFF
    class editor,visitor user
```

## Deployment

The application lives in a new repository (separate from this current find application repo). It is containerised and deployed into an existing EKS cluster.

- **Docker image** built in CI/CD on merge to `main`.
- **EKS pods** runs the Django app in the existing cluster.
- **Fastly CDN** sits in front of the application

```mermaid
flowchart LR
    editor([Editor])
    github["Github"]
    cicd["CI/CD pipeline"]
    image["Docker image"]
    eks["EKS pods\n(Django app)"]
    cdn["Fastly CDN"]
    visitor([Visitors])

    editor -->|Merge PR| github
    github -->|Trigger build| cicd
    cicd -->|Build & push| image
    image -->|Deploy| eks
    eks -->|Origin| cdn
    visitor -->|Request pages| cdn

    classDef user fill:#2D6A4F,stroke:#1B4332,color:#FFFFFF
    class editor,visitor user
```

## Deployment pipeline

Because markdown content is bundled inside the application image, every content change requires an application deployment. The pipeline therefore needs to be as quick and frictionless as possible.

**Promotion flow:**

1. **Merge to `main`** - already automatically deploys to the **integration** environment. No manual intervention required.
2. **Integration to staging** - the integration deployment automatically sets up a stage gate for staging promotion. A human accepts/triggers the promotion, but the gate is created without manual setup of copying tags/shas.
3. **Staging to production** - same pattern: the staging deployment sets up the production gate automatically; a human accepts/triggers the promotion.

```mermaid
flowchart LR
    merge["Merge to main"]
    int["Integration\n(auto-deploy)"]
    gate1{{"Stage gate\n(auto-created)"}}
    staging["Staging\n(human-triggered)"]
    gate2{{"Stage gate\n(auto-created)"}}
    prod["Production\n(human-triggered)"]

    merge --> int
    int --> gate1
    gate1 --> staging
    staging --> gate2
    gate2 --> prod
```

The key constraint is that the pipeline from merge to production must be streamlined enough that content updates aren't held up by complex manual promotion processes.

## What this approach enables

Running a Django application rather than a static site removes several categories of infrastructure complexity and incremental evolution paths are still available.

### Migration path to a database and admin interface

The solution starts with no database, but Django makes it straightforward to add one if needed. 

If the volume of content grows such that content editing via github becomes to onerous, frontmatter metadata and page content can be migrated into PostgreSQL and a lightweight admin interface built, without changing the hosting or deployment model. The app is already running; adding a database is a configuration change, not an architecture change. Even if the complexity of the site reaches the point that a full blown CMS is needed, there are upgrade paths for example to Wagtail which is a Django based CMS.

### Search without additional infrastructure

With a static site, search requires a separate indexing pipeline, a search service (e.g. OpenSearch), and an API layer (Lambda + API Gateway) to query it. 

A Django app can implement search server side, hether that's simple content scanning for a small number of pages or a database backed search index later. If search needs scale beyond what the app can handle directly, content can be pushed to an AWS managed search offering from the application itself, keeping the indexing pipeline simple and avoiding the need for separate Lambda functions or API Gateway layers.

### Redirects in application code

Redirects are handled natively in Django's URL configuration or views. There is no need for CDN level or reverse proxy URL rewriting (Cloudfront Functions, Lambda@Edge, or Fastly VCL) to manage redirect rules. Adding, changing, or removing redirects is a code change.

### Clean URL routing

Static sites on S3 require careful handling of trailing slashes, `index.html` conventions, and Cloudfront Functions to normalise URLs. Django's URL routing handles clean URLs (`/collection/business-and-economy`) natively with no CDN configuration needed.

### Simplified security model

The previously discussed static site approach required Github Actions to have write access to an S3 bucket in AWS, raising questions about cross account access and credential management. With content bundled in the Docker image, the deployment pipeline pushes a container image to a registry and deploys to EKS, a standard CI/CD pattern that doesn't require granting external systems direct access to serving infrastructure.
