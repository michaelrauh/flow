# Quick Start Guide

## TL;DR - Create All 10 Issues in One Command

```bash
python3 create_issues.py
```

That's it! The script will:
1. Fetch the findings document from PR #1
2. Parse all 10 issues
3. Create them on GitHub with proper labels
4. Print the URLs of created issues

## Prerequisites

Ensure GitHub CLI is authenticated:
```bash
gh auth status
```

If not authenticated, run:
```bash
gh auth login
```

## Alternative Methods

### Preview Before Creating (Recommended)
```bash
python3 create_issues.py --dry-run
```

### Manual Creation
1. Navigate to `issues_to_create/` directory
2. Open each `issue-*.md` file
3. Go to https://github.com/michaelrauh/flow/issues/new
4. Copy title and body from the file
5. Add the labels listed in the file
6. Submit

### Bulk Creation with Shell Loop
```bash
cd issues_to_create/
for file in issue-*.md; do
    title=$(grep '^title:' "$file" | sed 's/^title: //')
    labels=$(grep '^labels:' "$file" | sed 's/^labels: //')
    body=$(sed '1,/^---$/d' "$file" | head -n -3)
    
    echo "Creating: $title"
    gh issue create --repo michaelrauh/flow \
        --title "$title" \
        --body "$body" \
        --label "$labels"
done
```

## What Gets Created

10 GitHub issues covering:
- **2 High Priority**: God object, hardcoded entity types
- **6 Medium Priority**: Config system, caches, performance, format
- **2 Low Priority**: Global state, ID management

Each issue includes:
- Clear title
- Full problem description
- Affected files
- Suggested solutions
- Appropriate labels (priority + type)

## Files in This PR

| File | Purpose |
|------|---------|
| `create_issues.py` | Automated creation script |
| `export_issues.py` | Export to individual files |
| `CREATE_ISSUES_README.md` | Detailed documentation |
| `IMPLEMENTATION_SUMMARY.md` | Complete project overview |
| `QUICK_START.md` | This file |
| `issues_to_create/` | Pre-generated issue files |

## Troubleshooting

**"gh: command not found"**
- Install GitHub CLI: https://cli.github.com/

**"Failed to log in to github.com"**
- Run: `gh auth login`
- Follow the prompts to authenticate

**"Permission denied"**
- Ensure scripts are executable: `chmod +x *.py`

**"Markdown file not found"**
- The script will fetch it automatically from PR #1

## Next Steps After Creating Issues

1. Verify all 10 issues were created successfully
2. Review and adjust priorities if needed
3. Assign issues to team members
4. Add to project boards or milestones
5. Link related issues together
6. Begin addressing high-priority issues first

## Support

For more details, see:
- `CREATE_ISSUES_README.md` - Comprehensive guide
- `IMPLEMENTATION_SUMMARY.md` - Full technical details
- `issues_to_create/README.md` - Manual creation guide
