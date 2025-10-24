#!/bin/bash
# Safe commit script that ensures pre-commit hooks pass before committing
# Usage: ./scripts/safe-commit.sh "commit message"

set -e  # Exit on any error

if [ -z "$1" ]; then
    echo "Error: Commit message required"
    echo "Usage: ./scripts/safe-commit.sh \"your commit message\""
    exit 1
fi

COMMIT_MESSAGE="$1"

echo "📝 Staging all changes..."
git add -A

echo ""
echo "🔍 Running pre-commit hooks..."
# Run pre-commit hooks manually first
# This will auto-fix what it can and show what needs manual fixing
pre-commit run --all-files

# Check if pre-commit made any changes
if ! git diff --quiet --exit-code; then
    echo ""
    echo "✨ Pre-commit hooks made formatting changes"
    echo "📝 Re-staging modified files..."
    git add -A

    echo ""
    echo "🔍 Running pre-commit hooks again to verify..."
    # Run again to ensure everything passes
    pre-commit run --all-files
fi

echo ""
echo "✅ All pre-commit checks passed!"
echo "💾 Committing changes..."
git commit -m "$COMMIT_MESSAGE"

echo ""
echo "✅ Commit successful!"
git log -1 --oneline
