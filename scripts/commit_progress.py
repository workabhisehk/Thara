#!/usr/bin/env python3
"""
Helper script to commit progress with a timestamp.
Usage: python scripts/commit_progress.py [message]
"""
import subprocess
import sys
from datetime import datetime

def commit_progress(custom_message=None):
    """Commit all changes with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if custom_message:
        message = f"{custom_message} - {timestamp}"
    else:
        message = f"Progress update: {timestamp}"
    
    # Add all changes
    subprocess.run(["git", "add", "-A"], check=True)
    
    # Check if there are changes
    result = subprocess.run(
        ["git", "diff", "--staged", "--quiet"],
        capture_output=True
    )
    
    if result.returncode == 0:
        print("No changes to commit.")
        return
    
    # Commit
    subprocess.run(["git", "commit", "-m", message], check=True)
    print(f"✅ Committed: {message}")
    print("💡 Run 'git push' to push to remote")

if __name__ == "__main__":
    custom_msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    commit_progress(custom_msg)

