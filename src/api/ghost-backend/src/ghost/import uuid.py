import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

if TYPE_CHECKING:
    # typing-only imports for repository signatures
    from sqlalchemy import and_, desc, func, select
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session, selectinload

    from .agent_models import AgentState, AgentTask, AgentType, AIAgent, TaskStatus

    # model types referenced in annotations
    from .educational_models import (
        ContentObjective,
        DifficultyLevel,
        EducationalContent,
        EnvironmentType,
        LearningObjective,
        SubjectType,
    )
    from .models import BaseRepository, SPARCStateType, T
    from .quiz_models import MasteryLevel, Quiz, QuizAttempt, QuizQuestion


# At runtime, many of the names imported inside TYPE_CHECKING are used
# unquoted in annotations (this project does not rely on
# `from __future__ import annotations` everywhere). Provide permissive
# runtime aliases so importing this module doesn't raise NameError and so
# static analysis has concrete symbols to reference. Keep them as `Any`
# to avoid changing runtime behavior.
if not TYPE_CHECKING:
    # SQLAlchemy session aliases (runtime-safe fallbacks)
    Session = Any  # type: ignore
    AsyncSession = Any  # type: ignore

    # Domain model/type aliases used in annotations
    AgentState = Any  # type: ignore
    AgentTask = Any  # type: ignore
    AgentType = Any  # type: ignore
    AIAgent = Any  # type: ignore
    TaskStatus = Any  # type: ignore

    ContentObjective = Any  # type: ignore
    DifficultyLevel = Any  # type: ignore
    EducationalContent = Any  # type: ignore
    EnvironmentType = Any  # type: ignore
    LearningObjective = Any  # type: ignore
    SubjectType = Any  # type: ignore

    BaseRepository = Any  # type: ignore
    SPARCStateType = Any  # type: ignore
    T = Any  # type: ignore

    MasteryLevel = Any  # type: ignore
    Quiz = Any  # type: ignore
    QuizAttempt = Any  # type: ignore
    QuizQuestion = Any  # type: ignore


def _as_async(session: Union["Session", "AsyncSession"]):
    """Return the session cast to an AsyncSession when caller knows it's async.

    This helper avoids complex typing casts at each call site and is used
    by repository methods that accept either sync or async sessions.
    """
    return session


class EducationalContentRepository:
    def __init__(self, session: Union["Session", "AsyncSession"]):
        self.session = session
        self._is_async: bool = bool(getattr(session, "_is_async", False))

    async def get_by_bloom_level_async(
        self, bloom_level: str, grade_level: Optional[int] = None
    ) -> List[LearningObjective]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = select(LearningObjective).filter(
            LearningObjective.bloom_level == bloom_level
        )
        if grade_level:
            query = query.filter(LearningObjective.grade_level == grade_level)
        result = await session.execute(query)
        return list(result.scalars())


class LearningObjectiveRepository(BaseRepository[LearningObjective]):
    def __init__(self, session: Union["Session", "AsyncSession"]):
        super().__init__(LearningObjective, session)
        self._is_async: bool = bool(getattr(session, "_is_async", False))

    async def get_by_curriculum_standard_async(
        self, standard: str, subject: Optional[SubjectType] = None
    ) -> List[LearningObjective]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = select(LearningObjective).filter(
            LearningObjective.curriculum_standard == standard
        )
        if subject:
            query = query.filter(LearningObjective.subject == subject.value)
        result = await session.execute(query)
        return list(result.scalars())


class QuizRepository(BaseRepository[Quiz]):
    def __init__(self, session: Union["Session", "AsyncSession"]):
        super().__init__(Quiz, session)
        self._is_async: bool = bool(getattr(session, "_is_async", False))

    async def get_with_questions_async(self, quiz_id: str) -> Optional[Quiz]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = (
            select(Quiz)
            .options(selectinload(Quiz.questions).selectinload(QuizQuestion.options))
            .filter(Quiz.id == uuid.UUID(quiz_id))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_adaptive_quizzes_async(
        self, subject: SubjectType, grade_level: int
    ) -> List[Quiz]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = select(Quiz).filter(
            Quiz.subject == subject.value,
            Quiz.grade_level == grade_level,
            Quiz.is_adaptive == True,
            Quiz.is_deleted == False,
        )
        result = await session.execute(query)
        return list(result.scalars())

    async def get_student_attempts_async(
        self, user_id: str, quiz_id: Optional[str] = None, limit: int = 10
    ) -> List[QuizAttempt]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = select(QuizAttempt).filter(QuizAttempt.user_id == uuid.UUID(user_id))
        if quiz_id:
            query = query.filter(QuizAttempt.quiz_id == uuid.UUID(quiz_id))
        query = query.order_by(desc(QuizAttempt.created_at)).limit(limit)
        result = await session.execute(query)
        return list(result.scalars())

    async def calculate_mastery_level_async(
        self, user_id: str, subject: SubjectType, grade_level: int
    ) -> Optional[MasteryLevel]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = (
            select(QuizAttempt)
            .join(Quiz)
            .filter(
                QuizAttempt.user_id == uuid.UUID(user_id),
                Quiz.subject == subject.value,
                Quiz.grade_level == grade_level,
                QuizAttempt.completed_at.isnot(None),
            )
            .order_by(desc(QuizAttempt.completed_at))
            .limit(20)
        )
        result = await session.execute(query)
        attempts = list(result.scalars())
        if not attempts:
            return None
        scores = [float(a.score) for a in attempts if a.score]
        if not scores:
            return None
        avg = sum(scores) / len(scores)
        if avg >= 90:
            return MasteryLevel.EXPERT
        if avg >= 80:
            return MasteryLevel.ADVANCED
        if avg >= 70:
            return MasteryLevel.PROFICIENT
        if avg >= 60:
            return MasteryLevel.DEVELOPING
        return MasteryLevel.NOVICE


class AIAgentRepository(BaseRepository[AIAgent]):
    def __init__(self, session: Union["Session", "AsyncSession"]):
        super().__init__(AIAgent, session)
        self._is_async: bool = bool(getattr(session, "_is_async", False))

    async def get_active_agents_async(
        self, agent_type: Optional[AgentType] = None
    ) -> List[AIAgent]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = select(AIAgent).filter(
            AIAgent.is_active == True,
            AIAgent.status == "active",
            AIAgent.is_deleted == False,
        )
        if agent_type:
            query = query.filter(AIAgent.agent_type == agent_type.value)
        query = query.order_by(AIAgent.priority, AIAgent.name)
        result = await session.execute(query)
        return list(result.scalars())

    async def get_by_capabilities_async(self, required_capabilities: List[str]) -> List[AIAgent]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = select(AIAgent).filter(
            AIAgent.is_active == True,
            AIAgent.capabilities.op("@>")(required_capabilities),
            AIAgent.is_deleted == False,
        )
        result = await session.execute(query)
        return list(result.scalars())

    async def update_health_status_async(
        self, agent_id: str, is_healthy: bool, error_message: Optional[str] = None
    ) -> Optional[AIAgent]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        agent = await self.get_async(agent_id)
        if not agent:
            return None
        agent.last_health_check = datetime.now(timezone.utc)
        if is_healthy:
            agent.status = "active"
            agent.error_count = 0
            agent.last_error = None
        else:
            agent.status = "error"
            agent.error_count += 1
            agent.last_error = error_message
            if agent.error_count >= 5:
                agent.is_active = False
        session = _as_async(self.session)
        await session.flush()
        return agent


class AgentTaskRepository(BaseRepository[AgentTask]):
    def __init__(self, session: Union["Session", "AsyncSession"]):
        super().__init__(AgentTask, session)
        self._is_async: bool = bool(getattr(session, "_is_async", False))

    async def get_pending_tasks_async(
        self, agent_type: Optional[AgentType] = None, priority_threshold: int = 5
    ) -> List[AgentTask]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = select(AgentTask).filter(
            AgentTask.status == TaskStatus.PENDING.value,
            AgentTask.priority <= priority_threshold,
        )
        if agent_type:
            query = query.join(AIAgent).filter(AIAgent.agent_type == agent_type.value)
        query = query.order_by(AgentTask.priority, AgentTask.created_at)
        result = await session.execute(query)
        return list(result.scalars())

    async def get_workflow_tasks_async(self, workflow_id: str) -> List[AgentTask]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = (
            select(AgentTask)
            .filter(AgentTask.workflow_id == uuid.UUID(workflow_id))
            .order_by(AgentTask.created_at)
        )
        result = await session.execute(query)
        return list(result.scalars())

    async def assign_task_async(self, task_id: str, agent_id: str) -> Optional[AgentTask]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        task = await self.get_async(task_id)
        if not task or task.status != TaskStatus.PENDING.value:
            return None
        task.agent_id = uuid.UUID(agent_id)
        task.status = TaskStatus.ASSIGNED.value
        task.assigned_at = datetime.now(timezone.utc)
        session = _as_async(self.session)
        await session.flush()
        return task

    async def start_task_async(self, task_id: str) -> Optional[AgentTask]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        task = await self.get_async(task_id)
        if not task or task.status != TaskStatus.ASSIGNED.value:
            return None
        task.status = TaskStatus.RUNNING.value
        task.started_at = datetime.now(timezone.utc)
        session = _as_async(self.session)
        await session.flush()
        return task

    async def complete_task_async(
        self,
        task_id: str,
        output_data: Dict[str, Any],
        quality_score: Optional[float] = None,
    ) -> Optional[AgentTask]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        task = await self.get_async(task_id)
        if not task or task.status != TaskStatus.RUNNING.value:
            return None
        now = datetime.now(timezone.utc)
        task.status = TaskStatus.COMPLETED.value
        task.completed_at = now
        task.output_data = output_data
        task.progress_percentage = 100
        if quality_score is not None:
            task.quality_score = quality_score
        if task.started_at:
            duration = (now - task.started_at).total_seconds()
            task.duration_seconds = int(duration)
        session = _as_async(self.session)
        await session.flush()
        return task


class AgentStateRepository(BaseRepository[AgentState]):
    def __init__(self, session: Union["Session", "AsyncSession"]):
        super().__init__(AgentState, session)
        self._is_async: bool = bool(getattr(session, "_is_async", False))

    async def get_workflow_states_async(
        self, workflow_id: str, state_type: Optional[SPARCStateType] = None
    ) -> List[AgentState]:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = select(AgentState).filter(AgentState.workflow_id == uuid.UUID(workflow_id))
        if state_type:
            query = query.filter(AgentState.state_type == state_type.value)
        query = query.order_by(AgentState.state_type, AgentState.sequence_number)
        result = await session.execute(query)
        return list(result.scalars())

    async def create_state_async(
        self,
        agent_id: str,
        workflow_id: str,
        state_type: SPARCStateType,
        state_data: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> AgentState:
        if not self._is_async:
            raise RuntimeError("Async session required")
        session = _as_async(self.session)
        query = select(func.max(AgentState.sequence_number)).filter(
            AgentState.workflow_id == uuid.UUID(workflow_id),
            AgentState.state_type == state_type.value,
        )
        result = await session.execute(query)
        max_seq = result.scalar() or 0
        state = AgentState(
            agent_id=uuid.UUID(agent_id),
            workflow_id=uuid.UUID(workflow_id),
            state_type=state_type.value,
            state_data=state_data,
            sequence_number=max_seq + 1,
            task_id=uuid.UUID(task_id) if task_id else None,
        )
        session.add(state)
        await session.flush()
        return state


class RepositoryFactory:
    def __init__(self, session: Union["Session", "AsyncSession"]):
        self.session = session

    @property
    def educational_content(self) -> EducationalContentRepository:
        return EducationalContentRepository(self.session)

    @property
    def learning_objectives(self) -> LearningObjectiveRepository:
        return LearningObjectiveRepository(self.session)

    @property
    def quiz(self) -> QuizRepository:
        return QuizRepository(self.session)

    @property
    def ai_agent(self) -> AIAgentRepository:
        return AIAgentRepository(self.session)

    @property
    def agent_task(self) -> AgentTaskRepository:
        return AgentTaskRepository(self.session)

    @property
    def agent_state(self) -> AgentStateRepository:
        return AgentStateRepository(self.session)


__all__ = [
    "EducationalContentRepository",
    "LearningObjectiveRepository",
    "QuizRepository",
    "AIAgentRepository",
    "AgentTaskRepository",
    "AgentStateRepository",
    "RepositoryFactory"
]            return AgentStateRepository(self.session)