"""SPARC State Manager - Manages reasoning chain state

SPARC Framework: Specification, Pseudocode, Architecture, Refinement, Completion
"""
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SPARCPhase(Enum):
    """SPARC Framework phases"""
    SPECIFICATION = "specification"
    PSEUDOCODE = "pseudocode"
    ARCHITECTURE = "architecture"
    REFINEMENT = "refinement"
    COMPLETION = "completion"


class StateManager:
    """
    SPARC Framework State Manager

    Manages state transitions through the SPARC reasoning chain.
    Tracks progress through specification, pseudocode, architecture,
    refinement, and completion phases.
    """

    def __init__(self):
        """Initialize state manager"""
        self.current_phase = SPARCPhase.SPECIFICATION
        self.phase_history = []
        self.state_data = {}
        logger.info("SPARC StateManager initialized")

    def transition_to(self, phase: SPARCPhase):
        """Transition to new SPARC phase"""
        logger.info(f"Transitioning from {self.current_phase.value} to {phase.value}")
        self.phase_history.append(self.current_phase)
        self.current_phase = phase

    def set_phase_data(self, phase: SPARCPhase, data: Dict[str, Any]):
        """Store data for specific phase"""
        self.state_data[phase.value] = data

    def get_phase_data(self, phase: SPARCPhase) -> Optional[Dict[str, Any]]:
        """Retrieve data for specific phase"""
        return self.state_data.get(phase.value)

    def get_current_phase(self) -> SPARCPhase:
        """Get current phase"""
        return self.current_phase

    def reset(self):
        """Reset to initial state"""
        self.current_phase = SPARCPhase.SPECIFICATION
        self.phase_history = []
        self.state_data = {}
        logger.info("State reset to SPECIFICATION phase")


__all__ = ['StateManager', 'SPARCPhase']
