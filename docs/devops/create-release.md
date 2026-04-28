## Release Patch Workflow Using create-release.sh

### Purpose

This script create-release.sh standardizes how Data Gov UK team moves a single approved change
into the release branch.

Use it to promote one specific commit into release/1.0.0 without merging
an entire feature branch.

It reduces risk. It keeps release changes small and traceable.

------------------------------------------------------------------------

### What This Script Does

It automates the full patch flow:

-   Validates the commit hash
-   Switches to release/1.0.0
-   Pulls the latest release code
-   Creates a dedicated release branch
-   Cherry-picks the selected commit
-   Detects merge vs normal commits automatically
-   Shows the resulting changes
-   Guides the next steps
-   Optionally pushes the branch

------------------------------------------------------------------------

### When To Use It

Use this script when:

-   Need to move one fix into production
-   The commit is already tested and approved
-   Wanted a minimal, controlled release change

Do not use this script when:

-   Multiple dependent commits are required
-   The commit relies on code not present in release/1.0.0
-   A full branch merge is safer

------------------------------------------------------------------------

### Prerequisites

Before running the script:

-   Have the repository cloned
-   Have access to origin
-   Have local repo is clean

Check:

git status

------------------------------------------------------------------------

### Setup

Make the script executable:

chmod +x create-release.sh

------------------------------------------------------------------------

### Usage

Run the script with a commit hash:

./create-release.sh `<COMMIT_HASH>`{=html}

For Example:

./create-release.sh 8f3c2ab

------------------------------------------------------------------------

### Step-by-Step Flow

#### Step 1. Validate Input

The script checks:

-   A commit hash is provided
-   The commit exists in the repository

If invalid, it stops immediately.

------------------------------------------------------------------------

#### Step 2. Prepare Release Branch

The script:

-   Switches to release/1.0.0
-   Pulls the latest changes from origin
-   Creates a working branch

Branch format:

release/1.0.0-`<short_commit_hash>`{=html}

Example:

release/1.0.0-8f3c2ab

If the branch already exists, it reuses it.

------------------------------------------------------------------------

#### Step 3. Analyze Commit

The script reads:

-   Commit message
-   Number of parents

Merge commits need special handling. Normal commits use standard
cherry-pick.

------------------------------------------------------------------------

#### Step 4. Cherry-Pick Commit

The script applies the commit into the release branch.

Behavior:

-   Merge commit uses git cherry-pick -m 1
-   Normal commit uses git cherry-pick

If conflicts occur:

-   The script stops
-   You resolve conflicts manually

------------------------------------------------------------------------

#### Step 5. Verify Changes

The script shows:

git show --stat

Review this carefully before proceeding.

------------------------------------------------------------------------

#### Step 6. Prepare for Push

The script prints next steps and asks if want to push.

------------------------------------------------------------------------

### After Running the Script

#### 1. Push the Branch

git push origin release/1.0.0-8f3c2ab

------------------------------------------------------------------------

#### 2. Create Pull Request

-   Source: release/1.0.0-8f3c2ab\
-   Target: release/1.0.0

Ensure CI checks pass and review is completed.

------------------------------------------------------------------------

#### 3. Merge the PR

Merge into release/1.0.0 after approval.

------------------------------------------------------------------------

#### 4. Create Release Tag

git checkout release/1.0.0 git pull origin release/1.0.0 git tag -a
v1.0.0-patch-N -m "Release patch N" git push origin v1.0.0-patch-N

------------------------------------------------------------------------

#### 5. Deploy

Trigger deployment using the CI/CD pipeline.

------------------------------------------------------------------------

### Conflict Handling

If cherry-pick fails:

git status

Resolve conflicts.

Then:

git add . git cherry-pick --continue

Push:

git push origin `<RELEASE_BRANCH>`{=html}

------------------------------------------------------------------------

### Best Practices

-   Verify the commit before running
-   Avoid commits with dependencies
-   Keep release branches focused on one change
-   Always review changes
-   Do not skip PR review
-   Use consistent tagging

------------------------------------------------------------------------

### Naming Convention

Branch:

release/1.0.0-`<short_commit_hash>`{=html}

Tag:

v1.0.0-patch-N

------------------------------------------------------------------------

### Common Mistakes

-   Using dependent commits
-   Skipping review
-   Running on dirty repo
-   Forgetting to pull latest
-   Wrong PR target branch

------------------------------------------------------------------------

### Summary

One commit. One branch. One PR. One patch.

This keeps releases controlled and traceable.
