# data.gov.uk - branching and release

## Trunk based approach: lighter weight alternative?

> [!Note]
> Note is approach is not dramatically different to what we currently do, albeit with a lot of manual intervention.
> It could represent a more incremental approach to a better release process with solid automation

---

## Overview

This document outlines a trunk-based branching strategy as a potential alternative to the GitFlow-like approach documented in `data-gov-uk-release-strategy.md`. The goal is to evaluate whether a simpler model could reduce overhead, shorten feedback loops, and move the team closer to a continuous delivery model.

---

## How it differs from GitFlow

| Aspect | GitFlow Strategy | Trunk based Strategy |
|--------|-----------------|---------------------|
| Long-lived branches | `main`, `develop`, `release/*` | `main` only |
| Feature integration | Merge to `develop` | Merge to `main` |
| Release mechanism | `release/*` branch | Tag on `main` |
| Hotfix route | `hotfix/*` → `main` + `develop` | `hotfix/*` → `main` |
| Branch count | Higher | Lower |

In short: there is no `develop` branch, no long-lived `release/*` branches, and fewer moving parts to coordinate.

---

## Core idea

- `main` is always releasable.
- All work integrates into `main` via short-lived branches and squash merges.
- Releases are cut by tagging `main`, no release branches needed.
- Hotfixes follow the same path as features: branch from `main`, fix, merge back.
- Small, frequent merges replace large, infrequent ones.

---

## Environment promotion

| Environment | Source | Trigger |
|-------------|--------|---------|
| Integration | `main` (HEAD) | Automatic on merge to `main` |
| STAGING | `main` (HEAD) | Manual promotion from Integration |
| PROD | `main` (tagged) | New version tag (e.g. `v1.2.0`) |

Rollback is straightforward: redeploy the previous known good tag to PROD, then fix forward on `main`.

---

## Moving towards continuous delivery

A trunk based model naturally supports a move towards continuous delivery. With all changes flowing through a single branch and deploying automatically to Integration on every merge, the team gets faster, consistent feedback on the state of the software.

However, this only works if the team has confidence in what is being merged. **This approach requires stronger automated testing than a GitFlow model.** Without reliable automated test coverage, unit, integration, and acceptance, the risk of breaking `main` increases significantly.

Key enablers:

- **Automated test suites** that run on every PR and block merges on failure
- **Feature flags** to decouple deployment from release when needed
- **Short-lived branches** (ideally merged within a day) to minimise drift and merge conflicts
- **Frequent merges** to `main` — at least daily

---

## Branch Protection

- CI checks must pass before merge
- Auto delete merged branches

---

## Open question: DEV Environment

The current infrastructure has three environments: integration, staging, and prod. A DEV environment is not yet provisioned but could provide an earlier feedback loop, particularly for testing infrastructure dependent behaviour before changes reach integration.

Key decisions needed:

- Does DEV deploy from feature branches (pre-merge validation) or from `main` (post-merge)? - we currentl do this from time to time manually
- What infrastructure is required, and who owns/provisions it?

---

## Summary

Trunk based branching trades the structure and ceremony of GitFlow for speed and simplicity. It may suit teams that want to move towards continuous delivery, but it demands investment in automated testing and CI to maintain confidence in the trunk.
