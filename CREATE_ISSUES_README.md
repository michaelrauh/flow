# Creating Issues from PR Findings

This document explains how to create GitHub issues based on the scalability and extensibility findings from PR #1.

## Overview

PR #1 identified 10 issues related to scalability and extensibility in the codebase. These findings are documented in `SCALABILITY_EXTENSIBILITY_ISSUES.md` in the PR branch `copilot/check-scalability-issues`.

This directory contains a script (`create_issues.py`) that automatically parses the findings document and creates individual GitHub issues for each identified problem.

## Prerequisites

- Python 3.6+
- GitHub CLI (`gh`) installed and authenticated
- Access to the `michaelrauh/flow` repository

## Usage

### 1. Dry Run (Recommended First)

Before creating actual issues, do a dry run to preview what will be created:

```bash
python3 create_issues.py --markdown SCALABILITY_EXTENSIBILITY_ISSUES.md --dry-run
```

If the markdown file is not in the current directory, the script will attempt to fetch it from the PR branch automatically.

### 2. Create Issues

Once you've reviewed the dry run output, create the actual issues:

```bash
python3 create_issues.py --markdown SCALABILITY_EXTENSIBILITY_ISSUES.md
```

Or if you want to fetch the file automatically:

```bash
python3 create_issues.py --dry-run  # Preview
python3 create_issues.py            # Create issues
```

### 3. Custom Repository

If you need to create issues in a different repository:

```bash
python3 create_issues.py --repo owner/repo-name
```

## What Gets Created

The script creates 10 GitHub issues with the following properties:

### Issue Labels

Each issue is automatically labeled based on its type and severity:

**Priority Labels:**
- `priority: high` - High severity issues
- `priority: medium` - Medium severity issues  
- `priority: low` - Low severity issues

**Type Labels:**
- `type: extensibility` - Issues affecting code extensibility
- `type: scalability` - Issues affecting system scalability
- `type: maintainability` - Issues affecting code maintainability
- `type: testability` - Issues affecting testability
- `type: performance` - Performance-related issues
- `type: usability` - Usability-related issues

### Issues Created

1. **MovementResolver is a God Object** (Priority: High)
   - Labels: `priority: high`, `type: extensibility`, `type: maintainability`

2. **No Configuration System for Physics Constants** (Priority: Medium)
   - Labels: `priority: medium`, `type: extensibility`, `type: usability`

3. **Direction Mappings Duplicated Across Files** (Priority: Medium)
   - Labels: `priority: medium`, `type: extensibility`, `type: maintainability`

4. **Global Mutable State in Graphics Module** (Priority: Medium)
   - Labels: `priority: medium`, `type: scalability`, `type: testability`

5. **prev_owner Dict Rebuilt Every Tick** (Priority: Medium)
   - Labels: `priority: medium`, `type: scalability`, `type: performance`

6. **No Spatial Indexing for Collision Detection** (Priority: Medium)
   - Labels: `priority: medium`, `type: scalability`

7. **Hardcoded Entity Type System** (Priority: High)
   - Labels: `priority: high`, `type: extensibility`

8. **ASCII-Only Level Format** (Priority: Medium)
   - Labels: `priority: medium`, `type: extensibility`, `type: usability`

9. **Global Simulation Engine Instance** (Priority: Low)
   - Labels: `priority: low`, `type: extensibility`, `type: testability`

10. **Emitter ID Assignment Assumes Sequential IDs** (Priority: Low)
    - Labels: `priority: low`, `type: extensibility`

## Troubleshooting

### Authentication Error

If you get an authentication error, make sure you're logged in to GitHub CLI:

```bash
gh auth login
```

### Missing Markdown File

If the markdown file is not found, the script will attempt to fetch it from the PR branch. Make sure you have access to the repository and the branch exists:

```bash
git fetch origin copilot/check-scalability-issues
```

### Permission Denied

Make sure the script is executable:

```bash
chmod +x create_issues.py
```

## Notes

- Each issue body contains the full problem description, suggested solutions, and relevant code references from the original document
- Issues are created with appropriate labels for easy filtering and organization
- The script checks if labels exist and will create them if they don't (requires appropriate permissions)
