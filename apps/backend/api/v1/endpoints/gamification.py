import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Query

router = APIRouter()


# Mock leaderboard data for development
def generate_mock_leaderboard(timeframe: str = "weekly") -> list[dict]:
    """Generate mock leaderboard data for development"""
    names = [
        "Alex Thompson",
        "Sarah Johnson",
        "Mike Chen",
        "Emily Davis",
        "Chris Brown",
        "Jessica Lee",
        "David Wilson",
        "Amanda Garcia",
        "Ryan Martinez",
        "Lisa Anderson",
        "Kevin Park",
        "Maria Rodriguez",
    ]

    classes = ["Math 101", "Science 201", "English 301", "History 401"]

    leaderboard = []
    for i, name in enumerate(names):
        # Vary XP based on timeframe
        base_xp = 1000 - (i * 50)
        if timeframe == "daily":
            xp = base_xp // 7
        elif timeframe == "monthly":
            xp = base_xp * 4
        else:  # weekly
            xp = base_xp

        entry = {
            "userId": f"user_{i+1}",
            "displayName": name,
            "className": random.choice(classes),
            "xp": max(xp + random.randint(-100, 100), 100),
            "level": max(1, (xp // 500) + 1),
            "badgesCount": random.randint(1, 15),
            "streakDays": random.randint(0, 30),
            "rank": i + 1,
            "previousRank": i + 1 + random.randint(-2, 2),
            "avatarUrl": f"https://api.dicebear.com/7.x/avataaars/svg?seed={name.replace(' ', '')}",
            "trend": random.choice(["up", "down", "stable"]),
        }
        leaderboard.append(entry)

    # Sort by XP
    leaderboard.sort(key=lambda x: x["xp"], reverse=True)

    # Update ranks based on sorted order
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
        # Determine trend based on rank change
        if entry["previousRank"] > entry["rank"]:
            entry["trend"] = "up"
        elif entry["previousRank"] < entry["rank"]:
            entry["trend"] = "down"
        else:
            entry["trend"] = "stable"

    return leaderboard


@router.get("/leaderboard")
async def get_leaderboard(
    classId: str | None = Query(None, description="Filter by class ID"),
    timeframe: str | None = Query("weekly", description="Time period: daily, weekly, monthly, all"),
) -> list[dict]:
    """
    Get gamification leaderboard

    Returns a list of users ranked by XP for the specified timeframe
    """
    # For development, return mock data
    leaderboard = generate_mock_leaderboard(timeframe)

    # If classId is provided, filter (in production this would be a DB query)
    if classId:
        # For mock data, just return as-is since we don't have real class filtering
        pass

    return leaderboard


@router.get("/achievements")
async def get_achievements(
    userId: str | None = Query(None, description="User ID to get achievements for")
) -> list[dict]:
    """Get list of available achievements and user progress"""
    achievements = [
        {
            "id": "first_lesson",
            "name": "First Steps",
            "description": "Complete your first lesson",
            "xpReward": 50,
            "badgeIcon": "🎯",
            "unlocked": True,
            "unlockedAt": datetime.utcnow().isoformat(),
        },
        {
            "id": "week_streak",
            "name": "Week Warrior",
            "description": "Maintain a 7-day streak",
            "xpReward": 100,
            "badgeIcon": "🔥",
            "unlocked": True,
            "unlockedAt": (datetime.utcnow() - timedelta(days=2)).isoformat(),
        },
        {
            "id": "perfect_score",
            "name": "Perfectionist",
            "description": "Score 100% on an assessment",
            "xpReward": 150,
            "badgeIcon": "⭐",
            "unlocked": False,
            "progress": 0.8,
        },
        {
            "id": "helper",
            "name": "Team Player",
            "description": "Help 5 classmates",
            "xpReward": 75,
            "badgeIcon": "🤝",
            "unlocked": False,
            "progress": 0.6,
        },
    ]

    return achievements


@router.get("/badges")
async def get_badges(
    userId: str | None = Query(None, description="User ID to get badges for")
) -> list[dict]:
    """Get user's earned badges"""
    badges = [
        {
            "id": "badge_1",
            "name": "Quick Learner",
            "description": "Complete 5 lessons in one day",
            "icon": "⚡",
            "rarity": "common",
            "earnedAt": datetime.utcnow().isoformat(),
        },
        {
            "id": "badge_2",
            "name": "Math Master",
            "description": "Achieve level 10 in Mathematics",
            "icon": "🧮",
            "rarity": "rare",
            "earnedAt": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        },
        {
            "id": "badge_3",
            "name": "Explorer",
            "description": "Try all available subjects",
            "icon": "🗺️",
            "rarity": "epic",
            "earnedAt": (datetime.utcnow() - timedelta(days=10)).isoformat(),
        },
    ]

    return badges


@router.post("/xp/add")
async def add_xp(userId: str, amount: int, reason: str, source: str = "achievement") -> dict:
    """Add XP to a user's account"""
    # In production, this would update the database
    # For now, return a success response
    return {
        "success": True,
        "userId": userId,
        "xpAdded": amount,
        "newTotal": 2500 + amount,  # Mock total
        "newLevel": ((2500 + amount) // 500) + 1,
        "reason": reason,
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/stats/{userId}")
async def get_user_stats(userId: str) -> dict:
    """Get detailed gamification stats for a user"""
    return {
        "userId": userId,
        "totalXP": 2500,
        "currentLevel": 6,
        "xpToNextLevel": 500 - (2500 % 500),
        "rank": 15,
        "percentile": 85,
        "streakDays": 12,
        "longestStreak": 21,
        "totalBadges": 8,
        "totalAchievements": 12,
        "completedMissions": 45,
        "averageScore": 87.5,
        "subjectMastery": {"Mathematics": 85, "Science": 78, "English": 92, "History": 71},
        "recentActivity": [
            {
                "type": "lesson_completed",
                "description": "Completed 'Introduction to Algebra'",
                "xpEarned": 50,
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "type": "achievement_unlocked",
                "description": "Unlocked 'Week Warrior' achievement",
                "xpEarned": 100,
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            },
        ],
    }
