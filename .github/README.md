# GitHub Templates for LibreELEC Backupper

This directory contains templates for GitHub issues, pull requests, and wiki pages to maintain consistency and quality in project contributions.

## Directory Structure

```
.github/
├── ISSUE_TEMPLATE/           # Issue templates
│   ├── bug_report.md         # Template for bug reports
│   ├── feature_request.md    # Template for feature requests
│   ├── documentation.md      # Template for documentation improvements
│   └── config.yml            # Configuration for issue templates
├── PULL_REQUEST_TEMPLATE/    # Pull request templates
│   └── pull_request_template.md  # Template for pull requests
├── pull_request_template.md  # Default pull request template
└── wiki-templates/           # Wiki page templates
    ├── feature_documentation.md  # Template for documenting features
    ├── installation_guide.md     # Template for installation guides
    ├── troubleshooting_guide.md  # Template for troubleshooting guides
    └── home.md                   # Template for wiki home page
```

## Using Issue Templates

When creating a new issue on GitHub, you'll be prompted to choose a template:
- **Bug Report**: Use for reporting bugs or unexpected behavior
- **Feature Request**: Use for suggesting new features or enhancements
- **Documentation Improvement**: Use for suggesting documentation changes

## Using Pull Request Templates

When creating a new pull request, the default template will be automatically applied. Fill in the sections to provide clear information about your changes.

## Using Wiki Templates

The `wiki-templates` directory contains templates for common wiki pages. To use these templates:

1. Navigate to the wiki section of the GitHub repository
2. Create a new page or edit an existing page
3. Copy the content from the appropriate template
4. Customize the content for your specific needs

## Customizing Templates

Feel free to customize these templates to better suit the project's needs:

1. Edit the template files directly
2. Commit and push your changes
3. The updated templates will be immediately available

## GitHub CLI Commands for Templates

You can use GitHub CLI to work with these templates:

```bash
# Create a new issue using a template
gh issue create --template "bug_report.md"

# Create a pull request with the default template
gh pr create

# List available issue templates
gh issue create --list-templates
```

## Additional Resources

- [GitHub Docs: Issue Templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)
- [GitHub Docs: Pull Request Templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository)
- [GitHub CLI Documentation](https://cli.github.com/manual/) 