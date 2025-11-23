# CodeRabbit Setup Guide

This guide will help you set up CodeRabbit, an AI-powered code review assistant, for your repository.

## What is CodeRabbit?

CodeRabbit is an AI-powered code review tool that automatically reviews pull requests, provides suggestions, and helps maintain code quality. It integrates seamlessly with GitHub and provides:

- Automated code reviews on pull requests
- Security vulnerability detection
- Code quality suggestions
- Best practices recommendations
- Test coverage analysis
- PR description generation

## Prerequisites

- A GitHub account
- Repository admin or owner permissions
- The repository must be hosted on GitHub (public or private)

## Installation Steps

### 1. Install CodeRabbit GitHub App

1. Go to the [CodeRabbit GitHub Marketplace](https://github.com/marketplace/coderabbitai)
2. Click **"Install it for free"** or **"Set up a plan"**
3. Choose your installation option:
   - **All repositories**: CodeRabbit will work on all your repositories
   - **Only select repositories**: Choose specific repositories (recommended for initial setup)
4. Select your repository (e.g., `your-username/Thara`)
5. Click **"Install"**
6. Review and accept the permissions CodeRabbit requests

### 2. Verify Installation

After installation, CodeRabbit will:
- Create a `CodeRabbitAI` bot user that will appear in your repository
- Start automatically reviewing pull requests

### 3. Configuration

The repository already includes a `.coderabbit.yaml` configuration file that customizes CodeRabbit's behavior for this project. The configuration includes:

- **Review settings**: Automated reviews with focus on security, performance, and best practices
- **File filters**: Excludes generated files (migrations, logs, cache files)
- **Python-specific rules**: PEP 8 compliance, type hints, docstrings
- **Custom instructions**: Project-specific guidelines for Telegram bots, async patterns, and database queries

#### Configuration Options

You can customize the `.coderabbit.yaml` file to adjust:

- **Review mode**: `auto`, `request`, or `disabled`
- **Review status**: `auto` (auto-approve if no issues) or `manual`
- **Included/excluded file patterns**: Control which files get reviewed
- **Review categories**: Security, performance, documentation, etc.
- **Language-specific settings**: Python line length, docstring style, etc.

### 4. Test the Integration

1. Create a test pull request:
   ```bash
   git checkout -b test-coderabbit
   # Make some code changes
   git add .
   git commit -m "Test: Verify CodeRabbit integration"
   git push origin test-coderabbit
   ```

2. Open a pull request on GitHub from `test-coderabbit` to `main`

3. Wait for CodeRabbit to review (usually takes 1-2 minutes)

4. Check the PR comments - you should see CodeRabbit's review and suggestions

### 5. Configure Notifications (Optional)

You can configure CodeRabbit to notify you:
- When reviews are completed
- When critical issues are found
- Daily/weekly summaries

Configure these in the CodeRabbit web interface or GitHub App settings.

## Usage

### Automatic Reviews

CodeRabbit will automatically review:
- All pull requests to `main`, `master`, or `develop` branches
- Code changes matching configured file patterns
- Commit messages and PR descriptions

### Manual Review Request

You can request a review on any PR by:
1. Commenting `@coderabbitai review` in the PR
2. Or adding the `coderabbit-review` label to the PR

### Chat with CodeRabbit

You can ask CodeRabbit questions about your code:
1. Open a pull request
2. Comment with `@coderabbitai` followed by your question
3. Example: `@coderabbitai Can you explain this function?`

## Customization

### Adjust Review Focus

Edit `.coderabbit.yaml` to change review categories:

```yaml
review_categories:
  - security      # Security vulnerabilities
  - performance   # Performance optimizations
  - bug_risk      # Potential bugs
  - documentation # Documentation quality
  - best_practices # Best practices
  - style         # Code style
  - clarity       # Code clarity
  - maintainability # Maintainability
  - test_coverage # Test coverage
```

### Exclude Files from Review

Add patterns to the `ignore` section:

```yaml
ignore:
  - "**/migrations/versions/*.py"
  - "**/generated/**"
  - "**/*.min.js"
```

### Set Test Coverage Threshold

```yaml
workflows:
  test_coverage:
    enabled: true
    threshold: 80  # Minimum coverage percentage
```

## Cost Optimization

CodeRabbit offers a free tier with limited reviews per month. To optimize costs:

1. **Skip draft PRs**: Enable in config
   ```yaml
   cost_optimization:
     skip_draft: true
   ```

2. **Limit file count**: Review only smaller PRs
   ```yaml
   cost_optimization:
     max_files: 50
   ```

3. **Use request mode**: Only review when explicitly requested
   ```yaml
   reviews:
     mode: request  # Review only when @coderabbitai review is mentioned
   ```

## Troubleshooting

### CodeRabbit Not Reviewing PRs

1. Check that the GitHub App is installed:
   - Go to repository Settings → Integrations → Installed GitHub Apps
   - Verify CodeRabbit is listed

2. Check branch settings:
   - Ensure PR base branch is in `base_branches` list in `.coderabbit.yaml`

3. Check file filters:
   - Verify files match `include` patterns
   - Ensure files don't match `exclude` patterns

### Review Taking Too Long

- CodeRabbit typically reviews within 1-2 minutes
- Large PRs (>100 files) may take longer
- Check the CodeRabbit status in PR checks

### Too Many Suggestions

- Adjust `review_categories` to focus on specific areas
- Enable `auto_apply: true` for non-critical suggestions (use with caution)
- Set more specific `path_filters` to exclude certain directories

## Advanced Features

### Issue Tracking Integration

CodeRabbit can link PRs to issues:
1. Configure in CodeRabbit web interface
2. Link issues in PR description: `Fixes #123` or `Related to #456`

### Team Reports

Set up automated reports:
1. Go to CodeRabbit web interface
2. Configure daily/weekly reports
3. Choose report templates

### CI/CD Integration

CodeRabbit can analyze CI/CD logs:
1. Ensure CI/CD outputs are visible in PR checks
2. CodeRabbit will automatically analyze failures
3. Provides remediation suggestions

## Best Practices

1. **Review CodeRabbit's suggestions carefully**: Not all suggestions are mandatory
2. **Use it as a learning tool**: Understand why certain patterns are recommended
3. **Configure for your team**: Adjust settings based on your codebase and preferences
4. **Combine with manual reviews**: CodeRabbit complements, doesn't replace, human reviewers
5. **Keep config updated**: Update `.coderabbit.yaml` as your project evolves

## Resources

- [CodeRabbit Documentation](https://docs.coderabbit.ai/)
- [CodeRabbit GitHub App](https://github.com/apps/coderabbitai)
- [Configuration Reference](https://docs.coderabbit.ai/getting-started/configure-coderabbit)
- [Setup Best Practices](https://docs.coderabbit.ai/guides/setup-best-practices/)

## Support

- GitHub Issues: [CodeRabbit Issues](https://github.com/Codium-ai/pr-agent/issues)
- Documentation: [docs.coderabbit.ai](https://docs.coderabbit.ai/)
- Community: Check CodeRabbit's GitHub discussions

