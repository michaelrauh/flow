#!/usr/bin/env python3
"""
Script to create GitHub issues from SCALABILITY_EXTENSIBILITY_ISSUES.md

This script parses the markdown document from PR #1 and creates individual
GitHub issues for each identified problem.
"""

import re
import subprocess
import sys


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
            title_match = re.match(r'^\d+:\s*(.+)$', title)
            if title_match:
                title = title_match.group(1)
            
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
                'title': title,
                'body': content,
                'labels': labels,
                'type': issue_type,
                'severity': severity,
                'files': files
            })
    
    return issues


def create_github_issue(title, body, labels, repo='michaelrauh/flow'):
    """Create a GitHub issue using the gh CLI."""
    cmd = ['gh', 'issue', 'create', '--repo', repo, '--title', title, '--body', body]
    
    if labels:
        cmd.extend(['--label', ','.join(labels)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error creating issue: {e.stderr}", file=sys.stderr)
        return None


def main():
    """Main function to parse issues and create them on GitHub."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create GitHub issues from markdown document')
    parser.add_argument('--markdown', default='SCALABILITY_EXTENSIBILITY_ISSUES.md',
                        help='Path to the markdown file')
    parser.add_argument('--repo', default='michaelrauh/flow',
                        help='GitHub repository (owner/name)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print issues without creating them')
    
    args = parser.parse_args()
    
    # Check if markdown file exists, if not try to fetch it
    import os
    if not os.path.exists(args.markdown):
        print(f"Markdown file not found: {args.markdown}")
        print("Attempting to fetch from PR #1 branch...")
        try:
            subprocess.run([
                'git', 'show', 
                'origin/copilot/check-scalability-issues:SCALABILITY_EXTENSIBILITY_ISSUES.md'
            ], stdout=open(args.markdown, 'w'), check=True)
            print(f"Successfully fetched {args.markdown}")
        except subprocess.CalledProcessError:
            print("Failed to fetch file. Please ensure the file exists or the branch is available.")
            return 1
    
    issues = parse_issues_from_markdown(args.markdown)
    
    print(f"Found {len(issues)} issues to create\n")
    
    for i, issue in enumerate(issues, 1):
        print(f"Issue {i}: {issue['title']}")
        print(f"  Type: {issue['type']}")
        print(f"  Severity: {issue['severity']}")
        print(f"  Files: {issue['files']}")
        print(f"  Labels: {', '.join(issue['labels'])}")
        
        if args.dry_run:
            print(f"  [DRY RUN] Would create issue")
            print(f"  Body preview: {issue['body'][:100]}...")
        else:
            url = create_github_issue(issue['title'], issue['body'], issue['labels'], args.repo)
            if url:
                print(f"  ✓ Created: {url}")
            else:
                print(f"  ✗ Failed to create issue")
        
        print()
    
    if args.dry_run:
        print("Dry run complete. Use without --dry-run to create actual issues.")
    else:
        print(f"Successfully created {len(issues)} issues!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
