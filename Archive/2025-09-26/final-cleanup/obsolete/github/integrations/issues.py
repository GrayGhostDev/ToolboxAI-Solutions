#!/usr/bin/env python3
"""
Issue tracking automation for ToolboxAI Roblox Environment

This script provides automated issue management:
- Auto-labeling based on content analysis
- Assignment based on code ownership
- Priority detection from keywords
- Stale issue management
- Bug reproduction template generation
- Related issue linking

Usage:
    python issues.py [command] [options]

Commands:
    auto-label <issue_number>    - Automatically label an issue
    assign <issue_number>        - Assign issue based on code ownership
    detect-priority <issue_number> - Detect and set issue priority
    cleanup-stale               - Clean up stale issues
    generate-template <type>    - Generate issue template
    link-related <issue_number> - Find and link related issues

Environment Variables:
    GITHUB_TOKEN - GitHub personal access token
    ISSUE_AUTO_ASSIGN - Set to 'true' to enable auto-assignment
    STALE_ISSUE_DAYS - Days before marking issues as stale (default: 30)
"""

import argparse
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from github import EducationalPlatformHelper, GitHubHelper, load_config, setup_logging

logger = setup_logging()

class IssueAutomation:
    """GitHub issue automation for educational platform"""
    
    def __init__(self):
        self.github_helper = GitHubHelper()
        self.edu_helper = EducationalPlatformHelper()
        self.config = load_config()
        self.repo_root = self.github_helper.repo_root
        
        # Load code ownership mapping
        self.code_owners = self._load_code_owners()
        
        # Educational platform specific labels
        self.educational_labels = {
            'curriculum': {'color': '0e8a16', 'description': 'Related to curriculum development'},
            'assessment': {'color': 'f9d0c4', 'description': 'Quiz and assessment features'},
            'learning': {'color': 'c2e0c6', 'description': 'Learning experience features'},
            'student': {'color': 'bfdadc', 'description': 'Student-facing functionality'},
            'teacher': {'color': 'd4c5f9', 'description': 'Teacher tools and interfaces'},
            'grading': {'color': 'fef2c0', 'description': 'Grading and evaluation systems'},
            'lms-integration': {'color': 'e99695', 'description': 'LMS platform integration'},
            'gamification': {'color': 'f9c2ff', 'description': 'Gamification features'},
            'progress-tracking': {'color': 'c5def5', 'description': 'Student progress tracking'},
            'analytics': {'color': 'fbca04', 'description': 'Educational analytics'},
            'roblox': {'color': '1d76db', 'description': 'Roblox platform specific'},
            'agents': {'color': '0052cc', 'description': 'AI agent system'},
            'api': {'color': 'f29513', 'description': 'API and backend'},
            'security': {'color': 'd73a4a', 'description': 'Security related'},
            'performance': {'color': 'ff6b6b', 'description': 'Performance optimization'},
            'accessibility': {'color': '7057ff', 'description': 'Accessibility improvements'},
            'bug': {'color': 'd73a4a', 'description': 'Something is not working'},
            'enhancement': {'color': '0075ca', 'description': 'New feature or request'},
            'documentation': {'color': '0075ca', 'description': 'Improvements or additions to documentation'},
            'good-first-issue': {'color': '7057ff', 'description': 'Good for newcomers'},
            'help-wanted': {'color': '008672', 'description': 'Extra attention is needed'},
            'priority-high': {'color': 'd93f0b', 'description': 'High priority issue'},
            'priority-medium': {'color': 'fbca04', 'description': 'Medium priority issue'},
            'priority-low': {'color': '0e8a16', 'description': 'Low priority issue'},
        }
    
    def _load_code_owners(self) -> dict[str, list[str]]:
        """Load CODEOWNERS file for assignment mapping"""
        codeowners_file = self.repo_root / '.github' / 'CODEOWNERS'
        owners = {}
        
        if codeowners_file.exists():
            try:
                with open(codeowners_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split()
                            if len(parts) >= 2:
                                path_pattern = parts[0]
                                owners_list = parts[1:]
                                owners[path_pattern] = [owner.replace('@', '') for owner in owners_list]
            except Exception as e:
                logger.warning(f"Error loading CODEOWNERS: {e}")
        
        # Default ownership mapping
        if not owners:
            owners = {
                'agents/': ['ai-team'],
                'server/': ['backend-team'],
                'Roblox/': ['game-dev-team'],
                'API/Dashboard/': ['frontend-team'],
                'API/GhostBackend/': ['backend-team'],
                'mcp/': ['ai-team'],
                'github/': ['devops-team'],
                'tests/': ['qa-team'],
                'docs/': ['docs-team'],
                '*': ['maintainers']
            }
        
        return owners
    
    def auto_label_issue(self, issue_number: int) -> bool:
        """Automatically label an issue based on content analysis"""
        logger.info(f"Auto-labeling issue #{issue_number}")
        
        # Get issue details
        issue_data = self.github_helper.send_github_api_request(f'issues/{issue_number}')
        if not issue_data:
            logger.error(f"Could not fetch issue #{issue_number}")
            return False
        
        title = issue_data.get('title', '')
        body = issue_data.get('body', '')
        content = f"{title} {body}".lower()
        
        # Determine labels
        labels_to_add = set()
        
        # Educational platform labels
        educational_labels = self.edu_helper.get_educational_labels(content)
        labels_to_add.update(educational_labels)
        
        # Component labels
        if 'roblox' in content or 'lua' in content:
            labels_to_add.add('roblox')
        if 'agent' in content or 'ai' in content or 'langchain' in content:
            labels_to_add.add('agents')
        if 'api' in content or 'backend' in content or 'server' in content:
            labels_to_add.add('api')
        if 'dashboard' in content or 'frontend' in content or 'ui' in content:
            labels_to_add.add('frontend')
        
        # Issue type labels
        if any(keyword in content for keyword in ['bug', 'error', 'broken', 'crash', 'fail']):
            labels_to_add.add('bug')
        elif any(keyword in content for keyword in ['feature', 'enhancement', 'add', 'implement']):
            labels_to_add.add('enhancement')
        elif any(keyword in content for keyword in ['doc', 'readme', 'guide', 'tutorial']):
            labels_to_add.add('documentation')
        
        # Security labels
        if any(keyword in content for keyword in ['security', 'vulnerability', 'exploit', 'auth']):
            labels_to_add.add('security')
        
        # Performance labels
        if any(keyword in content for keyword in ['slow', 'performance', 'optimize', 'speed']):
            labels_to_add.add('performance')
        
        # Accessibility labels
        if any(keyword in content for keyword in ['accessibility', 'a11y', 'screen reader', 'keyboard']):
            labels_to_add.add('accessibility')
        
        # Difficulty labels
        if any(keyword in content for keyword in ['simple', 'easy', 'straightforward', 'beginner']):
            labels_to_add.add('good-first-issue')
        if any(keyword in content for keyword in ['help', 'need assistance', 'looking for', 'volunteers']):
            labels_to_add.add('help-wanted')
        
        # Priority detection
        priority = self._detect_priority(title, body)
        if priority:
            labels_to_add.add(f'priority-{priority}')
        
        # Ensure labels exist
        self._ensure_labels_exist(labels_to_add)
        
        # Apply labels
        if labels_to_add:
            current_labels = [label['name'] for label in issue_data.get('labels', [])]
            new_labels = list(set(current_labels + list(labels_to_add)))
            
            success = self.github_helper.send_github_api_request(
                f'issues/{issue_number}',
                method='PATCH',
                data={'labels': new_labels}
            )
            
            if success:
                logger.info(f"Added labels to issue #{issue_number}: {', '.join(labels_to_add)}")
                return True
            else:
                logger.error(f"Failed to add labels to issue #{issue_number}")
                return False
        
        logger.info(f"No new labels to add for issue #{issue_number}")
        return True
    
    def _detect_priority(self, title: str, body: str) -> Optional[str]:
        """Detect issue priority from content"""
        content = f"{title} {body}".lower()
        
        # High priority indicators
        high_priority_keywords = [
            'urgent', 'critical', 'blocking', 'production', 'security',
            'data loss', 'cannot login', 'site down', 'crash'
        ]
        
        # Medium priority indicators
        medium_priority_keywords = [
            'important', 'should', 'improvement', 'feature request',
            'performance', 'slow'
        ]
        
        # Low priority indicators
        low_priority_keywords = [
            'nice to have', 'when possible', 'minor', 'cosmetic',
            'documentation', 'typo'
        ]
        
        if any(keyword in content for keyword in high_priority_keywords):
            return 'high'
        elif any(keyword in content for keyword in medium_priority_keywords):
            return 'medium'
        elif any(keyword in content for keyword in low_priority_keywords):
            return 'low'
        
        return None
    
    def assign_issue(self, issue_number: int) -> bool:
        """Assign issue based on code ownership"""
        if not os.getenv('ISSUE_AUTO_ASSIGN', 'false').lower() == 'true':
            logger.info("Auto-assignment disabled")
            return True
        
        logger.info(f"Auto-assigning issue #{issue_number}")
        
        # Get issue details
        issue_data = self.github_helper.send_github_api_request(f'issues/{issue_number}')
        if not issue_data:
            logger.error(f"Could not fetch issue #{issue_number}")
            return False
        
        title = issue_data.get('title', '')
        body = issue_data.get('body', '')
        content = f"{title} {body}".lower()
        
        # Determine assignee based on content and code ownership
        assignees = self._determine_assignees(content)
        
        if assignees:
            success = self.github_helper.send_github_api_request(
                f'issues/{issue_number}',
                method='PATCH',
                data={'assignees': assignees}
            )
            
            if success:
                logger.info(f"Assigned issue #{issue_number} to: {', '.join(assignees)}")
                return True
            else:
                logger.error(f"Failed to assign issue #{issue_number}")
                return False
        
        logger.info(f"No suitable assignee found for issue #{issue_number}")
        return True
    
    def _determine_assignees(self, content: str) -> list[str]:
        """Determine assignees based on issue content"""
        assignees = []
        
        # Map content to code ownership
        for path_pattern, owners in self.code_owners.items():
            if path_pattern == '*':
                continue
            
            # Check if content relates to this path
            component_keywords = {
                'agents/': ['agent', 'ai', 'langchain', 'llm'],
                'server/': ['api', 'backend', 'server', 'fastapi'],
                'Roblox/': ['roblox', 'lua', 'game', 'studio'],
                'API/Dashboard/': ['dashboard', 'frontend', 'react', 'ui'],
                'API/GhostBackend/': ['ghost', 'backend', 'database'],
                'mcp/': ['mcp', 'model context', 'websocket'],
                'github/': ['ci', 'cd', 'deployment', 'github'],
                'tests/': ['test', 'testing', 'pytest'],
                'docs/': ['documentation', 'docs', 'readme']
            }
            
            keywords = component_keywords.get(path_pattern, [])
            if any(keyword in content for keyword in keywords):
                assignees.extend(owners)
        
        # Remove duplicates and limit to 2-3 assignees
        unique_assignees = list(set(assignees))
        return unique_assignees[:3]
    
    def cleanup_stale_issues(self) -> bool:
        """Clean up stale issues"""
        logger.info("Cleaning up stale issues")
        
        stale_days = int(os.getenv('STALE_ISSUE_DAYS', '30'))
        cutoff_date = datetime.now() - timedelta(days=stale_days)
        
        # Get open issues
        issues_data = self.github_helper.send_github_api_request('issues?state=open&per_page=100')
        if not issues_data:
            logger.error("Could not fetch issues")
            return False
        
        stale_issues = []
        
        for issue in issues_data:
            if issue.get('pull_request'):  # Skip pull requests
                continue
            
            updated_at = datetime.fromisoformat(issue['updated_at'].replace('Z', '+00:00'))
            if updated_at < cutoff_date:
                stale_issues.append(issue)
        
        logger.info(f"Found {len(stale_issues)} stale issues")
        
        # Process stale issues
        for issue in stale_issues:
            issue_number = issue['number']
            
            # Check if already marked as stale
            labels = [label['name'] for label in issue.get('labels', [])]
            if 'stale' in labels:
                # Close if stale for too long
                if updated_at < cutoff_date - timedelta(days=7):
                    self._close_stale_issue(issue_number)
            else:
                # Mark as stale
                self._mark_issue_stale(issue_number)
        
        return True
    
    def _mark_issue_stale(self, issue_number: int) -> bool:
        """Mark an issue as stale"""
        logger.info(f"Marking issue #{issue_number} as stale")
        
        # Add stale label
        self._ensure_labels_exist(['stale'])
        
        success = self.github_helper.send_github_api_request(
            f'issues/{issue_number}',
            method='PATCH',
            data={'labels': ['stale']}
        )
        
        if success:
            # Add stale comment
            comment = """
This issue has been automatically marked as stale because it has not had recent activity. 
It will be closed in 7 days if no further activity occurs.

If this issue is still relevant, please:
- Add a comment to keep it open
- Remove the 'stale' label
- Provide additional context or updates

Thank you for your contributions to the ToolboxAI Educational Platform! 🎓
            """.strip()
            
            self.github_helper.send_github_api_request(
                f'issues/{issue_number}/comments',
                method='POST',
                data={'body': comment}
            )
            
            return True
        
        return False
    
    def _close_stale_issue(self, issue_number: int) -> bool:
        """Close a stale issue"""
        logger.info(f"Closing stale issue #{issue_number}")
        
        # Close the issue
        success = self.github_helper.send_github_api_request(
            f'issues/{issue_number}',
            method='PATCH',
            data={'state': 'closed'}
        )
        
        if success:
            # Add closure comment
            comment = """
This issue has been automatically closed due to inactivity. 
If this issue is still relevant, please reopen it and provide updated information.

Thank you for your contributions! 🚀
            """.strip()
            
            self.github_helper.send_github_api_request(
                f'issues/{issue_number}/comments',
                method='POST',
                data={'body': comment}
            )
            
            return True
        
        return False
    
    def generate_issue_template(self, template_type: str) -> str:
        """Generate issue template based on type"""
        logger.info(f"Generating {template_type} issue template")
        
        templates = {
            'bug': self._generate_bug_template(),
            'feature': self._generate_feature_template(),
            'educational': self._generate_educational_template(),
            'roblox': self._generate_roblox_template(),
            'agent': self._generate_agent_template()
        }
        
        return templates.get(template_type, self._generate_generic_template())
    
    def _generate_bug_template(self) -> str:
        """Generate bug report template"""
        return """
---
name: Bug Report
about: Create a report to help us improve the ToolboxAI Educational Platform
title: '[BUG] '
labels: 'bug'
assignees: ''

---

## 🐛 Bug Description
A clear and concise description of what the bug is.

## 🔄 Steps to Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## ✅ Expected Behavior
A clear and concise description of what you expected to happen.

## 📸 Screenshots
If applicable, add screenshots to help explain your problem.

## 🌍 Environment
**Platform Component:**
- [ ] Roblox Game
- [ ] Web Dashboard
- [ ] API Backend
- [ ] AI Agents
- [ ] LMS Integration

**Educational Context:**
- Subject: 
- Grade Level: 
- Number of Students: 

**Technical Details:**
- OS: [e.g. Windows, macOS, Linux]
- Browser: [e.g. Chrome, Safari] (if applicable)
- Roblox Client Version: (if applicable)
- Node.js Version: (if applicable)
- Python Version: (if applicable)

## 📋 Additional Context
Add any other context about the problem here.

## 🎯 Impact on Learning
How does this bug affect the educational experience?

## 🔧 Potential Solution
If you have ideas for fixing this bug, please share them here.
        """.strip()
    
    def _generate_feature_template(self) -> str:
        """Generate feature request template"""
        return """
---
name: Feature Request
about: Suggest an educational feature for the ToolboxAI Platform
title: '[FEATURE] '
labels: 'enhancement'
assignees: ''

---

## 📚 Educational Use Case
**Subject Area:** (e.g., Mathematics, Science, History)
**Grade Level:** (e.g., K-5, 6-8, 9-12, Higher Ed)
**Learning Objective:** What educational goal does this feature support?

## 🚀 Feature Description
A clear and concise description of the educational feature you'd like to see implemented.

## 🎯 Problem Statement
What educational challenge or limitation does this feature address?

## 💡 Proposed Solution
Describe the solution you'd like to see, including:
- How it would work in the classroom
- Student interaction patterns
- Teacher management capabilities

## 📊 Success Metrics
How would we measure the success of this feature?
- [ ] Student engagement metrics
- [ ] Learning outcome improvements
- [ ] Teacher adoption rate
- [ ] Time-to-understanding reduction

## 🎮 Platform Integration
Which components would this feature involve?
- [ ] Roblox Game Environment
- [ ] Web Dashboard
- [ ] LMS Integration (Canvas, Schoology, etc.)
- [ ] AI Content Generation
- [ ] Assessment System

## 🔗 Related Features
Are there existing features this would complement or depend on?

## 📋 Additional Context
- Examples from other educational platforms
- Research or pedagogical backing
- Mockups or wireframes (if available)

## 🎨 User Experience Considerations
- Accessibility requirements
- Age-appropriate design
- Multilingual support needs
        """.strip()
    
    def _generate_educational_template(self) -> str:
        """Generate educational-specific template"""
        return """
---
name: Educational Content Issue
about: Report issues with educational content or pedagogy
title: '[EDU] '
labels: 'curriculum, educational'
assignees: ''

---

## 📚 Educational Context
**Subject:** 
**Grade Level:** 
**Standards Alignment:** (e.g., Common Core, NGSS)
**Learning Objectives:** 

## 📝 Content Issue Description
Describe the educational content or pedagogical issue:

## 🎯 Learning Impact
How does this issue affect student learning outcomes?

## 👨‍🏫 Teacher Perspective
What challenges does this create for educators?

## 🔍 Suggested Improvements
What changes would improve the educational value?

## 📊 Assessment Considerations
How should learning be assessed for this content?

## 🌐 Accessibility & Inclusion
Any considerations for diverse learners?

## 📋 Additional Resources
Links to relevant educational research or examples:
        """.strip()
    
    def _generate_roblox_template(self) -> str:
        """Generate Roblox-specific template"""
        return """
---
name: Roblox Platform Issue
about: Issues specific to Roblox game development
title: '[ROBLOX] '
labels: 'roblox'
assignees: ''

---

## 🎮 Roblox Environment
**Place ID:** 
**Game Type:** (e.g., Classroom, Lab, Field Trip)
**Max Players:** 

## 🐛 Issue Description
Describe the Roblox-specific issue:

## 🔧 Lua Code Context
If relevant, provide code snippets or script names:

```lua
-- Paste relevant Lua code here
```

## 📱 Client Information
**Platform:** (PC, Mobile, Console)
**Graphics Quality:** 
**Internet Connection:** 

## 🎯 Educational Context
How does this affect the learning experience in Roblox?

## 🔄 Reproduction Steps
1. Join the Roblox place
2. ...

## 📊 Performance Impact
Any performance issues (lag, memory usage, etc.)?

## 🎨 Visual/Audio Issues
Screenshots or videos of the problem:
        """.strip()
    
    def _generate_agent_template(self) -> str:
        """Generate AI agent template"""
        return """
---
name: AI Agent Issue
about: Issues with AI agents or content generation
title: '[AGENT] '
labels: 'agents, ai'
assignees: ''

---

## 🤖 Agent System
**Agent Type:** (Content, Quiz, Terrain, Script, Review)
**LLM Model:** (GPT-4, Claude, etc.)
**Agent Version:** 

## 📝 Issue Description
Describe the AI agent issue:

## 📋 Input Context
What inputs were provided to the agent?

**Subject:** 
**Grade Level:** 
**Learning Objectives:** 
**Additional Context:** 

## 🎯 Expected Output
What should the agent have generated?

## 📊 Actual Output
What did the agent actually generate? (sanitize any sensitive data)

## 🔍 Quality Issues
- [ ] Factual accuracy
- [ ] Age-appropriate content
- [ ] Educational alignment
- [ ] Technical implementation
- [ ] Safety/moderation

## 📈 Model Performance
**Response Time:** 
**Token Usage:** 
**Cost Estimate:** 

## 🔧 Technical Context
**Agent Configuration:** 
**Context Window:** 
**Temperature Setting:** 

## 📋 Reproduction Steps
How can this issue be reproduced?
        """.strip()
    
    def _generate_generic_template(self) -> str:
        """Generate generic issue template"""
        return """
---
name: General Issue
about: General issues not covered by other templates
title: ''
labels: ''
assignees: ''

---

## 📝 Description
A clear and concise description of the issue.

## 🎯 Expected Behavior
What should happen?

## 📊 Current Behavior
What actually happens?

## 📋 Steps to Reproduce
1. 
2. 
3. 

## 🌍 Environment
Relevant environment details:

## 📚 Educational Impact
How does this affect teaching or learning?

## 📋 Additional Context
Any other context or screenshots:
        """.strip()
    
    def link_related_issues(self, issue_number: int) -> bool:
        """Find and link related issues"""
        logger.info(f"Finding related issues for #{issue_number}")
        
        # Get issue details
        issue_data = self.github_helper.send_github_api_request(f'issues/{issue_number}')
        if not issue_data:
            logger.error(f"Could not fetch issue #{issue_number}")
            return False
        
        title = issue_data.get('title', '')
        body = issue_data.get('body', '')
        labels = [label['name'] for label in issue_data.get('labels', [])]
        
        # Find related issues
        related_issues = self._find_related_issues(title, body, labels, issue_number)
        
        if related_issues:
            # Add comment with related issues
            related_links = [f"- #{num}: {title}" for num, title in related_issues]
            comment = f"""
## 🔗 Related Issues

I found these potentially related issues:

{chr(10).join(related_links)}

---
*This comment was automatically generated by the ToolboxAI issue automation system.*
            """.strip()
            
            success = self.github_helper.send_github_api_request(
                f'issues/{issue_number}/comments',
                method='POST',
                data={'body': comment}
            )
            
            if success:
                logger.info(f"Added related issues comment to #{issue_number}")
                return True
        
        logger.info(f"No related issues found for #{issue_number}")
        return True
    
    def _find_related_issues(self, title: str, body: str, labels: list[str], exclude_issue: int) -> list[tuple[int, str]]:
        """Find issues related to the given issue"""
        # Get all open issues
        issues_data = self.github_helper.send_github_api_request('issues?state=open&per_page=100')
        if not issues_data:
            return []
        
        content = f"{title} {body}".lower()
        content_words = set(re.findall(r'\b\w+\b', content))
        
        related_issues = []
        
        for issue in issues_data:
            if issue.get('number') == exclude_issue or issue.get('pull_request'):
                continue
            
            other_title = issue.get('title', '')
            other_body = issue.get('body', '') or ''
            other_labels = [label['name'] for label in issue.get('labels', [])]
            
            other_content = f"{other_title} {other_body}".lower()
            other_words = set(re.findall(r'\b\w+\b', other_content))
            
            # Calculate similarity
            similarity_score = 0
            
            # Label overlap (weighted heavily)
            common_labels = set(labels) & set(other_labels)
            if common_labels:
                similarity_score += len(common_labels) * 3
            
            # Word overlap
            common_words = content_words & other_words
            if common_words:
                similarity_score += len(common_words)
            
            # Title similarity
            title_words = set(re.findall(r'\b\w+\b', title.lower()))
            other_title_words = set(re.findall(r'\b\w+\b', other_title.lower()))
            title_overlap = title_words & other_title_words
            if title_overlap:
                similarity_score += len(title_overlap) * 2
            
            # If similarity is high enough, consider it related
            if similarity_score >= 5:
                related_issues.append((issue['number'], other_title))
        
        # Sort by relevance and return top 5
        return sorted(related_issues, key=lambda x: x[1])[:5]
    
    def _ensure_labels_exist(self, labels: set[str]):
        """Ensure labels exist in the repository"""
        for label_name in labels:
            if label_name in self.educational_labels:
                label_data = self.educational_labels[label_name]
                self.github_helper.send_github_api_request(
                    'labels',
                    method='POST',
                    data={
                        'name': label_name,
                        'color': label_data['color'],
                        'description': label_data['description']
                    }
                )


def main():
    """Main entry point for issue automation"""
    parser = argparse.ArgumentParser(description='Issue automation for ToolboxAI Roblox Environment')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Auto-label command
    label_parser = subparsers.add_parser('auto-label', help='Automatically label an issue')
    label_parser.add_argument('issue_number', type=int, help='Issue number to label')
    
    # Assign command
    assign_parser = subparsers.add_parser('assign', help='Assign issue based on code ownership')
    assign_parser.add_argument('issue_number', type=int, help='Issue number to assign')
    
    # Detect priority command
    priority_parser = subparsers.add_parser('detect-priority', help='Detect and set issue priority')
    priority_parser.add_argument('issue_number', type=int, help='Issue number to analyze')
    
    # Cleanup stale command
    subparsers.add_parser('cleanup-stale', help='Clean up stale issues')
    
    # Generate template command
    template_parser = subparsers.add_parser('generate-template', help='Generate issue template')
    template_parser.add_argument('type', choices=['bug', 'feature', 'educational', 'roblox', 'agent'], help='Template type')
    
    # Link related command
    link_parser = subparsers.add_parser('link-related', help='Find and link related issues')
    link_parser.add_argument('issue_number', type=int, help='Issue number to find related issues for')
    
    # Common arguments
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel('DEBUG')
    
    automation = IssueAutomation()
    
    try:
        if args.command == 'auto-label':
            success = automation.auto_label_issue(args.issue_number)
        elif args.command == 'assign':
            success = automation.assign_issue(args.issue_number)
        elif args.command == 'detect-priority':
            success = automation.auto_label_issue(args.issue_number)  # Priority detection is part of auto-labeling
        elif args.command == 'cleanup-stale':
            success = automation.cleanup_stale_issues()
        elif args.command == 'generate-template':
            template = automation.generate_issue_template(args.type)
            print(template)
            success = True
        elif args.command == 'link-related':
            success = automation.link_related_issues(args.issue_number)
        else:
            parser.print_help()
            success = False
        
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Issue automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Issue automation failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()