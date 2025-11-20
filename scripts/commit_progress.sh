#!/bin/bash
# Helper script to commit progress with a timestamp

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
MESSAGE="Progress update: $TIMESTAMP"

# Add all changes
git add -A

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "No changes to commit."
else
    # Commit with timestamp
    git commit -m "$MESSAGE"
    echo "✅ Committed: $MESSAGE"
    
    # Optionally push (uncomment if you want auto-push)
    # git push
    echo "💡 Run 'git push' to push to remote"
fi

