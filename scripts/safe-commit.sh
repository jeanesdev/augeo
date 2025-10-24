#!/bin/bash
# Safe commit script that ensures pre-commit hooks pass before committing
# Usage: ./scripts/safe-commit.sh "commit message"

if [ -z "$1" ]; then
    echo "Error: Commit message required"
    echo "Usage: ./scripts/safe-commit.sh \"your commit message\""
    exit 1
fi

COMMIT_MESSAGE="$1"
MAX_ATTEMPTS=3
ATTEMPT=1

echo "📝 Staging all changes..."
git add -A

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo ""
    echo "🔍 Running pre-commit hooks (attempt $ATTEMPT/$MAX_ATTEMPTS)..."

    # Run pre-commit hooks (allow it to fail, we'll check status)
    if pre-commit run --all-files; then
        # All hooks passed!
        echo ""
        echo "✅ All pre-commit checks passed!"
        echo "💾 Committing changes..."
        git commit -m "$COMMIT_MESSAGE"

        echo ""
        echo "✅ Commit successful!"
        git log -1 --oneline
        exit 0
    else
        # Hooks failed or made changes
        echo ""

        # Check if there are unstaged changes (hooks auto-fixed something)
        if ! git diff --quiet --exit-code; then
            echo "✨ Pre-commit hooks made auto-fixes"
            echo "📝 Re-staging modified files..."
            git add -A
            ATTEMPT=$((ATTEMPT + 1))

            if [ $ATTEMPT -le $MAX_ATTEMPTS ]; then
                echo "� Will retry with fixes applied..."
            fi
        else
            # Hooks failed but made no changes - manual intervention needed
            echo ""
            echo "❌ Pre-commit hooks failed with errors that cannot be auto-fixed."
            echo "Please review the errors above and fix them manually."
            exit 1
        fi
    fi
done

echo ""
echo "❌ Failed to pass pre-commit hooks after $MAX_ATTEMPTS attempts."
echo "This shouldn't happen - please investigate."
exit 1
