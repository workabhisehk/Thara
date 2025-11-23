# CodeRabbit Installation Steps

## Quick Install Guide

1. **Go to CodeRabbit Installation Page**
   - URL: https://github.com/apps/coderabbitai/installations/new
   - Or visit: https://github.com/marketplace/coderabbitai

2. **Sign in to GitHub** (if not already signed in)

3. **Select Installation Type**
   - **Option A**: Install on all repositories
   - **Option B**: Install on only select repositories (recommended)
     - Select: `workabhisehk/Thara`

4. **Review Permissions**
   - CodeRabbit needs:
     - Read access to pull requests
     - Write access to comments
     - Read access to repository metadata
   
5. **Click "Install"**

6. **Verify Installation**
   - Go to your repository: https://github.com/workabhisehk/Thara
   - Go to Settings → Integrations → Installed GitHub Apps
   - Verify CodeRabbit is listed

7. **Test It Out**
   ```bash
   # Create a test branch
   git checkout -b test-coderabbit
   
   # Make a small change
   echo "# Test comment" >> README.md
   
   # Commit and push
   git add README.md
   git commit -m "Test: Verify CodeRabbit integration"
   git push origin test-coderabbit
   ```
   
   - Create a PR from `test-coderabbit` to `main`
   - Wait 1-2 minutes for CodeRabbit to review
   - Check PR comments for review feedback

## Your Repository Details
- Repository: `workabhisehk/Thara`
- Base branches configured: `main`, `master`, `develop`
- Configuration file: `.coderabbit.yaml` ✅

## What's Already Configured

✅ `.coderabbit.yaml` configuration file created
✅ Documentation in `docs/CODERABBIT_SETUP.md`
✅ README updated with CodeRabbit info
✅ Python-specific rules configured
✅ File exclusions set (migrations, logs, cache files)
✅ Custom instructions for Telegram bot codebase

## Need Help?

- Full documentation: `docs/CODERABBIT_SETUP.md`
- CodeRabbit Docs: https://docs.coderabbit.ai/
- GitHub App: https://github.com/apps/coderabbitai

