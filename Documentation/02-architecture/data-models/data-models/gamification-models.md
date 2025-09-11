# Gamification Models

This document defines the data models for gamification features including experience points, achievements, badges, leaderboards, and rewards within ToolBoxAI-Solutions.

## PlayerProfile Model

Represents a student's gamification profile with all game-related statistics and progress.

### Schema Definition

```lua
PlayerProfile = {
    -- Identification
    id = string,                     -- Profile ID (UUID)
    user_id = string,                -- References users.id

    -- Basic Info
    profile = {
        username = string,           -- Gaming username
        display_name = string,       -- Display name
        avatar = {
            type = string,          -- "default", "custom", "unlocked"
            url = string,           -- Avatar image URL
            frame_id = string,      -- Avatar frame ID
            effects = {string}      -- Applied effects
        },

        title = string,             -- Current title
        titles_earned = {string},   -- All earned titles

        bio = string,              -- Player bio

        status = string,           -- "online", "away", "offline", "playing"

        visibility = string        -- "public", "friends", "private"
    },

    -- Experience System
    experience = {
        current_xp = number,        -- Current XP points
        total_xp = number,         -- All-time XP earned

        level = number,            -- Current level

        level_progress = {
            current_level_xp = number,    -- XP in current level
            next_level_xp = number,       -- XP needed for next level
            progress_percentage = number   -- Progress to next level
        },

        prestige = {
            level = number,        -- Prestige level
            resets = number       -- Times prestiged
        },

        xp_multipliers = {         -- Active XP multipliers
            {
                source = string,   -- Source of multiplier
                value = number,    -- Multiplier value
                expires_at = DateTime
            }
        },

        xp_history = {            -- Recent XP gains
            {
                amount = number,
                source = string,
                timestamp = DateTime,
                multiplier = number
            }
        }
    },

    -- Points and Currency
    currency = {
        coins = number,           -- Standard currency
        gems = number,           -- Premium currency
        tokens = number,         -- Event currency

        lifetime_earned = {
            coins = number,
            gems = number,
            tokens = number
        },

        spending_history = {     -- Recent transactions
            {
                type = string,
                amount = number,
                item = string,
                timestamp = DateTime
            }
        }
    },

    -- Achievement System
    achievements = {
        total_earned = number,
        total_points = number,   -- Achievement points

        categories = {
            {
                category = string,
                earned = number,
                total = number,
                progress = number
            }
        },

        recent = {              -- Recent achievements
            {
                achievement_id = string,
                earned_at = DateTime,
                rarity = string
            }
        },

        showcase = {string}     -- Featured achievements
    },

    -- Badge Collection
    badges = {
        total_earned = number,

        rarity_counts = {
            common = number,
            uncommon = number,
            rare = number,
            epic = number,
            legendary = number
        },

        equipped = {string},    -- Currently equipped badges

        collections = {         -- Badge collections
            {
                collection_id = string,
                progress = number,
                completed = boolean
            }
        }
    },

    -- Statistics
    stats = {
        -- Learning Stats
        lessons_completed = number,
        quizzes_perfect = number,

        study_streak = {
            current = number,
            best = number,
            last_active = DateTime
        },

        total_study_time = number,  -- Minutes

        -- Performance Stats
        accuracy_rate = number,
        improvement_rate = number,
        mastery_score = number,

        -- Social Stats
        friends_count = number,

        helps_given = number,
        helps_received = number,

        challenges_won = number,
        challenges_total = number,

        -- Engagement Stats
        login_days = number,
        activities_completed = number,

        content_created = number,
        content_shared = number
    },

    -- Ranking
    ranking = {
        global_rank = number,

        school_rank = number,
        class_rank = number,

        percentile = number,        -- Global percentile

        league = string,           -- Current league/division
        league_points = number,    -- Points in current league

        season_rank = number,      -- Current season rank

        peak_rank = number,        -- Best rank achieved
        peak_date = DateTime
    },

    -- Inventory
    inventory = {
        items = {
            {
                item_id = string,
                quantity = number,
                acquired_at = DateTime,
                equipped = boolean,
                expires_at = DateTime
            }
        },

        power_ups = {
            {
                power_up_id = string,
                uses_remaining = number,
                active = boolean
            }
        },

        cosmetics = {
            avatars = {string},
            frames = {string},
            themes = {string},
            emotes = {string},
            effects = {string}
        },

        capacity = number,         -- Inventory slots
        used_slots = number
    },

    -- Quest Progress
    quests = {
        active = {
            {
                quest_id = string,
                progress = number,
                started_at = DateTime,
                expires_at = DateTime
            }
        },

        completed_today = number,
        completed_total = number,

        quest_points = number     -- Points from quests
    },

    -- Social Features
    social = {
        guild_id = string,        -- Guild/team membership
        guild_role = string,      -- Role in guild

        friends = {string},       -- Friend user IDs

        followers = number,
        following = number,

        reputation = number,      -- Social reputation score

        blocked = {string}       -- Blocked users
    },

    -- Timestamps
    created_at = DateTime,
    updated_at = DateTime,
    last_active = DateTime,

    -- Settings
    settings = {
        notifications = {
            achievements = boolean,
            level_up = boolean,
            friend_activity = boolean,
            challenges = boolean
        },

        privacy = {
            show_profile = boolean,
            show_stats = boolean,
            allow_challenges = boolean,
            allow_friend_requests = boolean
        }
    }
}
```

## Achievement Model

Defines achievements that players can earn.

### Schema Definition

```lua
Achievement = {
    -- Identification
    id = string,
    name = string,
    slug = string,

    -- Display
    display = {
        title = string,
        description = string,

        icon = {
            locked = string,         -- Icon when locked
            unlocked = string,       -- Icon when unlocked
            animated = string        -- Animated icon
        },

        banner = string,            -- Banner image

        flavor_text = string,       -- Flavor/lore text

        category = string,          -- Achievement category

        tags = {string}            -- Achievement tags
    },

    -- Requirements
    requirements = {
        type = string,             -- Requirement type
        -- Types: "counter", "threshold", "collection", "sequence",
        -- "time_limit", "perfect", "streak", "unique"

        conditions = {
            {
                metric = string,    -- Metric to track
                operator = string,  -- Comparison operator
                value = any,       -- Target value

                context = {        -- Additional context
                    subject = string,
                    difficulty = string,
                    time_frame = string
                }
            }
        },

        logic = string,            -- "all", "any", "sequence"

        prerequisite_achievements = {string},

        level_requirement = number,

        time_constraint = {
            type = string,         -- "within", "daily", "weekly"
            duration = number      -- Time in minutes
        }
    },

    -- Rewards
    rewards = {
        xp = number,              -- XP reward

        coins = number,           -- Coin reward
        gems = number,           -- Gem reward

        items = {                 -- Item rewards
            {
                item_id = string,
                quantity = number
            }
        },

        badges = {string},        -- Badge rewards

        titles = {string},        -- Title rewards

        unlock_content = {string}, -- Unlocked content

        multipliers = {           -- Multiplier rewards
            {
                type = string,
                value = number,
                duration = number
            }
        }
    },

    -- Progression
    progression = {
        type = string,            -- "instant", "progressive", "tiered"

        tiers = {                 -- For tiered achievements
            {
                tier = number,
                name = string,
                requirement = number,
                reward_multiplier = number
            }
        },

        milestones = {           -- Progress milestones
            {
                percentage = number,
                message = string,
                partial_reward = {}
            }
        },

        show_progress = boolean,  -- Show progress bar

        reset_on_prestige = boolean
    },

    -- Metadata
    metadata = {
        difficulty = string,      -- "easy", "medium", "hard", "expert"

        rarity = string,         -- "common", "uncommon", "rare", "epic", "legendary"

        points = number,         -- Achievement points

        estimated_time = number, -- Estimated hours to complete

        completion_rate = number, -- Global completion %

        secret = boolean,        -- Hidden achievement

        seasonal = boolean,      -- Seasonal achievement
        season = string,        -- Season identifier

        limited_time = boolean,  -- Time-limited
        available_from = DateTime,
        available_until = DateTime,

        stackable = boolean,     -- Can be earned multiple times

        platform_exclusive = string -- Platform exclusivity
    },

    -- Statistics
    statistics = {
        total_earned = number,    -- Times earned globally

        unique_earners = number,  -- Unique players earned

        average_time = number,   -- Average time to earn

        first_earned_by = string, -- First player to earn
        first_earned_at = DateTime,

        recent_earners = {       -- Recent earners
            {
                user_id = string,
                earned_at = DateTime
            }
        }
    },

    -- Status
    status = string,             -- "active", "retired", "upcoming"

    created_at = DateTime,
    updated_at = DateTime,

    created_by = string
}
```

## Badge Model

Collectible badges that represent accomplishments.

### Schema Definition

```lua
Badge = {
    id = string,
    name = string,

    -- Visual
    visual = {
        image = string,          -- Badge image
        thumbnail = string,      -- Thumbnail image

        animation = string,      -- Animation file

        shine_effect = boolean,  -- Shine effect

        rarity_color = string,   -- Rarity color code

        size = string,          -- "small", "medium", "large"

        style = string          -- Visual style
    },

    -- Information
    info = {
        title = string,
        description = string,

        lore = string,          -- Badge lore/story

        category = string,      -- Badge category

        collection = string,    -- Part of collection
        collection_position = number,

        tier = number,         -- Badge tier

        tags = {string}
    },

    -- Acquisition
    acquisition = {
        method = string,        -- How to obtain
        -- Methods: "achievement", "purchase", "event", "gift",
        -- "milestone", "collection", "challenge", "random"

        requirements = {
            achievement_id = string,

            level = number,

            quests = {string},

            items_needed = {
                {
                    item_id = string,
                    quantity = number
                }
            },

            cost = {
                coins = number,
                gems = number
            }
        },

        drop_rate = number,     -- Drop rate if random

        tradeable = boolean,    -- Can be traded

        limited = boolean,      -- Limited availability
        max_quantity = number   -- Max per player
    },

    -- Properties
    properties = {
        rarity = string,        -- Rarity level

        power = number,        -- Badge power/value

        bonuses = {            -- Stat bonuses when equipped
            {
                stat = string,
                value = number,
                type = string  -- "flat", "percentage"
            }
        },

        set_bonus = {          -- Bonus for complete set
            required_badges = {string},
            bonus = {}
        },

        stacks = boolean,      -- Effects stack

        evolution = {          -- Badge evolution
            next_badge_id = string,
            requirements = {}
        }
    },

    -- Statistics
    statistics = {
        total_awarded = number,
        unique_owners = number,

        equipped_count = number, -- Currently equipped

        trade_volume = number,  -- Times traded

        average_value = number  -- Market value
    },

    created_at = DateTime,
    updated_at = DateTime
}
```

## Leaderboard Model

Competitive rankings and leaderboards.

### Schema Definition

```lua
Leaderboard = {
    id = string,
    name = string,

    -- Configuration
    configuration = {
        type = string,          -- Leaderboard type
        -- Types: "points", "level", "achievement", "time",
        -- "accuracy", "streak", "collection", "composite"

        metric = string,        -- Metric being tracked

        scope = string,        -- "global", "regional", "school", "class", "friends"

        period = string,       -- "all-time", "seasonal", "monthly", "weekly", "daily"

        reset_schedule = {
            frequency = string, -- Reset frequency
            next_reset = DateTime,

            archive_previous = boolean
        },

        calculation = {
            formula = string,   -- Calculation formula

            weights = {        -- Metric weights
                {
                    metric = string,
                    weight = number
                }
            },

            aggregation = string, -- "sum", "average", "max", "latest"

            tie_breaker = string -- Tie-breaking metric
        },

        filters = {            -- Entry filters
            min_level = number,
            min_activities = number,

            required_achievements = {string},

            exclude_inactive_days = number
        },

        size_limits = {
            max_entries = number,

            display_top = number,

            show_nearby = number -- Show nearby ranks
        }
    },

    -- Entries
    entries = {
        {
            rank = number,

            user_id = string,
            display_name = string,
            avatar_url = string,

            score = number,

            score_details = {   -- Score breakdown
                -- Detailed metrics
            },

            movement = string,  -- "up", "down", "same", "new"
            previous_rank = number,

            streak = number,   -- Current streak

            badges = {string}, -- Display badges

            last_update = DateTime,

            highlight = boolean -- Special highlight
        }
    },

    -- Rewards
    rewards = {
        enabled = boolean,

        distribution = {       -- Reward tiers
            {
                rank_range = {
                    min = number,
                    max = number
                },

                percentage_range = {
                    min = number,
                    max = number
                },

                rewards = {
                    xp = number,
                    coins = number,
                    badges = {string},
                    items = {
                        {
                            item_id = string,
                            quantity = number
                        }
                    }
                }
            }
        },

        participation = {      -- Participation rewards
            minimum_score = number,
            reward = {}
        },

        milestones = {        -- Rank milestones
            {
                rank = number,
                reward = {},
                title = string
            }
        }
    },

    -- Seasons
    seasons = {
        current_season = {
            id = string,
            name = string,

            started_at = DateTime,
            ends_at = DateTime,

            theme = string,

            special_rules = {}
        },

        previous_seasons = {   -- Archived seasons
            {
                id = string,
                winner_id = string,
                top_players = {string},

                archived_at = DateTime
            }
        }
    },

    -- Display
    display = {
        icon = string,
        banner = string,

        color_scheme = {
            primary = string,
            secondary = string,
            accent = string
        },

        show_avatars = boolean,
        show_badges = boolean,
        show_stats = boolean,

        animations = {
            rank_change = boolean,
            new_entry = boolean,
            milestone = boolean
        },

        update_frequency = number -- Seconds
    },

    -- Statistics
    statistics = {
        total_participants = number,

        active_participants = number,

        average_score = number,
        median_score = number,

        top_score = number,
        top_scorer = string,

        competition_index = number, -- Competitiveness

        churn_rate = number,      -- Player churn

        update_count = number,
        last_updated = DateTime
    },

    -- Metadata
    status = string,              -- "active", "paused", "ended"

    visibility = string,          -- "public", "private", "unlisted"

    created_at = DateTime,
    updated_at = DateTime,

    tags = {string}
}
```

## Quest Model

Defines quests and challenges for players.

### Schema Definition

```lua
Quest = {
    id = string,
    name = string,

    -- Quest Information
    info = {
        title = string,
        description = string,

        story = string,          -- Quest narrative

        category = string,       -- Quest category

        difficulty = string,     -- Difficulty level

        type = string,          -- Quest type
        -- Types: "main", "side", "daily", "weekly", "event",
        -- "tutorial", "challenge", "hidden"

        icon = string,
        banner = string,

        npc = {                 -- Quest giver NPC
            name = string,
            avatar = string,
            dialogue = {string}
        }
    },

    -- Objectives
    objectives = {
        {
            id = string,

            description = string,

            type = string,      -- Objective type
            -- Types: "complete", "collect", "achieve", "reach",
            -- "interact", "time_limit", "perfect", "sequence"

            target = {
                metric = string,
                value = number,

                context = {}   -- Additional requirements
            },

            progress_tracking = {
                current = number,
                required = number,

                show_progress = boolean,

                checkpoints = { -- Progress checkpoints
                    {
                        value = number,
                        reward = {}
                    }
                }
            },

            optional = boolean,

            order = number,    -- Order in sequence

            unlocks = {string} -- Unlocked objectives
        }
    },

    -- Requirements
    requirements = {
        level = number,

        quests_completed = {string},

        achievements = {string},

        items = {
            {
                item_id = string,
                quantity = number,
                consume = boolean
            }
        },

        skills = {
            {
                skill = string,
                level = number
            }
        },

        time_window = {
            available_from = DateTime,
            available_until = DateTime,

            daily_reset = boolean,
            weekly_reset = boolean
        }
    },

    -- Rewards
    rewards = {
        guaranteed = {          -- Guaranteed rewards
            xp = number,
            coins = number,
            items = {
                {
                    item_id = string,
                    quantity = number
                }
            },

            badges = {string},
            achievements = {string},

            unlock_content = {string},
            unlock_quests = {string}
        },

        random = {             -- Random rewards
            {
                probability = number,
                reward = {}
            }
        },

        bonus = {              -- Bonus objectives
            {
                condition = string,
                reward = {}
            }
        },

        first_completion = {   -- First-time rewards
            -- Special first-time rewards
        },

        repeatable = boolean,

        repeat_rewards = {}   -- Rewards for repeats
    },

    -- Chain
    chain = {
        is_chain = boolean,

        chain_id = string,

        position = number,

        next_quest = string,

        branch_quests = {     -- Branching paths
            {
                condition = string,
                quest_id = string
            }
        }
    },

    -- Statistics
    statistics = {
        attempts = number,
        completions = number,

        success_rate = number,

        average_time = number,

        abandonment_rate = number,

        rating = {
            average = number,
            count = number
        }
    },

    -- Metadata
    active = boolean,

    priority = number,        -- Display priority

    created_at = DateTime,
    updated_at = DateTime,

    expires_at = DateTime,

    tags = {string}
}
```

## Reward Model

Defines rewards that can be earned or purchased.

### Schema Definition

```lua
Reward = {
    id = string,
    name = string,

    -- Reward Type
    type = string,           -- Reward type
    -- Types: "item", "currency", "xp", "badge", "title",
    -- "cosmetic", "power_up", "unlock", "multiplier"

    -- Display
    display = {
        title = string,
        description = string,

        icon = string,
        image = string,

        rarity = string,

        preview = string,    -- Preview animation/image

        effects = {         -- Visual effects
            particle = string,
            sound = string,
            animation = string
        }
    },

    -- Value
    value = {
        amount = number,     -- Quantity/amount

        duration = number,   -- Duration if temporary

        uses = number,      -- Number of uses

        stacks = boolean,   -- Can stack
        max_stack = number,

        properties = {}     -- Type-specific properties
    },

    -- Acquisition
    acquisition = {
        sources = {         -- How to obtain
            {
                type = string,
                id = string,
                probability = number
            }
        },

        purchasable = boolean,

        price = {
            coins = number,
            gems = number,
            tokens = number
        },

        tradeable = boolean,

        giftable = boolean,

        limited = {
            quantity = number,
            per_player = number,

            time_limited = boolean,
            available_until = DateTime
        }
    },

    -- Usage
    usage = {
        consumable = boolean,

        requirements = {
            level = number,
            achievements = {string}
        },

        cooldown = number,   -- Cooldown in seconds

        context = {         -- Where can be used
            environments = {string},
            activities = {string}
        },

        effects = {         -- Effects when used
            -- Effect definitions
        }
    },

    -- Statistics
    statistics = {
        distributed = number, -- Total distributed

        used = number,       -- Total used

        active = number,     -- Currently active

        average_hold_time = number,

        popularity = number  -- Popularity score
    },

    created_at = DateTime,
    updated_at = DateTime
}
```

## Implementation Notes

### XP Calculation System

```python
class XPCalculator:
    def calculate_xp(self, activity: str, performance: dict) -> int:
        base_xp = self.get_base_xp(activity)

        # Performance multipliers
        multipliers = []

        if performance['perfect']:
            multipliers.append(1.5)

        if performance['time'] < performance['expected_time'] * 0.5:
            multipliers.append(1.2)

        if performance['first_try']:
            multipliers.append(1.1)

        # Streak bonus
        streak_multiplier = 1 + (performance['streak'] * 0.05)
        multipliers.append(min(streak_multiplier, 2.0))

        # Apply multipliers
        total_multiplier = sum(multipliers) / len(multipliers) if multipliers else 1

        # Apply active boosts
        boost_multiplier = self.get_active_boosts(performance['user_id'])

        final_xp = int(base_xp * total_multiplier * boost_multiplier)

        return final_xp
```

### Level Progression Formula

```lua
LevelProgression = {
    formula = "exponential",

    base_xp = 100,           -- XP for level 1->2

    growth_rate = 1.5,       -- Exponential growth

    calculate_level_xp = function(level)
        return math.floor(base_xp * math.pow(growth_rate, level - 1))
    end,

    level_caps = {
        soft_cap = 50,       -- Slower progression after
        hard_cap = 100,      -- Maximum level

        prestige_enabled = true,
        prestige_benefits = {
            xp_boost = 0.1,  -- 10% XP boost per prestige
            exclusive_rewards = true
        }
    }
}
```

### Achievement Tracking

```python
class AchievementTracker:
    async def track_progress(self, user_id: str, metric: str, value: Any):
        # Get active achievements for metric
        achievements = await self.get_tracking_achievements(metric)

        for achievement in achievements:
            # Update progress
            progress = await self.update_achievement_progress(
                user_id, achievement.id, metric, value
            )

            # Check completion
            if self.check_completion(achievement, progress):
                await self.award_achievement(user_id, achievement)

                # Trigger notification
                await self.notify_achievement(user_id, achievement)

                # Check chain achievements
                await self.check_chain_achievements(user_id, achievement)
```

### Leaderboard Updates

```python
class LeaderboardManager:
    async def update_leaderboard(self, leaderboard_id: str, user_id: str, score: int):
        # Get current leaderboard
        leaderboard = await self.get_leaderboard(leaderboard_id)

        # Calculate new position
        new_rank = self.calculate_rank(leaderboard, score)

        # Update with optimistic locking
        async with self.redis.pipeline() as pipe:
            # Remove old entry
            pipe.zrem(f"lb:{leaderboard_id}", user_id)

            # Add new entry
            pipe.zadd(f"lb:{leaderboard_id}", {user_id: score})

            # Update metadata
            pipe.hset(f"lb:{leaderboard_id}:meta", user_id, json.dumps({
                'score': score,
                'rank': new_rank,
                'updated': datetime.utcnow().isoformat()
            }))

            await pipe.execute()

        # Trigger rank change events
        await self.process_rank_changes(leaderboard_id, user_id, new_rank)
```

### Quest System

```lua
QuestManager = {
    assign_quest = function(user_id, quest_id)
        -- Check requirements
        if not check_requirements(user_id, quest_id) then
            return false
        end

        -- Create quest instance
        instance = {
            user_id = user_id,
            quest_id = quest_id,
            started_at = os.time(),
            objectives = initialize_objectives(quest_id),
            status = "active"
        }

        -- Save and start tracking
        save_quest_instance(instance)
        start_objective_tracking(instance)

        return instance
    end,

    update_objective = function(instance_id, objective_id, progress)
        -- Update progress
        objective = get_objective(instance_id, objective_id)
        objective.current = progress

        -- Check completion
        if objective.current >= objective.required then
            complete_objective(instance_id, objective_id)

            -- Check quest completion
            if all_required_objectives_complete(instance_id) then
                complete_quest(instance_id)
            end
        end
    end
}
```

---

_For user profiles, see [User Models](user-models.md). For learning progress, see [Progress Models](progress-models.md). For analytics on gamification, see [Analytics Models](analytics-models.md)._
