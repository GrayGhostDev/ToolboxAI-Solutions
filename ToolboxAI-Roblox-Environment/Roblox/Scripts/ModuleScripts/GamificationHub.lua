--[[
    GamificationHub.lua - Comprehensive gamification system for ToolboxAI Platform
    
    Features:
    - Point and currency systems
    - Achievement definitions and unlocking
    - Badge management and display
    - Leaderboards and rankings
    - Rewards distribution
    - Progress tracking and milestones
    - Streak systems and daily challenges
    - Experience and leveling
]]

local GamificationHub = {}
GamificationHub.__index = GamificationHub

-- Services
local Players = game:GetService("Players")
local BadgeService = game:GetService("BadgeService")
local MarketplaceService = game:GetService("MarketplaceService")
local DataStoreService = game:GetService("DataStoreService")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Configuration
local CONFIG = {
    -- Point System
    POINTS_PER_CORRECT_ANSWER = 10,
    POINTS_PER_QUIZ_COMPLETION = 50,
    POINTS_PER_LESSON_COMPLETION = 100,
    POINTS_PER_ACHIEVEMENT = 25,
    POINTS_PER_STREAK_DAY = 15,
    
    -- Currency System
    COINS_PER_LEVEL = 100,
    GEMS_PER_ACHIEVEMENT = 5,
    GEMS_PER_PERFECT_QUIZ = 10,
    
    -- Experience System
    BASE_XP_PER_LEVEL = 100,
    XP_MULTIPLIER = 1.5,
    MAX_LEVEL = 100,
    
    -- Streak System
    STREAK_RESET_HOURS = 48,
    STREAK_BONUS_MULTIPLIER = 1.1,
    
    -- Leaderboard
    LEADERBOARD_SIZE = 100,
    LEADERBOARD_UPDATE_INTERVAL = 60, -- seconds
    
    -- Daily Challenges
    MAX_DAILY_CHALLENGES = 3,
    DAILY_RESET_HOUR = 0, -- Midnight UTC
}

-- Achievement Definitions
local ACHIEVEMENTS = {
    -- Learning Achievements
    first_steps = {
        id = "first_steps",
        name = "First Steps",
        description = "Complete your first lesson",
        icon = "rbxassetid://1234567890",
        points = 10,
        gems = 1,
        requirements = {
            type = "lessons_completed",
            count = 1
        }
    },
    
    quick_learner = {
        id = "quick_learner",
        name = "Quick Learner",
        description = "Complete 5 lessons",
        icon = "rbxassetid://1234567891",
        points = 25,
        gems = 3,
        requirements = {
            type = "lessons_completed",
            count = 5
        }
    },
    
    scholar = {
        id = "scholar",
        name = "Scholar",
        description = "Complete 25 lessons",
        icon = "rbxassetid://1234567892",
        points = 100,
        gems = 10,
        requirements = {
            type = "lessons_completed",
            count = 25
        }
    },
    
    -- Quiz Achievements
    quiz_novice = {
        id = "quiz_novice",
        name = "Quiz Novice",
        description = "Complete your first quiz",
        icon = "rbxassetid://1234567893",
        points = 15,
        gems = 2,
        requirements = {
            type = "quizzes_completed",
            count = 1
        }
    },
    
    perfect_score = {
        id = "perfect_score",
        name = "Perfect Score",
        description = "Get 100% on a quiz",
        icon = "rbxassetid://1234567894",
        points = 50,
        gems = 10,
        requirements = {
            type = "perfect_quiz",
            count = 1
        }
    },
    
    quiz_master = {
        id = "quiz_master",
        name = "Quiz Master",
        description = "Complete 50 quizzes",
        icon = "rbxassetid://1234567895",
        points = 200,
        gems = 25,
        requirements = {
            type = "quizzes_completed",
            count = 50
        }
    },
    
    -- Streak Achievements
    consistent = {
        id = "consistent",
        name = "Consistent",
        description = "Maintain a 3-day streak",
        icon = "rbxassetid://1234567896",
        points = 30,
        gems = 5,
        requirements = {
            type = "streak_days",
            count = 3
        }
    },
    
    dedicated = {
        id = "dedicated",
        name = "Dedicated",
        description = "Maintain a 7-day streak",
        icon = "rbxassetid://1234567897",
        points = 75,
        gems = 15,
        requirements = {
            type = "streak_days",
            count = 7
        }
    },
    
    unstoppable = {
        id = "unstoppable",
        name = "Unstoppable",
        description = "Maintain a 30-day streak",
        icon = "rbxassetid://1234567898",
        points = 300,
        gems = 50,
        badgeId = 123456789, -- Roblox Badge ID
        requirements = {
            type = "streak_days",
            count = 30
        }
    },
    
    -- Exploration Achievements
    explorer = {
        id = "explorer",
        name = "Explorer",
        description = "Visit 10 different learning environments",
        icon = "rbxassetid://1234567899",
        points = 40,
        gems = 8,
        requirements = {
            type = "environments_visited",
            count = 10
        }
    },
    
    -- Social Achievements
    team_player = {
        id = "team_player",
        name = "Team Player",
        description = "Complete a team challenge",
        icon = "rbxassetid://1234567900",
        points = 35,
        gems = 7,
        requirements = {
            type = "team_challenges",
            count = 1
        }
    },
    
    -- Time-based Achievements
    early_bird = {
        id = "early_bird",
        name = "Early Bird",
        description = "Play before 9 AM",
        icon = "rbxassetid://1234567901",
        points = 20,
        gems = 4,
        requirements = {
            type = "time_based",
            condition = "morning"
        }
    },
    
    night_owl = {
        id = "night_owl",
        name = "Night Owl",
        description = "Play after 9 PM",
        icon = "rbxassetid://1234567902",
        points = 20,
        gems = 4,
        requirements = {
            type = "time_based",
            condition = "night"
        }
    }
}

-- Badge IDs (Roblox badges)
local BADGE_IDS = {
    welcome = 123456789,
    first_achievement = 123456790,
    level_10 = 123456791,
    level_25 = 123456792,
    level_50 = 123456793,
    level_100 = 123456794,
    streak_master = 123456795,
    quiz_champion = 123456796,
}

-- Daily Challenge Templates
local DAILY_CHALLENGES = {
    {
        id = "daily_quiz",
        name = "Quiz of the Day",
        description = "Complete any quiz",
        reward = {points = 50, coins = 25},
        requirements = {type = "complete_quiz", count = 1}
    },
    {
        id = "perfect_day",
        name = "Perfect Day",
        description = "Get 100% on a quiz",
        reward = {points = 100, gems = 5},
        requirements = {type = "perfect_quiz", count = 1}
    },
    {
        id = "exploration",
        name = "Explorer",
        description = "Visit 3 different areas",
        reward = {points = 75, coins = 50},
        requirements = {type = "areas_visited", count = 3}
    },
    {
        id = "social_butterfly",
        name = "Social Butterfly",
        description = "Play with 2 other players",
        reward = {points = 60, coins = 30},
        requirements = {type = "play_with_others", count = 2}
    },
    {
        id = "quick_study",
        name = "Quick Study",
        description = "Complete 3 lessons",
        reward = {points = 150, gems = 3},
        requirements = {type = "lessons_completed", count = 3}
    }
}

-- Constructor
function GamificationHub.new()
    local self = setmetatable({}, GamificationHub)
    
    -- Player progress tracking
    self.playerProgress = {}
    
    -- Leaderboard cache
    self.leaderboardCache = {
        points = {},
        streak = {},
        level = {},
        lastUpdate = 0
    }
    
    -- Daily challenges
    self.todaysChallenges = {}
    self.playerChallengeProgress = {}
    
    -- Initialize systems
    self:Initialize()
    
    return self
end

-- Initialize gamification systems
function GamificationHub:Initialize()
    -- Set up RemoteEvents
    self:SetupRemoteEvents()
    
    -- Generate today's challenges
    self:GenerateDailyChallenges()
    
    -- Start leaderboard update cycle
    self:StartLeaderboardUpdates()
    
    -- Set up daily reset
    self:SetupDailyReset()
    
    print("[GamificationHub] Initialized successfully")
end

-- Set up RemoteEvents for client communication
function GamificationHub:SetupRemoteEvents()
    local remotes = ReplicatedStorage:FindFirstChild("Remotes")
    if not remotes then
        remotes = Instance.new("Folder")
        remotes.Name = "Remotes"
        remotes.Parent = ReplicatedStorage
    end
    
    -- Achievement event
    local achievementEvent = Instance.new("RemoteEvent")
    achievementEvent.Name = "AchievementEvent"
    achievementEvent.Parent = remotes
    
    -- Progress event
    local progressEvent = Instance.new("RemoteEvent")
    progressEvent.Name = "GamificationProgressEvent"
    progressEvent.Parent = remotes
    
    -- Leaderboard function
    local leaderboardFunction = Instance.new("RemoteFunction")
    leaderboardFunction.Name = "GetLeaderboardFunction"
    leaderboardFunction.Parent = remotes
    
    -- Challenge event
    local challengeEvent = Instance.new("RemoteEvent")
    challengeEvent.Name = "DailyChallengeEvent"
    challengeEvent.Parent = remotes
    
    -- Connect handlers
    leaderboardFunction.OnServerInvoke = function(player, leaderboardType)
        return self:GetLeaderboard(leaderboardType)
    end
end

-- Initialize player progress
function GamificationHub:InitializePlayer(player, existingData)
    local progress = existingData or {
        -- Points and currency
        points = 0,
        coins = 0,
        gems = 0,
        
        -- Experience and level
        level = 1,
        experience = 0,
        totalExperience = 0,
        
        -- Achievements
        achievements = {},
        achievementProgress = {},
        
        -- Badges (Roblox badges)
        badges = {},
        
        -- Streaks
        currentStreak = 0,
        bestStreak = 0,
        lastPlayDate = os.date("!*t"),
        
        -- Statistics
        stats = {
            lessonsCompleted = 0,
            quizzesCompleted = 0,
            perfectQuizzes = 0,
            questionsAnswered = 0,
            correctAnswers = 0,
            environmentsVisited = {},
            totalPlayTime = 0,
            teamChallenges = 0
        },
        
        -- Daily challenges
        dailyChallenges = {},
        lastChallengeReset = os.date("!*t")
    }
    
    self.playerProgress[player.UserId] = progress
    
    -- Check for streak continuation
    self:UpdateStreak(player)
    
    -- Check for pending achievements
    self:CheckAllAchievements(player)
    
    -- Send initial data to player
    self:SendProgressUpdate(player)
    
    return progress
end

-- Award points to player
function GamificationHub:AwardPoints(player, amount, reason)
    local progress = self.playerProgress[player.UserId]
    if not progress then return end
    
    -- Apply streak bonus if applicable
    if progress.currentStreak > 0 then
        amount = math.floor(amount * (1 + (progress.currentStreak * 0.01)))
    end
    
    progress.points = progress.points + amount
    
    -- Check for level up
    self:CheckLevelUp(player, progress)
    
    -- Update leaderboard
    self:UpdatePlayerLeaderboardScore(player, "points", progress.points)
    
    -- Send update to player
    self:SendProgressUpdate(player, {
        type = "points_awarded",
        amount = amount,
        reason = reason,
        total = progress.points
    })
    
    print(string.format("[GamificationHub] Awarded %d points to %s for %s", amount, player.Name, reason))
end

-- Award currency to player
function GamificationHub:AwardCurrency(player, currencyType, amount)
    local progress = self.playerProgress[player.UserId]
    if not progress then return end
    
    if currencyType == "coins" then
        progress.coins = progress.coins + amount
    elseif currencyType == "gems" then
        progress.gems = progress.gems + amount
    else
        return
    end
    
    self:SendProgressUpdate(player, {
        type = "currency_awarded",
        currencyType = currencyType,
        amount = amount,
        total = progress[currencyType]
    })
end

-- Award experience to player
function GamificationHub:AwardExperience(player, amount)
    local progress = self.playerProgress[player.UserId]
    if not progress then return end
    
    progress.experience = progress.experience + amount
    progress.totalExperience = progress.totalExperience + amount
    
    -- Check for level up
    while progress.experience >= self:GetExperienceForLevel(progress.level + 1) do
        progress.experience = progress.experience - self:GetExperienceForLevel(progress.level + 1)
        progress.level = progress.level + 1
        
        -- Level up rewards
        self:OnLevelUp(player, progress.level)
    end
    
    self:SendProgressUpdate(player, {
        type = "experience_gained",
        amount = amount,
        level = progress.level,
        experience = progress.experience,
        nextLevelExp = self:GetExperienceForLevel(progress.level + 1)
    })
end

-- Calculate experience required for a level
function GamificationHub:GetExperienceForLevel(level)
    return math.floor(CONFIG.BASE_XP_PER_LEVEL * math.pow(CONFIG.XP_MULTIPLIER, level - 1))
end

-- Handle level up
function GamificationHub:OnLevelUp(player, newLevel)
    -- Award level up rewards
    self:AwardCurrency(player, "coins", CONFIG.COINS_PER_LEVEL)
    
    -- Check for level milestone badges
    if BADGE_IDS["level_" .. newLevel] then
        self:AwardBadge(player, BADGE_IDS["level_" .. newLevel])
    end
    
    -- Special rewards for milestone levels
    local milestoneRewards = {
        [10] = {gems = 10, title = "Apprentice"},
        [25] = {gems = 25, title = "Scholar"},
        [50] = {gems = 50, title = "Expert"},
        [75] = {gems = 75, title = "Master"},
        [100] = {gems = 100, title = "Grandmaster"}
    }
    
    if milestoneRewards[newLevel] then
        local reward = milestoneRewards[newLevel]
        if reward.gems then
            self:AwardCurrency(player, "gems", reward.gems)
        end
        if reward.title then
            self:UnlockTitle(player, reward.title)
        end
    end
    
    -- Update leaderboard
    self:UpdatePlayerLeaderboardScore(player, "level", newLevel)
    
    -- Announce level up
    self:AnnounceLevelUp(player, newLevel)
end

-- Check and unlock achievements
function GamificationHub:CheckAchievement(player, achievementId)
    local achievement = ACHIEVEMENTS[achievementId]
    if not achievement then return false end
    
    local progress = self.playerProgress[player.UserId]
    if not progress then return false end
    
    -- Check if already unlocked
    if progress.achievements[achievementId] then
        return false
    end
    
    -- Check requirements
    local requirementMet = false
    local req = achievement.requirements
    
    if req.type == "lessons_completed" then
        requirementMet = progress.stats.lessonsCompleted >= req.count
        
    elseif req.type == "quizzes_completed" then
        requirementMet = progress.stats.quizzesCompleted >= req.count
        
    elseif req.type == "perfect_quiz" then
        requirementMet = progress.stats.perfectQuizzes >= req.count
        
    elseif req.type == "streak_days" then
        requirementMet = progress.currentStreak >= req.count or progress.bestStreak >= req.count
        
    elseif req.type == "environments_visited" then
        local visitCount = 0
        for _ in pairs(progress.stats.environmentsVisited) do
            visitCount = visitCount + 1
        end
        requirementMet = visitCount >= req.count
        
    elseif req.type == "team_challenges" then
        requirementMet = progress.stats.teamChallenges >= req.count
        
    elseif req.type == "time_based" then
        local hour = os.date("!*t").hour
        if req.condition == "morning" then
            requirementMet = hour < 9
        elseif req.condition == "night" then
            requirementMet = hour >= 21
        end
    end
    
    if requirementMet then
        self:UnlockAchievement(player, achievementId)
        return true
    end
    
    return false
end

-- Check all achievements for a player
function GamificationHub:CheckAllAchievements(player)
    for achievementId, _ in pairs(ACHIEVEMENTS) do
        self:CheckAchievement(player, achievementId)
    end
end

-- Unlock an achievement
function GamificationHub:UnlockAchievement(player, achievementId)
    local achievement = ACHIEVEMENTS[achievementId]
    if not achievement then return end
    
    local progress = self.playerProgress[player.UserId]
    if not progress then return end
    
    -- Mark as unlocked
    progress.achievements[achievementId] = {
        unlockedAt = os.time(),
        name = achievement.name
    }
    
    -- Award rewards
    if achievement.points then
        self:AwardPoints(player, achievement.points, "Achievement: " .. achievement.name)
    end
    
    if achievement.gems then
        self:AwardCurrency(player, "gems", achievement.gems)
    end
    
    -- Award Roblox badge if specified
    if achievement.badgeId then
        self:AwardBadge(player, achievement.badgeId)
    end
    
    -- Send achievement notification
    self:SendAchievementNotification(player, achievement)
    
    print(string.format("[GamificationHub] %s unlocked achievement: %s", player.Name, achievement.name))
end

-- Award Roblox badge
function GamificationHub:AwardBadge(player, badgeId)
    local success, hasBadge = pcall(function()
        return BadgeService:UserHasBadgeAsync(player.UserId, badgeId)
    end)
    
    if success and not hasBadge then
        pcall(function()
            BadgeService:AwardBadge(player.UserId, badgeId)
        end)
    end
end

-- Update player streak
function GamificationHub:UpdateStreak(player)
    local progress = self.playerProgress[player.UserId]
    if not progress then return end
    
    local currentDate = os.date("!*t")
    local lastPlayDate = progress.lastPlayDate
    
    -- Calculate days since last play
    local daysDiff = self:CalculateDaysDifference(lastPlayDate, currentDate)
    
    if daysDiff == 0 then
        -- Same day, no change
        return
    elseif daysDiff == 1 then
        -- Next day, increment streak
        progress.currentStreak = progress.currentStreak + 1
        
        -- Update best streak
        if progress.currentStreak > progress.bestStreak then
            progress.bestStreak = progress.currentStreak
        end
        
        -- Award streak points
        self:AwardPoints(player, CONFIG.POINTS_PER_STREAK_DAY * progress.currentStreak, "Daily Streak")
        
        -- Check streak achievements
        self:CheckAchievement(player, "consistent")
        self:CheckAchievement(player, "dedicated")
        self:CheckAchievement(player, "unstoppable")
        
    elseif daysDiff > CONFIG.STREAK_RESET_HOURS / 24 then
        -- Streak broken
        if progress.currentStreak > 0 then
            self:SendProgressUpdate(player, {
                type = "streak_broken",
                previousStreak = progress.currentStreak
            })
        end
        progress.currentStreak = 1
    end
    
    progress.lastPlayDate = currentDate
    
    -- Update leaderboard
    self:UpdatePlayerLeaderboardScore(player, "streak", progress.currentStreak)
end

-- Calculate days difference between two dates
function GamificationHub:CalculateDaysDifference(date1, date2)
    local time1 = os.time(date1)
    local time2 = os.time(date2)
    local diff = time2 - time1
    return math.floor(diff / 86400) -- 86400 seconds in a day
end

-- Generate daily challenges
function GamificationHub:GenerateDailyChallenges()
    self.todaysChallenges = {}
    
    -- Randomly select challenges
    local availableChallenges = {}
    for _, challenge in ipairs(DAILY_CHALLENGES) do
        table.insert(availableChallenges, challenge)
    end
    
    for i = 1, math.min(CONFIG.MAX_DAILY_CHALLENGES, #availableChallenges) do
        local index = math.random(1, #availableChallenges)
        local challenge = availableChallenges[index]
        table.insert(self.todaysChallenges, challenge)
        table.remove(availableChallenges, index)
    end
    
    print("[GamificationHub] Generated", #self.todaysChallenges, "daily challenges")
end

-- Update daily challenge progress
function GamificationHub:UpdateChallengeProgress(player, challengeType, amount)
    local progress = self.playerProgress[player.UserId]
    if not progress then return end
    
    -- Initialize challenge progress if needed
    if not self.playerChallengeProgress[player.UserId] then
        self.playerChallengeProgress[player.UserId] = {}
    end
    
    local playerChallenges = self.playerChallengeProgress[player.UserId]
    
    for _, challenge in ipairs(self.todaysChallenges) do
        if challenge.requirements.type == challengeType then
            if not playerChallenges[challenge.id] then
                playerChallenges[challenge.id] = {
                    progress = 0,
                    completed = false
                }
            end
            
            local challengeProgress = playerChallenges[challenge.id]
            
            if not challengeProgress.completed then
                challengeProgress.progress = challengeProgress.progress + amount
                
                if challengeProgress.progress >= challenge.requirements.count then
                    challengeProgress.completed = true
                    self:CompleteDailyChallenge(player, challenge)
                end
            end
        end
    end
end

-- Complete a daily challenge
function GamificationHub:CompleteDailyChallenge(player, challenge)
    -- Award rewards
    if challenge.reward.points then
        self:AwardPoints(player, challenge.reward.points, "Daily Challenge: " .. challenge.name)
    end
    
    if challenge.reward.coins then
        self:AwardCurrency(player, "coins", challenge.reward.coins)
    end
    
    if challenge.reward.gems then
        self:AwardCurrency(player, "gems", challenge.reward.gems)
    end
    
    -- Send notification
    self:SendChallengeComplete(player, challenge)
end

-- Get leaderboard data
function GamificationHub:GetLeaderboard(leaderboardType)
    local currentTime = tick()
    
    -- Check if cache is still valid
    if currentTime - self.leaderboardCache.lastUpdate < CONFIG.LEADERBOARD_UPDATE_INTERVAL then
        return self.leaderboardCache[leaderboardType] or {}
    end
    
    -- Update cache
    self:UpdateLeaderboardCache()
    
    return self.leaderboardCache[leaderboardType] or {}
end

-- Update leaderboard cache
function GamificationHub:UpdateLeaderboardCache()
    local leaderboards = {
        points = {},
        streak = {},
        level = {}
    }
    
    -- Collect all player data
    for userId, progress in pairs(self.playerProgress) do
        local player = Players:GetPlayerByUserId(userId)
        if player then
            table.insert(leaderboards.points, {
                userId = userId,
                name = player.Name,
                value = progress.points
            })
            
            table.insert(leaderboards.streak, {
                userId = userId,
                name = player.Name,
                value = progress.currentStreak
            })
            
            table.insert(leaderboards.level, {
                userId = userId,
                name = player.Name,
                value = progress.level
            })
        end
    end
    
    -- Sort leaderboards
    for leaderboardType, data in pairs(leaderboards) do
        table.sort(data, function(a, b)
            return a.value > b.value
        end)
        
        -- Limit to top players
        local limited = {}
        for i = 1, math.min(CONFIG.LEADERBOARD_SIZE, #data) do
            limited[i] = data[i]
            limited[i].rank = i
        end
        
        self.leaderboardCache[leaderboardType] = limited
    end
    
    self.leaderboardCache.lastUpdate = tick()
end

-- Update player's leaderboard score
function GamificationHub:UpdatePlayerLeaderboardScore(player, leaderboardType, score)
    -- This would typically update a DataStore for persistent leaderboards
    -- For now, just trigger a cache update on next request
    self.leaderboardCache.lastUpdate = 0
end

-- Start leaderboard update cycle
function GamificationHub:StartLeaderboardUpdates()
    spawn(function()
        while true do
            wait(CONFIG.LEADERBOARD_UPDATE_INTERVAL)
            self:UpdateLeaderboardCache()
        end
    end)
end

-- Set up daily reset
function GamificationHub:SetupDailyReset()
    spawn(function()
        while true do
            -- Calculate time until next reset
            local currentTime = os.date("!*t")
            local resetTime = os.time({
                year = currentTime.year,
                month = currentTime.month,
                day = currentTime.day + 1,
                hour = CONFIG.DAILY_RESET_HOUR,
                min = 0,
                sec = 0
            })
            
            local timeUntilReset = resetTime - os.time()
            
            wait(timeUntilReset)
            
            -- Perform daily reset
            self:PerformDailyReset()
        end
    end)
end

-- Perform daily reset
function GamificationHub:PerformDailyReset()
    print("[GamificationHub] Performing daily reset")
    
    -- Generate new challenges
    self:GenerateDailyChallenges()
    
    -- Reset player challenge progress
    self.playerChallengeProgress = {}
    
    -- Notify all players
    for _, player in ipairs(Players:GetPlayers()) do
        self:SendDailyReset(player)
    end
end

-- Send progress update to player
function GamificationHub:SendProgressUpdate(player, updateData)
    local remotes = ReplicatedStorage:WaitForChild("Remotes")
    local progressEvent = remotes:WaitForChild("GamificationProgressEvent")
    
    local progress = self.playerProgress[player.UserId]
    if not progress then return end
    
    progressEvent:FireClient(player, "progress_update", {
        progress = progress,
        update = updateData,
        timestamp = tick()
    })
end

-- Send achievement notification
function GamificationHub:SendAchievementNotification(player, achievement)
    local remotes = ReplicatedStorage:WaitForChild("Remotes")
    local achievementEvent = remotes:WaitForChild("AchievementEvent")
    
    achievementEvent:FireClient(player, "achievement_unlocked", {
        achievement = achievement,
        timestamp = tick()
    })
end

-- Send challenge complete notification
function GamificationHub:SendChallengeComplete(player, challenge)
    local remotes = ReplicatedStorage:WaitForChild("Remotes")
    local challengeEvent = remotes:WaitForChild("DailyChallengeEvent")
    
    challengeEvent:FireClient(player, "challenge_complete", {
        challenge = challenge,
        timestamp = tick()
    })
end

-- Send daily reset notification
function GamificationHub:SendDailyReset(player)
    local remotes = ReplicatedStorage:WaitForChild("Remotes")
    local challengeEvent = remotes:WaitForChild("DailyChallengeEvent")
    
    challengeEvent:FireClient(player, "daily_reset", {
        challenges = self.todaysChallenges,
        timestamp = tick()
    })
end

-- Announce level up
function GamificationHub:AnnounceLevelUp(player, level)
    -- Create announcement for all players
    for _, otherPlayer in ipairs(Players:GetPlayers()) do
        local remotes = ReplicatedStorage:WaitForChild("Remotes")
        local progressEvent = remotes:WaitForChild("GamificationProgressEvent")
        
        progressEvent:FireClient(otherPlayer, "player_level_up", {
            playerName = player.Name,
            level = level,
            timestamp = tick()
        })
    end
end

-- Unlock title for player
function GamificationHub:UnlockTitle(player, title)
    local progress = self.playerProgress[player.UserId]
    if not progress then return end
    
    if not progress.titles then
        progress.titles = {}
    end
    
    table.insert(progress.titles, {
        title = title,
        unlockedAt = os.time()
    })
    
    self:SendProgressUpdate(player, {
        type = "title_unlocked",
        title = title
    })
end

-- Track statistic
function GamificationHub:TrackStatistic(player, statType, value)
    local progress = self.playerProgress[player.UserId]
    if not progress then return end
    
    if statType == "lesson_completed" then
        progress.stats.lessonsCompleted = progress.stats.lessonsCompleted + 1
        self:AwardPoints(player, CONFIG.POINTS_PER_LESSON_COMPLETION, "Lesson Completed")
        self:UpdateChallengeProgress(player, "lessons_completed", 1)
        
    elseif statType == "quiz_completed" then
        progress.stats.quizzesCompleted = progress.stats.quizzesCompleted + 1
        self:AwardPoints(player, CONFIG.POINTS_PER_QUIZ_COMPLETION, "Quiz Completed")
        self:UpdateChallengeProgress(player, "complete_quiz", 1)
        
        if value.perfect then
            progress.stats.perfectQuizzes = progress.stats.perfectQuizzes + 1
            self:AwardCurrency(player, "gems", CONFIG.GEMS_PER_PERFECT_QUIZ)
            self:UpdateChallengeProgress(player, "perfect_quiz", 1)
        end
        
    elseif statType == "question_answered" then
        progress.stats.questionsAnswered = progress.stats.questionsAnswered + 1
        if value.correct then
            progress.stats.correctAnswers = progress.stats.correctAnswers + 1
            self:AwardPoints(player, CONFIG.POINTS_PER_CORRECT_ANSWER, "Correct Answer")
        end
        
    elseif statType == "environment_visited" then
        if not progress.stats.environmentsVisited[value] then
            progress.stats.environmentsVisited[value] = true
            self:UpdateChallengeProgress(player, "areas_visited", 1)
        end
        
    elseif statType == "team_challenge" then
        progress.stats.teamChallenges = progress.stats.teamChallenges + 1
    end
    
    -- Check for new achievements
    self:CheckAllAchievements(player)
end

-- Get player progress data
function GamificationHub:GetPlayerProgress(player)
    return self.playerProgress[player.UserId]
end

-- Save player progress (for external saving)
function GamificationHub:SavePlayerProgress(player)
    local progress = self.playerProgress[player.UserId]
    return progress
end

-- Module export
return GamificationHub