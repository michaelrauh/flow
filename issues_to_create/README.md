# Issues to Create

This directory contains individual issue files ready to be created on GitHub.

## How to Create Issues

### Option 1: Using the create_issues.py script (Automated)

If you have GitHub CLI (`gh`) installed and authenticated:

```bash
cd ..
python3 create_issues.py
```

### Option 2: Manual Creation

1. Go to https://github.com/michaelrauh/flow/issues/new
2. Copy the title from each issue file (after `title:`)
3. Copy the body content (everything after the `---` header)
4. Add the labels listed in the file
5. Click "Submit new issue"

### Option 3: Using GitHub CLI Manually

For each issue file:

```bash
gh issue create --repo michaelrauh/flow \
  --title "Issue Title Here" \
  --body-file issue-X-filename.md \
  --label "priority: high,type: extensibility"
```

## Issue List


### Priority: High

- **MovementResolver is a God Object**
  - File: `issue-1-movementresolver-is-a-god-object.md`
  - Labels: priority: high, type: extensibility, type: maintainability

- **Hardcoded Entity Type System**
  - File: `issue-7-hardcoded-entity-type-system.md`
  - Labels: priority: high, type: extensibility


### Priority: Medium

- **No Configuration System for Physics Constants**
  - File: `issue-2-no-configuration-system-for-physics-constants.md`
  - Labels: priority: medium, type: extensibility, type: usability

- **Direction Mappings Duplicated Across Files**
  - File: `issue-3-direction-mappings-duplicated-across-files.md`
  - Labels: priority: medium, type: extensibility, type: maintainability

- **Global Mutable State in Graphics Module**
  - File: `issue-4-global-mutable-state-in-graphics-module.md`
  - Labels: priority: medium, type: scalability, type: testability

- **prev_owner Dict Rebuilt Every Tick**
  - File: `issue-5-prev_owner-dict-rebuilt-every-tick.md`
  - Labels: priority: medium, type: scalability, type: performance

- **No Spatial Indexing for Collision Detection**
  - File: `issue-6-no-spatial-indexing-for-collision-detection.md`
  - Labels: priority: medium, type: scalability

- **ASCII-Only Level Format**
  - File: `issue-8-ascii-only-level-format.md`
  - Labels: priority: medium, type: extensibility, type: usability


### Priority: Low

- **Global Simulation Engine Instance**
  - File: `issue-9-global-simulation-engine-instance.md`
  - Labels: priority: low, type: extensibility, type: testability

- **Emitter ID Assignment Assumes Sequential IDs**
  - File: `issue-10-emitter-id-assignment-assumes-sequential-ids.md`
  - Labels: priority: low, type: extensibility

