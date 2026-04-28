#!/bin/bash

# create-release.sh
# Purpose:
#   Cherry-pick one commit into release/1.0.0, create a working release branch,
#   review the change, and optionally push the branch to origin.
#
# Usage:
#   ./create-release.sh <COMMIT_HASH>
#
# Example:
#   ./create-release.sh abc1234
#
# Notes:
#   - Only one input is required: the commit hash.
#   - The script creates a branch from release/1.0.0.
#   - The new branch name uses the short commit hash.
#   - If the commit is a merge commit, it uses cherry-pick -m 1.
#   - If the commit is a normal commit, it uses a standard cherry-pick.

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_step() {
    echo -e "\n${BLUE}====================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}====================================================${NC}\n"
}

# Step 0: Validate input
if [ $# -lt 1 ]; then
    print_error "Missing argument"
    echo ""
    echo "Usage: $0 <COMMIT_HASH>"
    echo ""
    echo "Example:"
    echo "  $0 abc1234"
    echo ""
    exit 1
fi

COMMIT_HASH=$1

print_step "STEP 1: Validating commit hash"

print_info "Using provided commit hash: $COMMIT_HASH"

# Verify the commit exists
if ! git rev-parse --verify "$COMMIT_HASH" >/dev/null 2>&1; then
    print_error "Invalid commit hash: $COMMIT_HASH"
    exit 1
fi

# Resolve full and short commit hashes
FULL_COMMIT_HASH=$(git rev-parse "$COMMIT_HASH")
SHORT_COMMIT_HASH=$(git rev-parse --short "$COMMIT_HASH")

print_success "Commit exists: $FULL_COMMIT_HASH"

print_step "STEP 2: Setting up release branch"

# Current branch for reference
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
print_info "Current branch: $CURRENT_BRANCH"

# Create release branch name
RELEASE_BRANCH="release/1.0.0-${SHORT_COMMIT_HASH}"
print_info "Target release branch: $RELEASE_BRANCH"

# Checkout release/1.0.0
print_info "Checking out release/1.0.0..."
git checkout release/1.0.0
print_success "Checked out release/1.0.0"

# Pull latest
print_info "Pulling latest from origin/release/1.0.0..."
git pull origin release/1.0.0
print_success "Pulled latest changes"

# Create or reuse working branch
print_info "Creating working branch: $RELEASE_BRANCH..."
if git rev-parse --verify "$RELEASE_BRANCH" >/dev/null 2>&1; then
    print_warning "Branch $RELEASE_BRANCH already exists. Checking it out..."
    git checkout "$RELEASE_BRANCH"
else
    git checkout -b "$RELEASE_BRANCH"
fi
print_success "Checked out branch: $RELEASE_BRANCH"

print_step "STEP 3: Reading commit details"

# Get commit message
COMMIT_MESSAGE=$(git log -1 --pretty=format:"%s" "$FULL_COMMIT_HASH")
print_info "Commit message: $COMMIT_MESSAGE"

# Detect whether commit is a merge commit
PARENT_COUNT=$(git rev-list --parents -n 1 "$FULL_COMMIT_HASH" | awk '{print NF-1}')

if [ "$PARENT_COUNT" -gt 1 ]; then
    IS_MERGE_COMMIT="true"
    print_info "Commit type: merge commit"
else
    IS_MERGE_COMMIT="false"
    print_info "Commit type: normal commit"
fi

print_step "STEP 4: Cherry-picking commit"

print_info "Cherry-picking commit: $FULL_COMMIT_HASH..."

if [ "$IS_MERGE_COMMIT" = "true" ]; then
    if git cherry-pick -m 1 "$FULL_COMMIT_HASH"; then
        print_success "Successfully cherry-picked merge commit"
    else
        print_error "Cherry-pick failed. There may be conflicts."
        echo ""
        print_warning "Please resolve conflicts manually and then run:"
        echo "  git cherry-pick --continue"
        echo "  git push origin $RELEASE_BRANCH"
        exit 1
    fi
else
    if git cherry-pick "$FULL_COMMIT_HASH"; then
        print_success "Successfully cherry-picked commit"
    else
        print_error "Cherry-pick failed. There may be conflicts."
        echo ""
        print_warning "Please resolve conflicts manually and then run:"
        echo "  git cherry-pick --continue"
        echo "  git push origin $RELEASE_BRANCH"
        exit 1
    fi
fi

print_step "STEP 5: Verifying changes"

print_info "Changes in the cherry-picked commit:"
echo ""
git show --stat --oneline HEAD
echo ""

print_step "STEP 6: Ready to push"

print_success "All steps completed successfully!"
echo ""
print_info "Your changes are ready. Next steps:"
echo ""
echo "1. Review the changes above"
echo ""
echo "2. Push the branch:"
echo "   ${BLUE}git push origin $RELEASE_BRANCH${NC}"
echo ""
echo "3. Create a PR from ${BLUE}$RELEASE_BRANCH${NC} into ${BLUE}release/1.0.0${NC}"
echo ""
echo "4. After PR is merged, create a new patch tag:"
echo "   ${BLUE}git checkout release/1.0.0${NC}"
echo "   ${BLUE}git pull origin release/1.0.0${NC}"
echo "   ${BLUE}git tag -a v1.0.0-patch-N -m 'Release patch N'${NC}"
echo "   ${BLUE}git push origin v1.0.0-patch-N${NC}"
echo ""
echo "5. Deploy the tag to Integration using your CI/CD pipeline"
echo ""

# Ask if user wants to push now
read -p "Do you want to push the branch now? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Pushing branch to origin..."
    git push origin "$RELEASE_BRANCH"
    print_success "Branch pushed successfully!"
    echo ""
    print_info "Next: Create a PR from $RELEASE_BRANCH into release/1.0.0"
else
    print_info "You can push manually later with: git push origin $RELEASE_BRANCH"
fi