"""
Content schema definitions
"""

from ..models.schemas import (
    ContentRequest,
    ContentResponse,
    GeneratedScript,
    TerrainConfiguration,
    GameMechanics,
    LearningObjective,
)

# Content-related schemas
ContentCreateRequest = ContentRequest
ContentCreateResponse = ContentResponse
ScriptGeneration = GeneratedScript
TerrainConfig = TerrainConfiguration
GameConfig = GameMechanics
Objective = LearningObjective

__all__ = [
    "ContentRequest",
    "ContentResponse",
    "GeneratedScript",
    "TerrainConfiguration",
    "GameMechanics",
    "LearningObjective",
    "ContentCreateRequest",
    "ContentCreateResponse",
    "ScriptGeneration",
    "TerrainConfig",
    "GameConfig",
    "Objective",
]
