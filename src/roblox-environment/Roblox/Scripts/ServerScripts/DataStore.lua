--[[
    DataStore.lua - Data persistence layer for ToolboxAI Educational Platform
    
    Handles all data storage operations including:
    - Player progress and statistics
    - Achievement tracking
    - Quiz results and learning metrics
    - Session data and analytics
    - Backup and recovery systems
]]

local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local MessagingService = game:GetService("MessagingService")

-- Constants
local CONFIG = {
    DATASTORE_NAME = "ToolboxAI_PlayerData_v2",
    BACKUP_DATASTORE_NAME = "ToolboxAI_PlayerData_Backup_v2",
    ANALYTICS_DATASTORE_NAME = "ToolboxAI_Analytics_v2",
    LEADERBOARD_DATASTORE_NAME = "ToolboxAI_Leaderboard_v2",
    
    AUTO_SAVE_INTERVAL = 60, -- seconds
    MAX_RETRIES = 3,
    RETRY_DELAY = 2,
    CACHE_DURATION = 300, -- 5 minutes
    
    -- Version control for data migration
    DATA_VERSION = 2,
    
    -- API endpoints for backup
    BACKUP_API_ENDPOINT = "http://127.0.0.1:8008/backup",
    SYNC_API_ENDPOINT = "http://127.0.0.1:8008/sync"
}

-- DataStore Module
local DataStore = {}
DataStore.__index = DataStore

-- Cache system to reduce DataStore calls
local DataCache = {}
local CacheTimestamps = {}

-- Pending save queue for batch operations
local SaveQueue = {}
local LastSaveTime = tick()

-- DataStore references
local PlayerDataStore = nil
local BackupDataStore = nil
local AnalyticsDataStore = nil
local LeaderboardDataStore = nil

-- Initialize DataStore connections
function DataStore:Initialize()
    local success, error = pcall(function()
        PlayerDataStore = DataStoreService:GetDataStore(CONFIG.DATASTORE_NAME)
        BackupDataStore = DataStoreService:GetDataStore(CONFIG.BACKUP_DATASTORE_NAME)
        AnalyticsDataStore = DataStoreService:GetDataStore(CONFIG.ANALYTICS_DATASTORE_NAME)
        LeaderboardDataStore = DataStoreService:GetOrderedDataStore(CONFIG.LEADERBOARD_DATASTORE_NAME)
    end)
    
    if not success then
        warn("[DataStore] Failed to initialize DataStores:", error)
        return false
    end
    
    -- Start auto-save system
    self:StartAutoSave()
    
    -- Subscribe to cross-server messaging for data sync
    self:SetupCrossServerSync()
    
    print("[DataStore] Initialized successfully")
    return true
end

-- Create default player data structure
function DataStore:CreateDefaultPlayerData(player)
    return {
        -- Meta information
        userId = player.UserId,
        username = player.Name,
        dataVersion = CONFIG.DATA_VERSION,
        createdAt = os.time(),
        lastUpdated = os.time(),
        
        -- Progress tracking
        progress = {
            currentLevel = 1,
            experience = 0,
            totalPlayTime = 0,
            sessionsPlayed = 0,
            lastSessionDate = os.date("!*t"),
        },
        
        -- Educational metrics
        education = {
            currentGrade = 5,
            currentSubject = "General",
            completedLessons = {},
            currentLesson = nil,
            learningPath = {},
            masteredTopics = {},
        },
        
        -- Quiz performance
        quizData = {
            totalQuizzesTaken = 0,
            totalQuestionsAnswered = 0,
            correctAnswers = 0,
            averageScore = 0,
            bestScore = 0,
            quizHistory = {}, -- Last 50 quiz results
            subjectScores = {}, -- Score by subject
        },
        
        -- Achievements
        achievements = {
            unlocked = {},
            inProgress = {},
            points = 0,
            badges = {},
            titles = {},
        },
        
        -- Gamification
        gamification = {
            coins = 0,
            gems = 0,
            streak = 0,
            lastStreakDate = nil,
            dailyChallenges = {},
            weeklyGoals = {},
        },
        
        -- Statistics
        statistics = {
            environmentsExplored = 0,
            objectsInteracted = 0,
            npcsSpokenTo = 0,
            collectiblesFound = 0,
            puzzlesSolved = 0,
            timeBySubject = {}, -- Time spent per subject
            favoriteSubject = nil,
        },
        
        -- Settings and preferences
        settings = {
            soundEnabled = true,
            musicVolume = 0.5,
            effectsVolume = 0.5,
            difficulty = "intermediate",
            language = "en",
            colorblindMode = false,
        },
        
        -- Inventory and unlocks
        inventory = {
            items = {},
            cosmetics = {},
            tools = {},
            unlockedWorlds = {"tutorial"},
        },
        
        -- Social features
        social = {
            friends = {},
            teamId = nil,
            groupId = nil,
            referralCode = nil,
        }
    }
end

-- Load player data with caching and retry logic
function DataStore:LoadPlayerData(player)
    local userId = tostring(player.UserId)
    
    -- Check cache first
    if DataCache[userId] and self:IsCacheValid(userId) then
        print("[DataStore] Loading from cache for", player.Name)
        return DataCache[userId]
    end
    
    -- Try to load from primary DataStore
    local data = nil
    local success = false
    local attempts = 0
    
    while attempts < CONFIG.MAX_RETRIES and not success do
        attempts = attempts + 1
        
        success = pcall(function()
            data = PlayerDataStore:GetAsync(userId)
        end)
        
        if not success then
            warn("[DataStore] Load attempt", attempts, "failed for", player.Name)
            if attempts < CONFIG.MAX_RETRIES then
                wait(CONFIG.RETRY_DELAY)
            end
        end
    end
    
    -- If primary load failed, try backup
    if not success or not data then
        warn("[DataStore] Primary load failed, attempting backup load for", player.Name)
        success = pcall(function()
            data = BackupDataStore:GetAsync(userId)
        end)
    end
    
    -- If all loads failed, create default data
    if not data then
        print("[DataStore] Creating default data for new player", player.Name)
        data = self:CreateDefaultPlayerData(player)
    else
        -- Migrate data if needed
        data = self:MigrateData(data)
    end
    
    -- Update cache
    DataCache[userId] = data
    CacheTimestamps[userId] = tick()
    
    -- Send to backend for backup
    self:SyncWithBackend(player, data, "load")
    
    return data
end

-- Save player data with retry logic and backup
function DataStore:SavePlayerData(player, data)
    local userId = tostring(player.UserId)
    
    -- Update metadata
    data.lastUpdated = os.time()
    data.dataVersion = CONFIG.DATA_VERSION
    
    -- Update cache immediately
    DataCache[userId] = data
    CacheTimestamps[userId] = tick()
    
    -- Add to save queue for batch processing
    SaveQueue[userId] = {
        player = player,
        data = data,
        timestamp = tick()
    }
    
    -- Process save if enough time has passed
    if tick() - LastSaveTime >= 5 then
        self:ProcessSaveQueue()
    end
    
    return true
end

-- Process pending saves in batch
function DataStore:ProcessSaveQueue()
    if next(SaveQueue) == nil then
        return
    end
    
    LastSaveTime = tick()
    local processed = 0
    
    for userId, saveData in pairs(SaveQueue) do
        local success = false
        local attempts = 0
        
        -- Try primary save
        while attempts < CONFIG.MAX_RETRIES and not success do
            attempts = attempts + 1
            
            success = pcall(function()
                PlayerDataStore:SetAsync(userId, saveData.data)
            end)
            
            if not success and attempts < CONFIG.MAX_RETRIES then
                wait(CONFIG.RETRY_DELAY)
            end
        end
        
        -- Save to backup DataStore
        if success then
            pcall(function()
                BackupDataStore:SetAsync(userId, saveData.data)
            end)
            
            -- Sync with backend
            self:SyncWithBackend(saveData.player, saveData.data, "save")
            
            processed = processed + 1
        else
            warn("[DataStore] Failed to save data for user", userId)
        end
    end
    
    print("[DataStore] Processed", processed, "saves from queue")
    SaveQueue = {}
end

-- Auto-save system
function DataStore:StartAutoSave()
    spawn(function()
        while true do
            wait(CONFIG.AUTO_SAVE_INTERVAL)
            
            -- Process any pending saves
            self:ProcessSaveQueue()
            
            -- Save all active players
            for _, player in ipairs(Players:GetPlayers()) do
                local userId = tostring(player.UserId)
                if DataCache[userId] then
                    self:SavePlayerData(player, DataCache[userId])
                end
            end
            
            print("[DataStore] Auto-save completed at", os.date())
        end
    end)
end

-- Update specific player statistics
function DataStore:UpdatePlayerStats(player, statType, value)
    local userId = tostring(player.UserId)
    local data = DataCache[userId] or self:LoadPlayerData(player)
    
    if statType == "quiz_completed" then
        data.quizData.totalQuizzesTaken = data.quizData.totalQuizzesTaken + 1
        
        -- Add to history (keep last 50)
        table.insert(data.quizData.quizHistory, 1, value)
        if #data.quizData.quizHistory > 50 then
            table.remove(data.quizData.quizHistory)
        end
        
        -- Update average score
        local total = 0
        for _, quiz in ipairs(data.quizData.quizHistory) do
            total = total + (quiz.score or 0)
        end
        data.quizData.averageScore = total / #data.quizData.quizHistory
        
        -- Update best score
        if value.score > data.quizData.bestScore then
            data.quizData.bestScore = value.score
        end
        
    elseif statType == "achievement_unlocked" then
        data.achievements.unlocked[value.id] = {
            unlockedAt = os.time(),
            name = value.name,
            description = value.description
        }
        data.achievements.points = data.achievements.points + (value.points or 0)
        
    elseif statType == "lesson_completed" then
        table.insert(data.education.completedLessons, value)
        
    elseif statType == "play_time" then
        data.progress.totalPlayTime = data.progress.totalPlayTime + value
        
    elseif statType == "streak_update" then
        data.gamification.streak = value
        data.gamification.lastStreakDate = os.date("!*t")
    end
    
    -- Mark for save
    self:SavePlayerData(player, data)
    
    return data
end

-- Get leaderboard data
function DataStore:GetLeaderboard(category, limit)
    limit = limit or 10
    local leaderboard = {}
    
    local success, pages = pcall(function()
        return LeaderboardDataStore:GetSortedAsync(false, limit)
    end)
    
    if success then
        local currentPage = pages:GetCurrentPage()
        
        for rank, entry in ipairs(currentPage) do
            table.insert(leaderboard, {
                rank = rank,
                userId = entry.key,
                score = entry.value,
                username = self:GetUsernameFromCache(entry.key) or "Unknown"
            })
        end
    else
        warn("[DataStore] Failed to get leaderboard data")
    end
    
    return leaderboard
end

-- Update leaderboard score
function DataStore:UpdateLeaderboard(player, score)
    local userId = tostring(player.UserId)
    
    pcall(function()
        LeaderboardDataStore:SetAsync(userId, score)
    end)
    
    -- Store username for leaderboard display
    if DataCache[userId] then
        DataCache[userId].username = player.Name
    end
end

-- Analytics tracking
function DataStore:LogAnalytics(eventType, eventData)
    local analyticsEntry = {
        event = eventType,
        data = eventData,
        timestamp = os.time(),
        serverJobId = game.JobId
    }
    
    -- Store in analytics DataStore with timestamp key
    local key = string.format("%s_%d", eventType, os.time())
    
    pcall(function()
        AnalyticsDataStore:SetAsync(key, analyticsEntry)
    end)
    
    -- Also send to backend
    self:SendAnalyticsToBackend(analyticsEntry)
end

-- Sync with backend API
function DataStore:SyncWithBackend(player, data, operation)
    spawn(function()
        local url = operation == "save" and CONFIG.BACKUP_API_ENDPOINT or CONFIG.SYNC_API_ENDPOINT
        
        local success, result = pcall(function()
            return HttpService:RequestAsync({
                Url = url,
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json"
                },
                Body = HttpService:JSONEncode({
                    userId = player.UserId,
                    username = player.Name,
                    operation = operation,
                    data = data,
                    timestamp = os.time()
                })
            })
        end)
        
        if not success then
            warn("[DataStore] Backend sync failed:", result)
        end
    end)
end

-- Send analytics to backend
function DataStore:SendAnalyticsToBackend(analyticsData)
    spawn(function()
        pcall(function()
            HttpService:RequestAsync({
                Url = CONFIG.BACKUP_API_ENDPOINT .. "/analytics",
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json"
                },
                Body = HttpService:JSONEncode(analyticsData)
            })
        end)
    end)
end

-- Cross-server data synchronization
function DataStore:SetupCrossServerSync()
    -- Subscribe to data sync messages
    local success = pcall(function()
        MessagingService:SubscribeAsync("DataSync", function(message)
            local data = message.Data
            
            if data.operation == "update" then
                -- Update local cache if player is in this server
                local player = Players:GetPlayerByUserId(data.userId)
                if player and DataCache[tostring(data.userId)] then
                    -- Merge updates into local cache
                    for key, value in pairs(data.updates) do
                        DataCache[tostring(data.userId)][key] = value
                    end
                    CacheTimestamps[tostring(data.userId)] = tick()
                end
            end
        end)
    end)
    
    if success then
        print("[DataStore] Cross-server sync established")
    else
        warn("[DataStore] Failed to setup cross-server sync")
    end
end

-- Broadcast data update to other servers
function DataStore:BroadcastUpdate(userId, updates)
    pcall(function()
        MessagingService:PublishAsync("DataSync", {
            operation = "update",
            userId = userId,
            updates = updates,
            serverJobId = game.JobId,
            timestamp = os.time()
        })
    end)
end

-- Data migration for version updates
function DataStore:MigrateData(data)
    if not data.dataVersion then
        data.dataVersion = 1
    end
    
    -- Migrate from v1 to v2
    if data.dataVersion < 2 then
        -- Add new fields introduced in v2
        data.education = data.education or {
            currentGrade = 5,
            currentSubject = "General",
            completedLessons = {},
            currentLesson = nil,
            learningPath = {},
            masteredTopics = {}
        }
        
        data.gamification = data.gamification or {
            coins = 0,
            gems = 0,
            streak = 0,
            lastStreakDate = nil,
            dailyChallenges = {},
            weeklyGoals = {}
        }
        
        data.dataVersion = 2
        print("[DataStore] Migrated data from v1 to v2")
    end
    
    -- Future migrations would go here
    
    return data
end

-- Cache validation
function DataStore:IsCacheValid(userId)
    local timestamp = CacheTimestamps[userId]
    if not timestamp then
        return false
    end
    
    return (tick() - timestamp) < CONFIG.CACHE_DURATION
end

-- Get username from cache
function DataStore:GetUsernameFromCache(userId)
    if DataCache[userId] then
        return DataCache[userId].username
    end
    return nil
end

-- Clear cache for a specific player
function DataStore:ClearCache(userId)
    DataCache[userId] = nil
    CacheTimestamps[userId] = nil
end

-- Handle player removal (save and cleanup)
function DataStore:OnPlayerRemoving(player)
    local userId = tostring(player.UserId)
    
    -- Final save
    if DataCache[userId] then
        self:SavePlayerData(player, DataCache[userId])
    end
    
    -- Process any pending saves immediately
    if SaveQueue[userId] then
        self:ProcessSaveQueue()
    end
    
    -- Clear cache after a delay to handle any final operations
    wait(5)
    self:ClearCache(userId)
end

-- Export functions for external use
function DataStore:GetPlayerDataField(player, field)
    local userId = tostring(player.UserId)
    local data = DataCache[userId] or self:LoadPlayerData(player)
    
    -- Navigate nested fields (e.g., "quizData.totalQuizzesTaken")
    local current = data
    for key in string.gmatch(field, "[^%.]+") do
        current = current[key]
        if current == nil then
            return nil
        end
    end
    
    return current
end

function DataStore:SetPlayerDataField(player, field, value)
    local userId = tostring(player.UserId)
    local data = DataCache[userId] or self:LoadPlayerData(player)
    
    -- Navigate to the parent of the field
    local keys = {}
    for key in string.gmatch(field, "[^%.]+") do
        table.insert(keys, key)
    end
    
    local current = data
    for i = 1, #keys - 1 do
        local key = keys[i]
        if not current[key] then
            current[key] = {}
        end
        current = current[key]
    end
    
    -- Set the final value
    current[keys[#keys]] = value
    
    -- Save the updated data
    self:SavePlayerData(player, data)
    
    return true
end

-- Backup all player data
function DataStore:BackupAllData()
    print("[DataStore] Starting full backup...")
    local backupCount = 0
    
    for userId, data in pairs(DataCache) do
        local success = pcall(function()
            BackupDataStore:SetAsync(userId .. "_" .. os.time(), data)
        end)
        
        if success then
            backupCount = backupCount + 1
        end
    end
    
    print("[DataStore] Backed up data for", backupCount, "players")
    
    -- Log backup event
    self:LogAnalytics("backup_completed", {
        playerCount = backupCount,
        timestamp = os.time()
    })
end

-- Restore player data from backup
function DataStore:RestoreFromBackup(player, backupTimestamp)
    local userId = tostring(player.UserId)
    local backupKey = userId .. "_" .. backupTimestamp
    
    local success, data = pcall(function()
        return BackupDataStore:GetAsync(backupKey)
    end)
    
    if success and data then
        -- Restore the backup data
        DataCache[userId] = data
        CacheTimestamps[userId] = tick()
        
        -- Save to primary DataStore
        self:SavePlayerData(player, data)
        
        print("[DataStore] Restored backup for", player.Name, "from", os.date("%c", backupTimestamp))
        return true
    else
        warn("[DataStore] Failed to restore backup for", player.Name)
        return false
    end
end

-- Initialize the module
DataStore:Initialize()

-- Module export
return DataStore