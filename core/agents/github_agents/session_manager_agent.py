"""
Session Manager Agent for managing Claude Code sessions across worktrees.

This agent manages individual Claude Code sessions, tracks their progress,
and provides insights into session activity and productivity.
"""

import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .base_github_agent import BaseGitHubAgent

logger = logging.getLogger(__name__)


@dataclass
class ClaudeSession:
    """Represents a Claude Code session."""

    session_id: str
    worktree_branch: str
    worktree_path: Path
    started_at: datetime
    last_activity: datetime
    status: str  # active, idle, completed, error
    tasks_completed: list[str] = field(default_factory=list)
    files_modified: set[str] = field(default_factory=set)
    commits_made: list[str] = field(default_factory=list)
    context_switches: int = 0
    total_tokens: int = 0
    error_count: int = 0
    productivity_score: float = 0.0


@dataclass
class SessionMetrics:
    """Aggregated metrics for all sessions."""

    total_sessions: int = 0
    active_sessions: int = 0
    completed_sessions: int = 0
    average_session_duration: float = 0.0
    average_productivity: float = 0.0
    total_tasks_completed: int = 0
    total_files_modified: int = 0
    total_commits: int = 0
    peak_concurrent_sessions: int = 0
    error_rate: float = 0.0


class SessionManagerAgent(BaseGitHubAgent):
    """Manages Claude Code sessions across multiple worktrees."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the session manager agent.

        Args:
            config_path: Path to configuration file
        """
        super().__init__(config_path)
        self.sessions: dict[str, ClaudeSession] = {}
        self.session_history: list[ClaudeSession] = []
        self.metrics = SessionMetrics()
        self.session_log_path = Path(
            "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions-worktrees/.claude-sessions.json"
        )

        # Load existing session data
        self._load_session_history()

    def _load_session_history(self) -> None:
        """Load session history from disk."""
        if self.session_log_path.exists():
            try:
                with open(self.session_log_path) as f:
                    data = json.load(f)
                    # Reconstruct sessions from saved data
                    for session_data in data.get("sessions", []):
                        # Convert datetime strings back to datetime objects
                        session_data["started_at"] = datetime.fromisoformat(
                            session_data["started_at"]
                        )
                        session_data["last_activity"] = datetime.fromisoformat(
                            session_data["last_activity"]
                        )
                        session_data["worktree_path"] = Path(session_data["worktree_path"])
                        session_data["files_modified"] = set(session_data.get("files_modified", []))

                        session = ClaudeSession(**session_data)
                        self.session_history.append(session)

                    # Load metrics
                    if "metrics" in data:
                        for key, value in data["metrics"].items():
                            if hasattr(self.metrics, key):
                                setattr(self.metrics, key, value)
            except Exception as e:
                logger.warning(f"Could not load session history: {e}")

    def _save_session_data(self) -> None:
        """Save session data to disk."""
        try:
            # Prepare data for serialization
            sessions_data = []
            for session in self.session_history + list(self.sessions.values()):
                session_dict = {
                    "session_id": session.session_id,
                    "worktree_branch": session.worktree_branch,
                    "worktree_path": str(session.worktree_path),
                    "started_at": session.started_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "status": session.status,
                    "tasks_completed": session.tasks_completed,
                    "files_modified": list(session.files_modified),
                    "commits_made": session.commits_made,
                    "context_switches": session.context_switches,
                    "total_tokens": session.total_tokens,
                    "error_count": session.error_count,
                    "productivity_score": session.productivity_score,
                }
                sessions_data.append(session_dict)

            # Save to file
            self.session_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_log_path, "w") as f:
                json.dump(
                    {
                        "sessions": sessions_data,
                        "metrics": {
                            "total_sessions": self.metrics.total_sessions,
                            "completed_sessions": self.metrics.completed_sessions,
                            "average_session_duration": self.metrics.average_session_duration,
                            "average_productivity": self.metrics.average_productivity,
                            "total_tasks_completed": self.metrics.total_tasks_completed,
                            "total_files_modified": self.metrics.total_files_modified,
                            "total_commits": self.metrics.total_commits,
                            "peak_concurrent_sessions": self.metrics.peak_concurrent_sessions,
                            "error_rate": self.metrics.error_rate,
                        },
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Could not save session data: {e}")

    async def analyze(self, files: list[str]) -> dict[str, Any]:
        """Analyze files (required by BaseGitHubAgent).

        Args:
            files: List of files to analyze

        Returns:
            Analysis results
        """
        # Not needed for session management
        return {"message": "Session manager doesn't analyze files"}

    async def execute_action(self, action: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute an action (required by BaseGitHubAgent).

        Args:
            action: Action to execute
            context: Action context

        Returns:
            Action result
        """
        # Delegate to execute method
        task = context.copy()
        task["action"] = action
        return await self.execute(task)

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute session management task.

        Args:
            task: Task configuration with action and parameters

        Returns:
            Result of the session management task
        """
        action = task.get("action", "status")

        try:
            if action == "start":
                return await self.start_session(
                    worktree_branch=task.get("worktree_branch"),
                    worktree_path=task.get("worktree_path"),
                )
            elif action == "stop":
                return await self.stop_session(session_id=task.get("session_id"))
            elif action == "monitor":
                return await self.monitor_sessions()
            elif action == "status":
                return await self.get_session_status(session_id=task.get("session_id"))
            elif action == "list":
                return await self.list_sessions()
            elif action == "analyze":
                return await self.analyze_productivity()
            elif action == "summary":
                return await self.generate_summary(session_id=task.get("session_id"))
            elif action == "optimize":
                return await self.optimize_sessions()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f"Error executing session task: {e}")
            return {"success": False, "error": str(e)}

    async def start_session(self, worktree_branch: str, worktree_path: str) -> dict[str, Any]:
        """Start tracking a new Claude Code session.

        Args:
            worktree_branch: Branch name for the worktree
            worktree_path: Path to the worktree

        Returns:
            Session start result
        """
        session_id = f"claude-{worktree_branch}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        session = ClaudeSession(
            session_id=session_id,
            worktree_branch=worktree_branch,
            worktree_path=Path(worktree_path),
            started_at=datetime.now(),
            last_activity=datetime.now(),
            status="active",
        )

        self.sessions[session_id] = session

        # Update metrics
        self.metrics.total_sessions += 1
        self.metrics.active_sessions = len(self.sessions)
        self.metrics.peak_concurrent_sessions = max(
            self.metrics.peak_concurrent_sessions, self.metrics.active_sessions
        )

        # Save session data
        self._save_session_data()

        logger.info(f"Started tracking session: {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "message": f"Session {session_id} started successfully",
        }

    async def stop_session(self, session_id: str) -> dict[str, Any]:
        """Stop tracking a Claude Code session.

        Args:
            session_id: ID of the session to stop

        Returns:
            Session stop result
        """
        if session_id not in self.sessions:
            return {"success": False, "error": f"Session not found: {session_id}"}

        session = self.sessions[session_id]
        session.status = "completed"
        session.last_activity = datetime.now()

        # Calculate productivity score
        session.productivity_score = await self._calculate_productivity(session)

        # Move to history
        self.session_history.append(session)
        del self.sessions[session_id]

        # Update metrics
        self.metrics.completed_sessions += 1
        self.metrics.active_sessions = len(self.sessions)

        # Update averages
        await self._update_metrics()

        # Save session data
        self._save_session_data()

        logger.info(f"Stopped tracking session: {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "productivity_score": session.productivity_score,
            "message": f"Session {session_id} completed",
        }

    async def monitor_sessions(self) -> dict[str, Any]:
        """Monitor all active sessions.

        Returns:
            Monitoring results for all sessions
        """
        monitoring_results = []

        for session_id, session in self.sessions.items():
            # Check if Claude process is still running
            is_active = await self._check_claude_process(session.worktree_path)

            # Check for recent activity
            recent_changes = await self._check_recent_changes(session.worktree_path)

            # Update session
            if is_active:
                session.status = "active" if recent_changes else "idle"
                session.last_activity = datetime.now() if recent_changes else session.last_activity

                # Track file modifications
                if recent_changes:
                    session.files_modified.update(recent_changes)
            else:
                session.status = "inactive"

            monitoring_results.append(
                {
                    "session_id": session_id,
                    "status": session.status,
                    "worktree": session.worktree_branch,
                    "duration": (datetime.now() - session.started_at).total_seconds() / 3600,
                    "files_modified": len(session.files_modified),
                    "last_activity": session.last_activity.isoformat(),
                }
            )

        # Save updated data
        self._save_session_data()

        return {
            "success": True,
            "active_sessions": len(self.sessions),
            "results": monitoring_results,
        }

    async def get_session_status(self, session_id: Optional[str] = None) -> dict[str, Any]:
        """Get status of a specific session or all sessions.

        Args:
            session_id: Optional specific session ID

        Returns:
            Session status information
        """
        if session_id:
            if session_id not in self.sessions:
                # Check history
                for session in self.session_history:
                    if session.session_id == session_id:
                        return {
                            "success": True,
                            "session": self._session_to_dict(session),
                        }
                return {"success": False, "error": f"Session not found: {session_id}"}

            session = self.sessions[session_id]
            return {"success": True, "session": self._session_to_dict(session)}

        # Return all active sessions
        return {
            "success": True,
            "sessions": [self._session_to_dict(session) for session in self.sessions.values()],
        }

    async def list_sessions(self) -> dict[str, Any]:
        """List all sessions (active and historical).

        Returns:
            List of all sessions
        """
        all_sessions = []

        # Add active sessions
        for session in self.sessions.values():
            session_dict = self._session_to_dict(session)
            session_dict["is_active"] = True
            all_sessions.append(session_dict)

        # Add historical sessions (last 50)
        for session in self.session_history[-50:]:
            session_dict = self._session_to_dict(session)
            session_dict["is_active"] = False
            all_sessions.append(session_dict)

        return {
            "success": True,
            "total": len(all_sessions),
            "active": len(self.sessions),
            "completed": len(self.session_history),
            "sessions": all_sessions,
        }

    async def analyze_productivity(self) -> dict[str, Any]:
        """Analyze productivity across all sessions.

        Returns:
            Productivity analysis
        """
        # Analyze active sessions
        active_analysis = []
        for session in self.sessions.values():
            productivity = await self._calculate_productivity(session)
            active_analysis.append(
                {
                    "session_id": session.session_id,
                    "productivity_score": productivity,
                    "duration_hours": (datetime.now() - session.started_at).total_seconds() / 3600,
                    "files_modified": len(session.files_modified),
                    "commits": len(session.commits_made),
                    "tasks": len(session.tasks_completed),
                }
            )

        # Calculate trends
        recent_sessions = self.session_history[-20:] if self.session_history else []
        productivity_trend = []

        for session in recent_sessions:
            productivity_trend.append(
                {
                    "date": session.started_at.date().isoformat(),
                    "productivity": session.productivity_score,
                    "duration": (session.last_activity - session.started_at).total_seconds() / 3600,
                }
            )

        # Identify patterns
        patterns = await self._identify_productivity_patterns()

        return {
            "success": True,
            "active_sessions": active_analysis,
            "productivity_trend": productivity_trend,
            "patterns": patterns,
            "recommendations": await self._generate_recommendations(),
        }

    async def generate_summary(self, session_id: Optional[str] = None) -> dict[str, Any]:
        """Generate a summary for a session or all sessions.

        Args:
            session_id: Optional specific session ID

        Returns:
            Session summary
        """
        if session_id:
            # Find session
            session = self.sessions.get(session_id)
            if not session:
                for s in self.session_history:
                    if s.session_id == session_id:
                        session = s
                        break

            if not session:
                return {"success": False, "error": f"Session not found: {session_id}"}

            # Generate individual summary
            summary = await self._generate_session_summary(session)
            return {"success": True, "summary": summary}

        # Generate overall summary
        total_duration = sum(
            (s.last_activity - s.started_at).total_seconds() / 3600
            for s in self.session_history + list(self.sessions.values())
        )

        total_files = sum(
            len(s.files_modified) for s in self.session_history + list(self.sessions.values())
        )

        total_commits = sum(
            len(s.commits_made) for s in self.session_history + list(self.sessions.values())
        )

        return {
            "success": True,
            "summary": {
                "total_sessions": self.metrics.total_sessions,
                "active_sessions": self.metrics.active_sessions,
                "completed_sessions": self.metrics.completed_sessions,
                "total_duration_hours": total_duration,
                "total_files_modified": total_files,
                "total_commits": total_commits,
                "average_productivity": self.metrics.average_productivity,
                "peak_concurrent": self.metrics.peak_concurrent_sessions,
            },
        }

    async def optimize_sessions(self) -> dict[str, Any]:
        """Optimize active sessions for better performance.

        Returns:
            Optimization results
        """
        optimizations = []

        for session_id, session in self.sessions.items():
            # Check for idle sessions
            idle_time = (datetime.now() - session.last_activity).total_seconds() / 60

            if idle_time > 30:  # 30 minutes idle
                optimizations.append(
                    {
                        "session_id": session_id,
                        "type": "idle_session",
                        "recommendation": "Consider pausing or closing idle session",
                        "idle_minutes": idle_time,
                    }
                )

            # Check for high error rate
            if session.error_count > 5:
                optimizations.append(
                    {
                        "session_id": session_id,
                        "type": "high_errors",
                        "recommendation": "Review errors and consider restarting session",
                        "error_count": session.error_count,
                    }
                )

            # Check for context switching
            if session.context_switches > 10:
                optimizations.append(
                    {
                        "session_id": session_id,
                        "type": "context_switching",
                        "recommendation": "Too many context switches, consider focusing on single task",
                        "switches": session.context_switches,
                    }
                )

        return {
            "success": True,
            "optimizations": optimizations,
            "count": len(optimizations),
        }

    async def _check_claude_process(self, worktree_path: Path) -> bool:
        """Check if Claude process is running for a worktree.

        Args:
            worktree_path: Path to the worktree

        Returns:
            True if Claude process is active
        """
        cmd = f"pgrep -f 'claude.*{worktree_path}'"
        result = subprocess.run(cmd, shell=True, capture_output=True)
        return result.returncode == 0

    async def _check_recent_changes(self, worktree_path: Path) -> list[str]:
        """Check for recent file changes in worktree.

        Args:
            worktree_path: Path to the worktree

        Returns:
            List of recently modified files
        """
        if not worktree_path.exists():
            return []

        # Check git status for changes
        cmd = ["git", "status", "--porcelain"]
        result = subprocess.run(cmd, cwd=str(worktree_path), capture_output=True, text=True)

        if result.returncode == 0:
            changed_files = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    # Extract filename from git status output
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        changed_files.append(parts[-1])
            return changed_files

        return []

    async def _calculate_productivity(self, session: ClaudeSession) -> float:
        """Calculate productivity score for a session.

        Args:
            session: Claude session

        Returns:
            Productivity score (0-100)
        """
        score = 0.0

        # Duration factor (optimal: 2-4 hours)
        duration_hours = (session.last_activity - session.started_at).total_seconds() / 3600
        if 2 <= duration_hours <= 4:
            score += 20
        elif duration_hours < 2:
            score += duration_hours * 10
        else:
            score += max(0, 20 - (duration_hours - 4) * 2)

        # Files modified factor
        file_count = len(session.files_modified)
        score += min(20, file_count * 2)

        # Commits factor
        commit_count = len(session.commits_made)
        score += min(20, commit_count * 5)

        # Tasks completed factor
        task_count = len(session.tasks_completed)
        score += min(20, task_count * 4)

        # Error penalty
        error_penalty = min(10, session.error_count * 2)
        score -= error_penalty

        # Context switch penalty
        switch_penalty = min(10, session.context_switches)
        score -= switch_penalty

        return max(0, min(100, score))

    async def _update_metrics(self) -> None:
        """Update aggregated metrics."""
        all_sessions = self.session_history + list(self.sessions.values())

        if all_sessions:
            # Average session duration
            total_duration = sum(
                (s.last_activity - s.started_at).total_seconds() / 3600 for s in all_sessions
            )
            self.metrics.average_session_duration = total_duration / len(all_sessions)

            # Average productivity
            total_productivity = sum(s.productivity_score for s in all_sessions)
            self.metrics.average_productivity = total_productivity / len(all_sessions)

            # Total tasks, files, commits
            self.metrics.total_tasks_completed = sum(len(s.tasks_completed) for s in all_sessions)
            self.metrics.total_files_modified = sum(len(s.files_modified) for s in all_sessions)
            self.metrics.total_commits = sum(len(s.commits_made) for s in all_sessions)

            # Error rate
            total_errors = sum(s.error_count for s in all_sessions)
            self.metrics.error_rate = total_errors / len(all_sessions) if all_sessions else 0

    async def _identify_productivity_patterns(self) -> list[dict[str, Any]]:
        """Identify productivity patterns from session history.

        Returns:
            List of identified patterns
        """
        patterns = []

        if len(self.session_history) < 5:
            return patterns

        # Time of day analysis
        hour_productivity = {}
        for session in self.session_history[-50:]:
            hour = session.started_at.hour
            if hour not in hour_productivity:
                hour_productivity[hour] = []
            hour_productivity[hour].append(session.productivity_score)

        # Find most productive hours
        best_hours = sorted(
            [(hour, sum(scores) / len(scores)) for hour, scores in hour_productivity.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        if best_hours:
            patterns.append(
                {
                    "type": "time_of_day",
                    "description": "Most productive hours",
                    "data": best_hours,
                }
            )

        # Session duration analysis
        duration_productivity = {}
        for session in self.session_history[-50:]:
            duration_bucket = int(
                (session.last_activity - session.started_at).total_seconds() / 3600
            )
            if duration_bucket not in duration_productivity:
                duration_productivity[duration_bucket] = []
            duration_productivity[duration_bucket].append(session.productivity_score)

        # Find optimal duration
        if duration_productivity:
            optimal_duration = max(
                duration_productivity.items(),
                key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0,
            )
            patterns.append(
                {
                    "type": "session_duration",
                    "description": f"Optimal session duration: {optimal_duration[0]} hours",
                    "average_productivity": sum(optimal_duration[1]) / len(optimal_duration[1]),
                }
            )

        return patterns

    async def _generate_recommendations(self) -> list[str]:
        """Generate productivity recommendations.

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check for too many concurrent sessions
        if self.metrics.active_sessions > 5:
            recommendations.append("Consider reducing concurrent sessions to maintain focus")

        # Check error rate
        if self.metrics.error_rate > 3:
            recommendations.append(
                "High error rate detected. Review common errors and improve tooling"
            )

        # Check average productivity
        if self.metrics.average_productivity < 50:
            recommendations.append(
                "Productivity could be improved. Consider shorter, focused sessions"
            )

        # Check session duration
        if self.metrics.average_session_duration > 6:
            recommendations.append(
                "Sessions are running long. Consider taking breaks every 2-3 hours"
            )

        return recommendations

    async def _generate_session_summary(self, session: ClaudeSession) -> dict[str, Any]:
        """Generate summary for a single session.

        Args:
            session: Claude session

        Returns:
            Session summary
        """
        duration = (session.last_activity - session.started_at).total_seconds() / 3600

        return {
            "session_id": session.session_id,
            "worktree": session.worktree_branch,
            "status": session.status,
            "duration_hours": duration,
            "started": session.started_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "productivity_score": session.productivity_score,
            "stats": {
                "files_modified": len(session.files_modified),
                "commits_made": len(session.commits_made),
                "tasks_completed": len(session.tasks_completed),
                "context_switches": session.context_switches,
                "errors": session.error_count,
            },
            "files": list(session.files_modified)[:10],  # Top 10 files
            "commits": session.commits_made[:5],  # Last 5 commits
        }

    def _session_to_dict(self, session: ClaudeSession) -> dict[str, Any]:
        """Convert session to dictionary.

        Args:
            session: Claude session

        Returns:
            Session dictionary
        """
        return {
            "session_id": session.session_id,
            "worktree_branch": session.worktree_branch,
            "worktree_path": str(session.worktree_path),
            "started_at": session.started_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "status": session.status,
            "productivity_score": session.productivity_score,
            "files_modified": len(session.files_modified),
            "commits_made": len(session.commits_made),
            "tasks_completed": len(session.tasks_completed),
        }

    def get_report(self) -> dict[str, Any]:
        """Generate a report of session management activities.

        Returns:
            Report data
        """
        return {
            "agent": "SessionManagerAgent",
            "status": "operational",
            "sessions": {
                "active": self.metrics.active_sessions,
                "completed": self.metrics.completed_sessions,
                "total": self.metrics.total_sessions,
            },
            "metrics": {
                "average_duration_hours": self.metrics.average_session_duration,
                "average_productivity": self.metrics.average_productivity,
                "peak_concurrent": self.metrics.peak_concurrent_sessions,
                "error_rate": self.metrics.error_rate,
            },
            "productivity": {
                "tasks_completed": self.metrics.total_tasks_completed,
                "files_modified": self.metrics.total_files_modified,
                "commits_made": self.metrics.total_commits,
            },
        }
