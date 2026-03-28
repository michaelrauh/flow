#!/usr/bin/env python3
"""
Script to export issues as individual markdown files for manual creation
or bulk import.
"""

import os
import re
import json


def parse_issues_from_markdown(filepath):
    """Parse the markdown file and extract individual issues."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Split by issue sections
    issue_pattern = re.compile(r'^## (Issue \d+: [^\n]+)', re.MULTILINE)
    sections = issue_pattern.split(content)
    
    issues = []
    # Skip the intro (sections[0]) and process pairs of (title, content)
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            title = sections[i].replace('Issue ', '').strip()
            # Remove the number prefix (e.g., "1: ")
            title_match = re.match(r'^(\d+):\s*(.+)$', title)
            issue_num = ''
            if title_match:
                issue_num = title_match.group(1)
                title = title_match.group(2)
            
            content = sections[i + 1].strip()
            # Get the next separator to know where this issue ends
            next_section_match = re.search(r'^---\s*$', content, re.MULTILINE)
            if next_section_match:
                content = content[:next_section_match.start()].strip()
            
            # Parse metadata from the content
            type_match = re.search(r'\*\*Type:\*\*\s*([^\n]+)', content)
            severity_match = re.search(r'\*\*Severity:\*\*\s*([^\n]+)', content)
            file_match = re.search(r'\*\*Files?:\*\*\s*([^\n]+)', content)
            
            issue_type = type_match.group(1).strip() if type_match else ''
            severity = severity_match.group(1).strip() if severity_match else ''
            files = file_match.group(1).strip() if file_match else ''
            
            # Create labels based on type and severity
            labels = []
            if 'High' in severity:
                labels.append('priority: high')
            elif 'Medium' in severity:
                labels.append('priority: medium')
            else:
                labels.append('priority: low')
            
            if 'Extensibility' in issue_type or 'Ext' in issue_type:
                labels.append('type: extensibility')
            if 'Scalability' in issue_type or 'Scale' in issue_type:
                labels.append('type: scalability')
            if 'Maintainability' in issue_type or 'Maint' in issue_type:
                labels.append('type: maintainability')
            if 'Testability' in issue_type or 'Test' in issue_type:
                labels.append('type: testability')
            if 'Performance' in issue_type or 'Perf' in issue_type:
                labels.append('type: performance')
            if 'Usability' in issue_type:
                labels.append('type: usability')
            
            issues.append({
                'number': issue_num,
                'title': title,
                'body': content,
                'labels': labels,
                'type': issue_type,
                'severity': severity,
                'files': files
            })
    
    return issues


def export_issues_to_files(issues, output_dir='issues_to_create'):
    """Export issues as individual markdown files."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a manifest file
    manifest = []
    
    for issue in issues:
        # Create filename
        filename = f"issue-{issue['number']}-{issue['title'].lower().replace(' ', '-').replace('/', '-')[:50]}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Create the issue content
        issue_content = f"""---
title: {issue['title']}
labels: {', '.join(issue['labels'])}
---

{issue['body']}

---

*This issue was automatically generated from the scalability and extensibility analysis in PR #1.*
"""
        
        with open(filepath, 'w') as f:
            f.write(issue_content)
        
        manifest.append({
            'file': filename,
            'title': issue['title'],
            'labels': issue['labels'],
            'priority': 'high' if 'priority: high' in issue['labels'] else 
                       'medium' if 'priority: medium' in issue['labels'] else 'low'
        })
        
        print(f"Created: {filepath}")
    
    # Write manifest
    manifest_path = os.path.join(output_dir, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nCreated manifest: {manifest_path}")
    
    # Create a README for the issues directory
    readme_path = os.path.join(output_dir, 'README.md')
    with open(readme_path, 'w') as f:
        f.write("""# Issues to Create

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
gh issue create --repo michaelrauh/flow \\
  --title "Issue Title Here" \\
  --body-file issue-X-filename.md \\
  --label "priority: high,type: extensibility"
```

## Issue List

""")
        
        # Add issue list sorted by priority
        for priority in ['high', 'medium', 'low']:
            priority_issues = [m for m in manifest if m['priority'] == priority]
            if priority_issues:
                f.write(f"\n### Priority: {priority.capitalize()}\n\n")
                for m in priority_issues:
                    f.write(f"- **{m['title']}**\n")
                    f.write(f"  - File: `{m['file']}`\n")
                    f.write(f"  - Labels: {', '.join(m['labels'])}\n\n")
    
    print(f"Created README: {readme_path}")


def main():
    """Main function."""
    import sys
    
    markdown_file = sys.argv[1] if len(sys.argv) > 1 else '/tmp/scalability_issues.md'
    
    if not os.path.exists(markdown_file):
        print(f"Error: Markdown file not found: {markdown_file}")
        return 1
    
    issues = parse_issues_from_markdown(markdown_file)
    print(f"Found {len(issues)} issues\n")
    
    export_issues_to_files(issues)
    
    print(f"\n✓ Successfully exported {len(issues)} issues to the 'issues_to_create' directory")
    print("See issues_to_create/README.md for instructions on how to create them.")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
