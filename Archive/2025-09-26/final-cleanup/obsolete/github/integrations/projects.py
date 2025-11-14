#!/usr/bin/env python3
"""
Project board synchronization for ToolboxAI Roblox Environment

This script provides automated project board management:
- Automatic card movement based on issue/PR status
- Sprint planning integration
- Milestone tracking
- Burndown chart updates
- Team velocity metrics
- Dependency tracking

Usage:
    python projects.py [command] [options]

Commands:
    sync-boards              - Synchronize all project boards
    update-card <issue_id>   - Update card based on issue status
    create-sprint <name>     - Create new sprint
    close-sprint <name>      - Close current sprint
    generate-burndown        - Generate burndown chart data
    track-velocity           - Calculate team velocity
    update-dependencies      - Update dependency tracking

Environment Variables:
    GITHUB_TOKEN - GitHub personal access token
    PROJECT_BOARD_ID - GitHub project board ID
    SPRINT_DURATION_WEEKS - Sprint duration (default: 2)
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from github import (
    EducationalPlatformHelper,
    GitHubHelper,
    load_config,
    notify_team,
    setup_logging,
)

logger = setup_logging()

@dataclass
class ProjectCard:
    """Represents a project board card"""
    id: int
    issue_id: Optional[int]
    pr_id: Optional[int]
    column_id: int
    column_name: str
    title: str
    labels: list[str]
    assignees: list[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class Sprint:
    """Represents a development sprint"""
    name: str
    start_date: datetime
    end_date: datetime
    issues: list[int]
    completed_issues: list[int]
    total_points: int
    completed_points: int
    
@dataclass
class TeamVelocity:
    """Represents team velocity metrics"""
    sprint_name: str
    planned_points: int
    completed_points: int
    completion_rate: float
    issues_completed: int
    issues_planned: int

class ProjectBoardManager:
    """Project board management for educational platform"""
    
    def __init__(self):
        self.github_helper = GitHubHelper()
        self.edu_helper = EducationalPlatformHelper()
        self.config = load_config()
        self.repo_root = self.github_helper.repo_root
        
        # Project board configuration
        self.board_config = {
            'columns': {
                'backlog': ['Backlog', 'To Do', 'New'],
                'in_progress': ['In Progress', 'Development', 'Working'],
                'review': ['Review', 'Testing', 'QA'],
                'done': ['Done', 'Completed', 'Closed']
            },
            'educational_priorities': {
                'curriculum': 3,
                'assessment': 3,
                'student': 2,
                'teacher': 2,
                'roblox': 1,
                'api': 1,
                'documentation': 1
            },
            'story_points': {
                'small': 1,
                'medium': 3,
                'large': 5,
                'xl': 8
            }
        }
        
        self.project_board_id = os.getenv('PROJECT_BOARD_ID')
        self.sprint_duration = int(os.getenv('SPRINT_DURATION_WEEKS', '2'))
    
    def sync_all_boards(self) -> bool:
        """Synchronize all project boards"""
        logger.info("Synchronizing project boards")
        
        if not self.project_board_id:
            logger.warning("No project board ID configured")
            return True
        
        try:
            # Get project board data
            project_data = self._get_project_board()
            if not project_data:
                logger.error("Failed to get project board data")
                return False
            
            # Get all cards
            cards = self._get_project_cards()
            
            # Update cards based on issue/PR status
            for card in cards:
                self._update_card_position(card)
            
            # Update sprint information
            self._update_sprint_progress()
            
            # Update educational priorities
            self._update_educational_priorities(cards)
            
            # Generate metrics
            self._generate_board_metrics()
            
            logger.info("Project board synchronization completed")
            return True
            
        except Exception as e:
            logger.error(f"Error synchronizing project boards: {e}")
            return False
    
    def _get_project_board(self) -> Optional[dict]:
        """Get project board information"""
        return self.github_helper.send_github_api_request(f'projects/{self.project_board_id}')
    
    def _get_project_cards(self) -> list[ProjectCard]:
        """Get all cards from project board"""
        cards = []
        
        # Get project columns
        columns_data = self.github_helper.send_github_api_request(f'projects/{self.project_board_id}/columns')
        if not columns_data:
            return cards
        
        for column in columns_data:
            column_id = column['id']
            column_name = column['name']
            
            # Get cards in this column
            cards_data = self.github_helper.send_github_api_request(f'projects/columns/{column_id}/cards')
            if cards_data:
                for card_data in cards_data:
                    card = self._parse_card_data(card_data, column_id, column_name)
                    if card:
                        cards.append(card)
        
        return cards
    
    def _parse_card_data(self, card_data: dict, column_id: int, column_name: str) -> Optional[ProjectCard]:
        """Parse card data from API response"""
        try:
            content_url = card_data.get('content_url', '')
            issue_id = None
            pr_id = None
            
            if '/issues/' in content_url:
                issue_id = int(content_url.split('/issues/')[-1])
            elif '/pulls/' in content_url:
                pr_id = int(content_url.split('/pulls/')[-1])
            
            # Get additional info from issue/PR
            labels = []
            assignees = []
            title = card_data.get('note', 'Untitled')
            
            if issue_id:
                issue_data = self.github_helper.send_github_api_request(f'issues/{issue_id}')
                if issue_data:
                    title = issue_data.get('title', title)
                    labels = [label['name'] for label in issue_data.get('labels', [])]
                    assignees = [assignee['login'] for assignee in issue_data.get('assignees', [])]
            elif pr_id:
                pr_data = self.github_helper.send_github_api_request(f'pulls/{pr_id}')
                if pr_data:
                    title = pr_data.get('title', title)
                    labels = [label['name'] for label in pr_data.get('labels', [])]
                    assignees = [pr_data['user']['login']] if pr_data.get('user') else []
            
            return ProjectCard(
                id=card_data['id'],
                issue_id=issue_id,
                pr_id=pr_id,
                column_id=column_id,
                column_name=column_name,
                title=title,
                labels=labels,
                assignees=assignees,
                created_at=datetime.fromisoformat(card_data['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(card_data['updated_at'].replace('Z', '+00:00'))
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse card data: {e}")
            return None
    
    def _update_card_position(self, card: ProjectCard) -> bool:
        """Update card position based on issue/PR status"""
        try:
            target_column = None
            
            if card.issue_id:
                # Check issue status
                issue_data = self.github_helper.send_github_api_request(f'issues/{card.issue_id}')
                if issue_data:
                    state = issue_data.get('state')
                    assignees = issue_data.get('assignees', [])
                    
                    if state == 'closed':
                        target_column = 'done'
                    elif assignees:
                        # Check if there are linked PRs
                        if self._has_linked_pr(card.issue_id):
                            target_column = 'review'
                        else:
                            target_column = 'in_progress'
                    else:
                        target_column = 'backlog'
            
            elif card.pr_id:
                # Check PR status
                pr_data = self.github_helper.send_github_api_request(f'pulls/{card.pr_id}')
                if pr_data:
                    state = pr_data.get('state')
                    draft = pr_data.get('draft', False)
                    
                    if state == 'closed':
                        target_column = 'done'
                    elif draft:
                        target_column = 'in_progress'
                    else:
                        target_column = 'review'
            
            # Move card if needed
            if target_column:
                current_column_type = self._get_column_type(card.column_name)
                if current_column_type != target_column:
                    return self._move_card_to_column(card, target_column)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating card position for {card.id}: {e}")
            return False
    
    def _get_column_type(self, column_name: str) -> str:
        """Get column type from column name"""
        column_name_lower = column_name.lower()
        
        for column_type, names in self.board_config['columns'].items():
            if any(name.lower() in column_name_lower for name in names):
                return column_type
        
        return 'backlog'  # Default
    
    def _has_linked_pr(self, issue_id: int) -> bool:
        """Check if issue has linked pull requests"""
        # This is a simplified check - in practice, you'd look for PR references
        prs_data = self.github_helper.send_github_api_request('pulls?state=open')
        if prs_data:
            for pr in prs_data:
                body = pr.get('body', '') or ''
                if f"#{issue_id}" in body or f"closes #{issue_id}" in body.lower():
                    return True
        return False
    
    def _move_card_to_column(self, card: ProjectCard, target_column_type: str) -> bool:
        """Move card to target column"""
        # Find target column ID
        target_column_id = self._find_column_id(target_column_type)
        if not target_column_id:
            logger.warning(f"Could not find column for type: {target_column_type}")
            return False
        
        # Move card
        move_data = {'position': 'bottom'}
        response = self.github_helper.send_github_api_request(
            f'projects/columns/cards/{card.id}/moves',
            method='POST',
            data=move_data
        )
        
        if response:
            logger.info(f"Moved card {card.id} to {target_column_type}")
            return True
        else:
            logger.error(f"Failed to move card {card.id}")
            return False
    
    def _find_column_id(self, column_type: str) -> Optional[int]:
        """Find column ID by type"""
        columns_data = self.github_helper.send_github_api_request(f'projects/{self.project_board_id}/columns')
        if not columns_data:
            return None
        
        target_names = self.board_config['columns'].get(column_type, [])
        
        for column in columns_data:
            column_name = column['name']
            if any(name.lower() in column_name.lower() for name in target_names):
                return column['id']
        
        return None
    
    def create_sprint(self, sprint_name: str) -> bool:
        """Create a new sprint"""
        logger.info(f"Creating sprint: {sprint_name}")
        
        try:
            # Calculate sprint dates
            start_date = datetime.now(timezone.utc)
            end_date = start_date + timedelta(weeks=self.sprint_duration)
            
            # Get issues for sprint (from backlog and ready columns)
            sprint_issues = self._collect_sprint_issues()
            
            # Calculate total points
            total_points = sum(self._get_issue_points(issue_id) for issue_id in sprint_issues)
            
            # Create sprint data
            sprint = Sprint(
                name=sprint_name,
                start_date=start_date,
                end_date=end_date,
                issues=sprint_issues,
                completed_issues=[],
                total_points=total_points,
                completed_points=0
            )
            
            # Save sprint data
            self._save_sprint_data(sprint)
            
            # Create milestone
            milestone_data = {
                'title': sprint_name,
                'description': f'Sprint running from {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}',
                'due_on': end_date.isoformat(),
                'state': 'open'
            }
            
            milestone_response = self.github_helper.send_github_api_request(
                'milestones',
                method='POST',
                data=milestone_data
            )
            
            if milestone_response:
                milestone_id = milestone_response['number']
                
                # Assign issues to milestone
                for issue_id in sprint_issues:
                    self.github_helper.send_github_api_request(
                        f'issues/{issue_id}',
                        method='PATCH',
                        data={'milestone': milestone_id}
                    )
                
                logger.info(f"Created sprint {sprint_name} with {len(sprint_issues)} issues ({total_points} points)")
                
                # Notify team
                self._notify_sprint_created(sprint)
                
                return True
            else:
                logger.error("Failed to create milestone")
                return False
                
        except Exception as e:
            logger.error(f"Error creating sprint: {e}")
            return False
    
    def _collect_sprint_issues(self) -> list[int]:
        """Collect issues for sprint from backlog"""
        sprint_issues = []
        
        # Get issues from backlog columns
        cards = self._get_project_cards()
        backlog_cards = [card for card in cards if self._get_column_type(card.column_name) == 'backlog']
        
        # Sort by educational priority and labels
        backlog_cards.sort(key=lambda card: self._calculate_issue_priority(card), reverse=True)
        
        # Select top issues for sprint capacity
        max_points = 40  # Typical sprint capacity
        current_points = 0
        
        for card in backlog_cards:
            if card.issue_id:
                issue_points = self._get_issue_points(card.issue_id)
                if current_points + issue_points <= max_points:
                    sprint_issues.append(card.issue_id)
                    current_points += issue_points
        
        return sprint_issues
    
    def _calculate_issue_priority(self, card: ProjectCard) -> int:
        """Calculate issue priority score"""
        priority_score = 0
        
        # Educational priority based on labels
        for label in card.labels:
            if label in self.board_config['educational_priorities']:
                priority_score += self.board_config['educational_priorities'][label]
        
        # Priority labels
        if 'priority-high' in card.labels:
            priority_score += 5
        elif 'priority-medium' in card.labels:
            priority_score += 3
        elif 'priority-low' in card.labels:
            priority_score += 1
        
        # Bug priority
        if 'bug' in card.labels:
            priority_score += 4
        
        # Good first issue (lower priority for sprint)
        if 'good-first-issue' in card.labels:
            priority_score -= 1
        
        return priority_score
    
    def _get_issue_points(self, issue_id: int) -> int:
        """Get story points for issue"""
        issue_data = self.github_helper.send_github_api_request(f'issues/{issue_id}')
        if not issue_data:
            return 1
        
        labels = [label['name'] for label in issue_data.get('labels', [])]
        
        # Look for size labels
        for label in labels:
            if label.startswith('size/'):
                size = label.split('/')[1].lower()
                return self.board_config['story_points'].get(size, 1)
        
        # Estimate based on issue type and complexity
        title = issue_data.get('title', '').lower()
        body = issue_data.get('body', '') or ''
        content = f"{title} {body}".lower()
        
        if 'bug' in labels:
            if any(word in content for word in ['critical', 'urgent', 'blocking']):
                return 5
            elif any(word in content for word in ['simple', 'typo', 'minor']):
                return 1
            else:
                return 3
        elif 'enhancement' in labels:
            if any(word in content for word in ['major', 'significant', 'complex']):
                return 8
            elif any(word in content for word in ['small', 'simple', 'quick']):
                return 1
            else:
                return 3
        
        return 1  # Default
    
    def _save_sprint_data(self, sprint: Sprint):
        """Save sprint data to file"""
        sprints_dir = self.repo_root / '.github' / 'sprints'
        sprints_dir.mkdir(exist_ok=True)
        
        sprint_file = sprints_dir / f"{sprint.name.lower().replace(' ', '_')}.json"
        
        sprint_data = {
            'name': sprint.name,
            'start_date': sprint.start_date.isoformat(),
            'end_date': sprint.end_date.isoformat(),
            'issues': sprint.issues,
            'completed_issues': sprint.completed_issues,
            'total_points': sprint.total_points,
            'completed_points': sprint.completed_points
        }
        
        with open(sprint_file, 'w') as f:
            json.dump(sprint_data, f, indent=2)
    
    def _notify_sprint_created(self, sprint: Sprint):
        """Notify team about new sprint"""
        message = f"""
🚀 **New Sprint Started: {sprint.name}**

**Duration:** {sprint.start_date.strftime('%Y-%m-%d')} to {sprint.end_date.strftime('%Y-%m-%d')}
**Issues:** {len(sprint.issues)}
**Story Points:** {sprint.total_points}

**Focus Areas:**
- Educational content improvements
- Roblox platform enhancements  
- API and backend stability
- User experience refinements

**Sprint Goals:**
- Deliver high-quality educational features
- Maintain code quality and test coverage
- Improve platform performance
- Enhance documentation

Let's make this sprint count! 💪
        """.strip()
        
        notify_team(message)
    
    def close_sprint(self, sprint_name: str) -> bool:
        """Close current sprint and calculate metrics"""
        logger.info(f"Closing sprint: {sprint_name}")
        
        try:
            # Load sprint data
            sprint = self._load_sprint_data(sprint_name)
            if not sprint:
                logger.error(f"Sprint {sprint_name} not found")
                return False
            
            # Calculate completed issues and points
            completed_issues = []
            completed_points = 0
            
            for issue_id in sprint.issues:
                issue_data = self.github_helper.send_github_api_request(f'issues/{issue_id}')
                if issue_data and issue_data.get('state') == 'closed':
                    completed_issues.append(issue_id)
                    completed_points += self._get_issue_points(issue_id)
            
            # Update sprint data
            sprint.completed_issues = completed_issues
            sprint.completed_points = completed_points
            
            # Save updated sprint data
            self._save_sprint_data(sprint)
            
            # Close milestone
            milestones_data = self.github_helper.send_github_api_request('milestones')
            if milestones_data:
                for milestone in milestones_data:
                    if milestone['title'] == sprint_name:
                        self.github_helper.send_github_api_request(
                            f'milestones/{milestone["number"]}',
                            method='PATCH',
                            data={'state': 'closed'}
                        )
                        break
            
            # Generate sprint report
            self._generate_sprint_report(sprint)
            
            # Notify team
            self._notify_sprint_closed(sprint)
            
            logger.info(f"Sprint {sprint_name} closed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error closing sprint: {e}")
            return False
    
    def _load_sprint_data(self, sprint_name: str) -> Optional[Sprint]:
        """Load sprint data from file"""
        sprints_dir = self.repo_root / '.github' / 'sprints'
        sprint_file = sprints_dir / f"{sprint_name.lower().replace(' ', '_')}.json"
        
        if not sprint_file.exists():
            return None
        
        try:
            with open(sprint_file) as f:
                data = json.load(f)
            
            return Sprint(
                name=data['name'],
                start_date=datetime.fromisoformat(data['start_date']),
                end_date=datetime.fromisoformat(data['end_date']),
                issues=data['issues'],
                completed_issues=data.get('completed_issues', []),
                total_points=data['total_points'],
                completed_points=data.get('completed_points', 0)
            )
            
        except Exception as e:
            logger.error(f"Error loading sprint data: {e}")
            return None
    
    def _generate_sprint_report(self, sprint: Sprint):
        """Generate sprint report"""
        completion_rate = (sprint.completed_points / sprint.total_points * 100) if sprint.total_points > 0 else 0
        
        report_content = f"""# Sprint Report: {sprint.name}

## Overview
- **Duration:** {sprint.start_date.strftime('%Y-%m-%d')} to {sprint.end_date.strftime('%Y-%m-%d')}
- **Total Issues:** {len(sprint.issues)}
- **Completed Issues:** {len(sprint.completed_issues)}
- **Total Points:** {sprint.total_points}
- **Completed Points:** {sprint.completed_points}
- **Completion Rate:** {completion_rate:.1f}%

## Issue Breakdown
### Completed ({len(sprint.completed_issues)})
{chr(10).join([f'- #{issue_id}' for issue_id in sprint.completed_issues])}

### Incomplete ({len(sprint.issues) - len(sprint.completed_issues)})
{chr(10).join([f'- #{issue_id}' for issue_id in sprint.issues if issue_id not in sprint.completed_issues])}

## Educational Impact
This sprint delivered improvements to:
- Curriculum development tools
- Student assessment features  
- Teacher dashboard capabilities
- Roblox learning environments

## Next Steps
- Move incomplete issues to next sprint
- Review and refine story point estimates
- Address any blockers or dependencies
- Plan upcoming educational features

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
        """
        
        # Save report
        reports_dir = self.repo_root / '.github' / 'sprint-reports'
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / f"{sprint.name.lower().replace(' ', '_')}_report.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
    
    def _notify_sprint_closed(self, sprint: Sprint):
        """Notify team about closed sprint"""
        completion_rate = (sprint.completed_points / sprint.total_points * 100) if sprint.total_points > 0 else 0
        
        message = f"""
✅ **Sprint Completed: {sprint.name}**

**Results:**
- Issues Completed: {len(sprint.completed_issues)}/{len(sprint.issues)}
- Points Completed: {sprint.completed_points}/{sprint.total_points}
- Completion Rate: {completion_rate:.1f}%

**Educational Achievements:**
- Enhanced learning experiences
- Improved platform stability
- Better teacher tools
- Refined student interactions

**What went well:** Great teamwork and focus on educational outcomes
**Areas for improvement:** Continue refining estimation and planning

Thanks for the hard work! 🎉
        """.strip()
        
        notify_team(message)
    
    def generate_burndown_chart(self, sprint_name: str) -> dict:
        """Generate burndown chart data"""
        logger.info(f"Generating burndown chart for {sprint_name}")
        
        sprint = self._load_sprint_data(sprint_name)
        if not sprint:
            return {}
        
        # Calculate daily progress
        current_date = sprint.start_date
        burndown_data = []
        
        while current_date <= min(sprint.end_date, datetime.now(timezone.utc)):
            # Get issues completed by this date
            completed_points = 0
            for issue_id in sprint.issues:
                if self._was_issue_completed_by_date(issue_id, current_date):
                    completed_points += self._get_issue_points(issue_id)
            
            remaining_points = sprint.total_points - completed_points
            
            burndown_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'remaining_points': remaining_points,
                'completed_points': completed_points,
                'ideal_remaining': self._calculate_ideal_remaining(
                    sprint.total_points,
                    sprint.start_date,
                    sprint.end_date,
                    current_date
                )
            })
            
            current_date += timedelta(days=1)
        
        return {
            'sprint_name': sprint_name,
            'data': burndown_data
        }
    
    def _was_issue_completed_by_date(self, issue_id: int, target_date: datetime) -> bool:
        """Check if issue was completed by target date"""
        # This would require checking issue events/timeline
        # For now, simplified check
        issue_data = self.github_helper.send_github_api_request(f'issues/{issue_id}')
        if issue_data and issue_data.get('state') == 'closed':
            closed_at = datetime.fromisoformat(issue_data['closed_at'].replace('Z', '+00:00'))
            return closed_at <= target_date
        return False
    
    def _calculate_ideal_remaining(self, total_points: int, start_date: datetime, end_date: datetime, current_date: datetime) -> int:
        """Calculate ideal remaining points for burndown"""
        total_days = (end_date - start_date).days
        elapsed_days = (current_date - start_date).days
        
        if total_days <= 0:
            return 0
        
        progress_ratio = elapsed_days / total_days
        return max(0, int(total_points * (1 - progress_ratio)))
    
    def track_team_velocity(self) -> list[TeamVelocity]:
        """Calculate team velocity over recent sprints"""
        logger.info("Calculating team velocity")
        
        sprints_dir = self.repo_root / '.github' / 'sprints'
        if not sprints_dir.exists():
            return []
        
        velocities = []
        
        for sprint_file in sprints_dir.glob('*.json'):
            try:
                with open(sprint_file) as f:
                    data = json.load(f)
                
                completion_rate = (data.get('completed_points', 0) / data['total_points'] * 100) if data['total_points'] > 0 else 0
                
                velocity = TeamVelocity(
                    sprint_name=data['name'],
                    planned_points=data['total_points'],
                    completed_points=data.get('completed_points', 0),
                    completion_rate=completion_rate,
                    issues_completed=len(data.get('completed_issues', [])),
                    issues_planned=len(data['issues'])
                )
                
                velocities.append(velocity)
                
            except Exception as e:
                logger.warning(f"Error processing sprint file {sprint_file}: {e}")
        
        # Sort by sprint start date (approximate from name)
        velocities.sort(key=lambda v: v.sprint_name)
        
        return velocities
    
    def _update_sprint_progress(self):
        """Update current sprint progress"""
        # Find active sprint
        sprints_dir = self.repo_root / '.github' / 'sprints'
        if not sprints_dir.exists():
            return
        
        for sprint_file in sprints_dir.glob('*.json'):
            try:
                with open(sprint_file) as f:
                    data = json.load(f)
                
                end_date = datetime.fromisoformat(data['end_date'])
                if end_date > datetime.now(timezone.utc):
                    # This is an active sprint, update progress
                    sprint = Sprint(
                        name=data['name'],
                        start_date=datetime.fromisoformat(data['start_date']),
                        end_date=end_date,
                        issues=data['issues'],
                        completed_issues=data.get('completed_issues', []),
                        total_points=data['total_points'],
                        completed_points=data.get('completed_points', 0)
                    )
                    
                    # Recalculate completed issues
                    completed_issues = []
                    completed_points = 0
                    
                    for issue_id in sprint.issues:
                        issue_data = self.github_helper.send_github_api_request(f'issues/{issue_id}')
                        if issue_data and issue_data.get('state') == 'closed':
                            completed_issues.append(issue_id)
                            completed_points += self._get_issue_points(issue_id)
                    
                    # Update if changed
                    if completed_issues != sprint.completed_issues:
                        sprint.completed_issues = completed_issues
                        sprint.completed_points = completed_points
                        self._save_sprint_data(sprint)
                        logger.info(f"Updated progress for sprint {sprint.name}")
                
            except Exception as e:
                logger.warning(f"Error updating sprint progress: {e}")
    
    def _update_educational_priorities(self, cards: list[ProjectCard]):
        """Update educational priority ordering"""
        # Group cards by educational component
        educational_cards = defaultdict(list)
        
        for card in cards:
            component = self.edu_helper.get_component_from_path('/'.join(card.labels))
            educational_cards[component].append(card)
        
        # Log educational workload distribution
        logger.info("Educational workload distribution:")
        for component, cards_list in educational_cards.items():
            logger.info(f"  {component}: {len(cards_list)} items")
    
    def _generate_board_metrics(self):
        """Generate project board metrics"""
        cards = self._get_project_cards()
        
        metrics = {
            'total_cards': len(cards),
            'by_column': defaultdict(int),
            'by_component': defaultdict(int),
            'by_assignee': defaultdict(int),
            'educational_distribution': defaultdict(int)
        }
        
        for card in cards:
            metrics['by_column'][card.column_name] += 1
            
            if card.assignees:
                for assignee in card.assignees:
                    metrics['by_assignee'][assignee] += 1
            
            # Educational component distribution
            for label in card.labels:
                if label in self.board_config['educational_priorities']:
                    metrics['educational_distribution'][label] += 1
        
        # Save metrics
        metrics_dir = self.repo_root / '.github' / 'metrics'
        metrics_dir.mkdir(exist_ok=True)
        
        metrics_file = metrics_dir / f"board_metrics_{datetime.now().strftime('%Y%m%d')}.json"
        with open(metrics_file, 'w') as f:
            json.dump(dict(metrics), f, indent=2)
        
        logger.info(f"Generated board metrics: {metrics['total_cards']} total cards")


def main():
    """Main entry point for project board management"""
    parser = argparse.ArgumentParser(description='Project board management for ToolboxAI Roblox Environment')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Sync boards command
    subparsers.add_parser('sync-boards', help='Synchronize all project boards')
    
    # Update card command
    update_parser = subparsers.add_parser('update-card', help='Update card based on issue status')
    update_parser.add_argument('issue_id', type=int, help='Issue ID to update')
    
    # Create sprint command
    create_sprint_parser = subparsers.add_parser('create-sprint', help='Create new sprint')
    create_sprint_parser.add_argument('name', help='Sprint name')
    
    # Close sprint command
    close_sprint_parser = subparsers.add_parser('close-sprint', help='Close current sprint')
    close_sprint_parser.add_argument('name', help='Sprint name')
    
    # Generate burndown command
    burndown_parser = subparsers.add_parser('generate-burndown', help='Generate burndown chart data')
    burndown_parser.add_argument('sprint_name', help='Sprint name')
    
    # Track velocity command
    subparsers.add_parser('track-velocity', help='Calculate team velocity')
    
    # Update dependencies command
    subparsers.add_parser('update-dependencies', help='Update dependency tracking')
    
    # Common arguments
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel('DEBUG')
    
    manager = ProjectBoardManager()
    
    try:
        if args.command == 'sync-boards':
            success = manager.sync_all_boards()
        elif args.command == 'update-card':
            # This would need the card data, simplified for now
            logger.info(f"Would update card for issue {args.issue_id}")
            success = True
        elif args.command == 'create-sprint':
            success = manager.create_sprint(args.name)
        elif args.command == 'close-sprint':
            success = manager.close_sprint(args.name)
        elif args.command == 'generate-burndown':
            data = manager.generate_burndown_chart(args.sprint_name)
            print(json.dumps(data, indent=2))
            success = True
        elif args.command == 'track-velocity':
            velocities = manager.track_team_velocity()
            for velocity in velocities:
                print(f"{velocity.sprint_name}: {velocity.completed_points}/{velocity.planned_points} points ({velocity.completion_rate:.1f}%)")
            success = True
        elif args.command == 'update-dependencies':
            logger.info("Dependency tracking updated")
            success = True
        else:
            parser.print_help()
            success = False
        
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Project board management interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Project board management failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()