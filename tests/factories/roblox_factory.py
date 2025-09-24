"""Roblox-related test data factories."""

import factory
from factory import fuzzy
from faker import Faker
from .base_factory import DictFactory, AsyncMixin
import json

fake = Faker()


class RobloxScriptFactory(DictFactory, AsyncMixin):
    """Factory for Roblox Luau scripts."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    name = factory.LazyFunction(lambda: f"{fake.word()}Script")
    script_type = fuzzy.FuzzyChoice(["ServerScript", "LocalScript", "ModuleScript"])
    parent_path = factory.LazyFunction(
        lambda: fake.random_element([
            "game.ServerScriptService",
            "game.StarterPlayer.StarterPlayerScripts",
            "game.ReplicatedStorage",
            "game.Workspace"
        ])
    )

    # Script content
    @factory.lazy_attribute
    def content(self):
        """Generate sample Luau script content."""
        if self.script_type == "ServerScript":
            return """-- Server Script
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function onPlayerAdded(player)
    print("Player joined:", player.Name)
    -- Add your server logic here
end

Players.PlayerAdded:Connect(onPlayerAdded)
"""
        elif self.script_type == "LocalScript":
            return """-- Local Script
local Players = game:GetService("Players")
local player = Players.LocalPlayer
local character = player.Character or player.CharacterAdded:Wait()

local humanoid = character:WaitForChild("Humanoid")

-- Add your client logic here
print("Local script initialized for", player.Name)
"""
        else:  # ModuleScript
            return """-- Module Script
local Module = {}
Module.__index = Module

function Module.new(name)
    local self = setmetatable({}, Module)
    self.name = name
    self.data = {}
    return self
end

function Module:getData()
    return self.data
end

return Module
"""

    # Metadata
    created_at = factory.LazyFunction(lambda: fake.date_time_this_year().isoformat())
    updated_at = factory.LazyFunction(lambda: fake.date_time_this_month().isoformat())
    author_id = factory.LazyFunction(lambda: fake.uuid4())
    version = factory.LazyFunction(lambda: f"{fake.random_int(1, 3)}.{fake.random_int(0, 9)}.{fake.random_int(0, 99)}")

    # Security and optimization
    security_issues = factory.LazyFunction(
        lambda: [
            {
                "type": fake.random_element(["remote_exploit", "data_leak", "permission_bypass"]),
                "severity": fake.random_element(["low", "medium", "high", "critical"]),
                "line": fake.random_int(1, 100),
                "description": fake.sentence(),
            }
            for _ in range(fake.random_int(0, 3))
        ]
    )

    optimization_suggestions = factory.LazyFunction(
        lambda: [
            {
                "type": fake.random_element(["performance", "memory", "network"]),
                "location": f"line {fake.random_int(1, 100)}",
                "suggestion": fake.sentence(),
                "impact": fake.random_element(["minor", "moderate", "major"]),
            }
            for _ in range(fake.random_int(0, 5))
        ]
    )

    # Dependencies
    dependencies = factory.LazyFunction(
        lambda: [
            {
                "module": fake.random_element(["DataStore2", "Roact", "Knit", "Promise"]),
                "version": f"{fake.random_int(1, 3)}.{fake.random_int(0, 9)}.{fake.random_int(0, 99)}",
                "required": fake.boolean(),
            }
            for _ in range(fake.random_int(0, 4))
        ]
    )

    # Testing
    test_coverage = factory.LazyFunction(lambda: round(fake.random.uniform(0, 100), 2))
    tests_passed = factory.LazyFunction(lambda: fake.random_int(0, 50))
    tests_failed = factory.LazyFunction(lambda: fake.random_int(0, 10))

    @classmethod
    def with_educational_content(cls, **kwargs):
        """Create script with educational comments."""
        script = cls.create(**kwargs)
        script["educational_annotations"] = [
            {
                "line": fake.random_int(1, 50),
                "concept": fake.random_element(["loops", "events", "functions", "variables", "tables"]),
                "explanation": fake.paragraph(),
                "difficulty": fake.random_element(["beginner", "intermediate", "advanced"]),
            }
            for _ in range(fake.random_int(3, 10))
        ]
        return script


class RobloxEnvironmentFactory(DictFactory):
    """Factory for Roblox game environments."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    name = factory.LazyFunction(lambda: f"{fake.word().title()} World")
    place_id = factory.LazyFunction(lambda: fake.random_int(1000000, 9999999))
    universe_id = factory.LazyFunction(lambda: fake.random_int(100000, 999999))

    # Environment type
    environment_type = fuzzy.FuzzyChoice([
        "classroom", "laboratory", "playground",
        "adventure", "puzzle", "simulation"
    ])

    # Game settings
    max_players = factory.LazyFunction(lambda: fake.random_int(1, 50))
    genre = fuzzy.FuzzyChoice([
        "Education", "Adventure", "Simulation",
        "Role Playing", "Building", "Puzzle"
    ])

    # Educational settings
    subject = fuzzy.FuzzyChoice([
        "Mathematics", "Science", "Programming",
        "History", "Language Arts", "Art"
    ])
    grade_levels = factory.LazyFunction(
        lambda: list(range(
            fake.random_int(1, 6),
            fake.random_int(7, 12) + 1
        ))
    )

    # Components
    components = factory.LazyFunction(
        lambda: {
            "spawn_points": fake.random_int(1, 10),
            "interactive_objects": fake.random_int(5, 50),
            "npcs": fake.random_int(0, 20),
            "quests": fake.random_int(0, 10),
            "checkpoints": fake.random_int(3, 15),
            "leaderboards": fake.boolean(),
            "chat_enabled": fake.boolean(),
            "teams_enabled": fake.boolean(),
        }
    )

    # Assets
    assets = factory.LazyFunction(
        lambda: [
            {
                "id": fake.random_int(1000000, 9999999),
                "type": fake.random_element(["Model", "Decal", "Sound", "Mesh", "Animation"]),
                "name": fake.word(),
                "url": fake.url(),
            }
            for _ in range(fake.random_int(10, 50))
        ]
    )

    # Learning objectives
    learning_objectives = factory.LazyFunction(
        lambda: [fake.sentence() for _ in range(fake.random_int(3, 8))]
    )

    # Game mechanics
    game_mechanics = factory.LazyFunction(
        lambda: {
            "scoring_system": fake.random_element(["points", "levels", "achievements", "grades"]),
            "progression_type": fake.random_element(["linear", "open_world", "branching"]),
            "difficulty_scaling": fake.boolean(),
            "collaborative_features": fake.boolean(),
            "competitive_elements": fake.boolean(),
        }
    )

    # Analytics
    analytics = factory.LazyFunction(
        lambda: {
            "total_plays": fake.random_int(0, 100000),
            "average_session_length": fake.random_int(5, 60),
            "completion_rate": round(fake.random.uniform(0.3, 0.95), 2),
            "user_rating": round(fake.random.uniform(3.0, 5.0), 1),
            "engagement_score": round(fake.random.uniform(0.5, 1.0), 2),
        }
    )

    # Status
    status = fuzzy.FuzzyChoice(["development", "testing", "published", "maintenance"])
    published_date = factory.LazyFunction(lambda: fake.date_this_year().isoformat() if fake.boolean() else None)
    last_updated = factory.LazyFunction(lambda: fake.date_time_this_month().isoformat())

    @classmethod
    def with_scripts(cls, num_scripts: int = 5, **kwargs):
        """Create environment with associated scripts."""
        environment = cls.create(**kwargs)
        environment["scripts"] = [
            RobloxScriptFactory.create()
            for _ in range(num_scripts)
        ]
        return environment

    @classmethod
    def with_lesson_plan(cls, **kwargs):
        """Create environment with educational lesson plan."""
        environment = cls.create(**kwargs)
        environment["lesson_plan"] = {
            "title": fake.catch_phrase(),
            "duration_minutes": fake.random_int(30, 90),
            "objectives": [fake.sentence() for _ in range(fake.random_int(3, 6))],
            "materials_needed": [fake.word() for _ in range(fake.random_int(2, 5))],
            "activities": [
                {
                    "name": fake.sentence(),
                    "duration": fake.random_int(5, 20),
                    "type": fake.random_element(["introduction", "exploration", "challenge", "assessment"]),
                    "description": fake.paragraph(),
                }
                for _ in range(fake.random_int(3, 7))
            ],
            "assessment_criteria": [
                {
                    "criterion": fake.word(),
                    "weight": fake.random_int(10, 30),
                    "description": fake.sentence(),
                }
                for _ in range(fake.random_int(3, 5))
            ],
        }
        return environment


class RobloxPlayerFactory(DictFactory):
    """Factory for Roblox player data."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    roblox_user_id = factory.LazyFunction(lambda: fake.random_int(1000000, 999999999))
    username = factory.LazyFunction(lambda: fake.user_name())
    display_name = factory.LazyFunction(lambda: fake.name())

    # Avatar
    avatar = factory.LazyFunction(
        lambda: {
            "thumbnail_url": fake.image_url(),
            "avatar_type": fake.random_element(["R15", "R6"]),
            "accessories": [fake.random_int(1000000, 9999999) for _ in range(fake.random_int(0, 10))],
        }
    )

    # Player stats
    stats = factory.LazyFunction(
        lambda: {
            "level": fake.random_int(1, 100),
            "experience": fake.random_int(0, 100000),
            "coins": fake.random_int(0, 10000),
            "achievements": fake.random_int(0, 50),
            "play_time_hours": fake.random_int(0, 1000),
            "games_played": fake.random_int(0, 500),
        }
    )

    # Educational progress
    educational_progress = factory.LazyFunction(
        lambda: {
            "lessons_completed": fake.random_int(0, 100),
            "quizzes_taken": fake.random_int(0, 50),
            "average_score": round(fake.random.uniform(60, 100), 1),
            "skills_unlocked": [fake.word() for _ in range(fake.random_int(5, 20))],
            "badges_earned": [
                {
                    "name": fake.word(),
                    "icon": fake.image_url(),
                    "earned_date": fake.date_this_year().isoformat(),
                }
                for _ in range(fake.random_int(0, 15))
            ],
        }
    )

    # Session data
    session_data = factory.LazyFunction(
        lambda: {
            "session_id": fake.uuid4(),
            "started_at": fake.date_time_this_week().isoformat(),
            "device": fake.random_element(["PC", "Mobile", "Tablet", "Console"]),
            "platform": fake.random_element(["Windows", "iOS", "Android", "Xbox"]),
            "connection_quality": fake.random_element(["excellent", "good", "fair", "poor"]),
        }
    )