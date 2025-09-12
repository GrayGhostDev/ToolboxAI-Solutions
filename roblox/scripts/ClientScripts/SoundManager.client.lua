--[[
    SoundManager.client.lua
    Comprehensive audio system for educational experiences
    
    Manages background music, sound effects, voice overs,
    and adaptive audio for learning activities
]]

local Players = game:GetService("Players")
local SoundService = game:GetService("SoundService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")
local ContentProvider = game:GetService("ContentProvider")

local player = Players.LocalPlayer

-- Sound categories
local SoundCategories = {
    MUSIC = "Music",
    SFX = "SoundEffects",
    VOICE = "VoiceOver",
    AMBIENT = "Ambient",
    UI = "Interface"
}

-- Sound storage
local sounds = {}
local soundGroups = {}
local activeSounds = {}

-- Volume settings
local masterVolume = 1.0
local categoryVolumes = {
    [SoundCategories.MUSIC] = 0.7,
    [SoundCategories.SFX] = 1.0,
    [SoundCategories.VOICE] = 1.0,
    [SoundCategories.AMBIENT] = 0.5,
    [SoundCategories.UI] = 0.8
}

-- Initialize sound system
local soundPreferences = {
    spatialSound = true,
    reverbEnabled = true,
    dopplerEffect = false,
    audioQuality = "high",
    maxPoolSize = 20,
    preloadSounds = true
}

-- Audio pools for performance
local soundPools = {}
local maxPooledSounds = 10

-- 3D Audio settings
local listener3D = workspace.CurrentCamera
local maxAudioDistance = 100
local referenceDistance = 10
local rolloffMode = Enum.RollOffMode.Linear

-- TODO: Create sound groups for audio mixing
local function InitializeSoundGroups()
    for category, name in pairs(SoundCategories) do
        local soundGroup = Instance.new("SoundGroup")
        soundGroup.Name = name
        soundGroup.Volume = categoryVolumes[name] or 1.0
        soundGroup.Parent = SoundService
        soundGroups[name] = soundGroup
        
        -- Configure audio effects
        if name == SoundCategories.MUSIC or name == SoundCategories.AMBIENT then
            -- Add reverb for music and ambient
            local reverb = Instance.new("ReverbSoundEffect")
            reverb.DecayTime = 1.5
            reverb.Density = 0.5
            reverb.Diffusion = 0.5
            reverb.DryLevel = -6
            reverb.WetLevel = -12
            reverb.Parent = soundGroup
        elseif name == SoundCategories.VOICE then
            -- Add compressor for voice clarity
            local compressor = Instance.new("CompressorSoundEffect")
            compressor.Threshold = -10
            compressor.Ratio = 4
            compressor.Attack = 0.1
            compressor.Release = 0.1
            compressor.Parent = soundGroup
        elseif name == SoundCategories.SFX then
            -- Add equalizer for sound effects
            local equalizer = Instance.new("EqualizerSoundEffect")
            equalizer.HighGain = 2
            equalizer.MidGain = 0
            equalizer.LowGain = 1
            equalizer.Parent = soundGroup
        end
    end
end

-- TODO: Implement sound loading and caching
local SoundLoader = {}

function SoundLoader.LoadSound(soundId, category, preload)
    -- Check cache first
    local cacheKey = soundId .. "_" .. category
    if sounds[cacheKey] then
        return sounds[cacheKey]:Clone()
    end
    
    -- Create new sound
    local sound = Instance.new("Sound")
    sound.SoundId = soundId
    sound.Name = cacheKey
    
    -- Set sound group
    if soundGroups[category] then
        sound.SoundGroup = soundGroups[category]
    end
    
    -- Configure based on category
    if category == SoundCategories.MUSIC then
        sound.Looped = true
        sound.Volume = 0.7
    elseif category == SoundCategories.SFX then
        sound.Volume = 1.0
        sound.RollOffMode = rolloffMode
        sound.RollOffMaxDistance = maxAudioDistance
        sound.RollOffMinDistance = referenceDistance
    elseif category == SoundCategories.VOICE then
        sound.Volume = 1.0
        sound.Priority = 1  -- Highest priority
    elseif category == SoundCategories.AMBIENT then
        sound.Looped = true
        sound.Volume = 0.5
    end
    
    -- Preload if requested
    if preload or soundPreferences.preloadSounds then
        ContentProvider:PreloadAsync({sound})
    end
    
    -- Store in cache
    sounds[cacheKey] = sound
    
    return sound:Clone()
end

function SoundLoader.LoadSoundBank(bankData)
    local loadedSounds = {}
    local totalSounds = 0
    
    -- Count total sounds
    for category, soundList in pairs(bankData) do
        totalSounds = totalSounds + #soundList
    end
    
    local loadedCount = 0
    
    -- Load all sounds in bank
    for category, soundList in pairs(bankData) do
        loadedSounds[category] = {}
        
        for _, soundData in ipairs(soundList) do
            local sound = SoundLoader.LoadSound(
                soundData.id or soundData,
                category,
                true  -- Preload all bank sounds
            )
            
            if type(soundData) == "table" then
                sound.Name = soundData.name or sound.Name
                sound.Volume = soundData.volume or sound.Volume
                sound.Pitch = soundData.pitch or 1
            end
            
            table.insert(loadedSounds[category], sound)
            loadedCount = loadedCount + 1
            
            -- Report progress
            local progress = loadedCount / totalSounds
            game.ReplicatedStorage:WaitForChild("SoundLoadProgress"):FireServer(progress)
        end
    end
    
    return loadedSounds
end

-- TODO: Implement background music system
local MusicSystem = {}
local currentMusic = nil
local musicPlaylist = {}

function MusicSystem.PlayMusic(soundId, fadeIn, crossfade)
    fadeIn = fadeIn ~= false  -- Default to true
    crossfade = crossfade or false
    
    local newMusic = SoundLoader.LoadSound(soundId, SoundCategories.MUSIC)
    newMusic.Looped = true
    newMusic.Parent = SoundService
    
    if currentMusic and currentMusic.Playing then
        if crossfade then
            -- Crossfade between tracks
            local fadeOutTween = TweenService:Create(
                currentMusic,
                TweenInfo.new(2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
                {Volume = 0}
            )
            
            newMusic.Volume = 0
            newMusic:Play()
            
            local fadeInTween = TweenService:Create(
                newMusic,
                TweenInfo.new(2, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
                {Volume = categoryVolumes[SoundCategories.MUSIC] * masterVolume}
            )
            
            fadeOutTween:Play()
            fadeInTween:Play()
            
            fadeOutTween.Completed:Connect(function()
                currentMusic:Stop()
                currentMusic:Destroy()
            end)
        else
            -- Stop current music
            MusicSystem.StopMusic(true)
            wait(0.5)  -- Small gap between tracks
        end
    end
    
    currentMusic = newMusic
    
    if fadeIn and not crossfade then
        currentMusic.Volume = 0
        currentMusic:Play()
        
        TweenService:Create(
            currentMusic,
            TweenInfo.new(1.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
            {Volume = categoryVolumes[SoundCategories.MUSIC] * masterVolume}
        ):Play()
    elseif not crossfade then
        currentMusic.Volume = categoryVolumes[SoundCategories.MUSIC] * masterVolume
        currentMusic:Play()
    end
    
    -- Track active sound
    table.insert(activeSounds, currentMusic)
    
    return currentMusic
end

function MusicSystem.StopMusic(fadeOut)
    if not currentMusic then return end
    
    if fadeOut then
        local fadeOutTween = TweenService:Create(
            currentMusic,
            TweenInfo.new(1.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
            {Volume = 0}
        )
        
        fadeOutTween:Play()
        
        fadeOutTween.Completed:Connect(function()
            if currentMusic then
                currentMusic:Stop()
                currentMusic:Destroy()
                
                -- Remove from active sounds
                local index = table.find(activeSounds, currentMusic)
                if index then
                    table.remove(activeSounds, index)
                end
                
                currentMusic = nil
            end
        end)
    else
        currentMusic:Stop()
        currentMusic:Destroy()
        
        -- Remove from active sounds
        local index = table.find(activeSounds, currentMusic)
        if index then
            table.remove(activeSounds, index)
        end
        
        currentMusic = nil
    end
end

function MusicSystem.CreatePlaylist(tracks, shuffle, loop)
    musicPlaylist = tracks
    MusicSystem.playlistIndex = 1
    MusicSystem.shuffleEnabled = shuffle or false
    MusicSystem.loopPlaylist = loop ~= false  -- Default to true
    
    if MusicSystem.shuffleEnabled then
        -- Shuffle playlist
        for i = #musicPlaylist, 2, -1 do
            local j = math.random(i)
            musicPlaylist[i], musicPlaylist[j] = musicPlaylist[j], musicPlaylist[i]
        end
    end
    
    -- Start playing first track
    if #musicPlaylist > 0 then
        MusicSystem.PlayMusic(musicPlaylist[1], true, false)
        
        -- Set up track completion handler
        if currentMusic then
            currentMusic.Ended:Connect(function()
                MusicSystem.NextTrack()
            end)
        end
    end
end

function MusicSystem.NextTrack()
    if not musicPlaylist or #musicPlaylist == 0 then return end
    
    MusicSystem.playlistIndex = MusicSystem.playlistIndex + 1
    
    if MusicSystem.playlistIndex > #musicPlaylist then
        if MusicSystem.loopPlaylist then
            MusicSystem.playlistIndex = 1
            
            if MusicSystem.shuffleEnabled then
                -- Re-shuffle on loop
                for i = #musicPlaylist, 2, -1 do
                    local j = math.random(i)
                    musicPlaylist[i], musicPlaylist[j] = musicPlaylist[j], musicPlaylist[i]
                end
            end
        else
            -- Playlist finished
            return
        end
    end
    
    MusicSystem.PlayMusic(musicPlaylist[MusicSystem.playlistIndex], true, true)
end

function MusicSystem.PreviousTrack()
    if not musicPlaylist or #musicPlaylist == 0 then return end
    
    MusicSystem.playlistIndex = MusicSystem.playlistIndex - 1
    
    if MusicSystem.playlistIndex < 1 then
        MusicSystem.playlistIndex = #musicPlaylist
    end
    
    MusicSystem.PlayMusic(musicPlaylist[MusicSystem.playlistIndex], true, true)
end

-- TODO: Implement sound effects system
local SFXSystem = {}
local sfxPool = {}

function SFXSystem.PlaySFX(soundId, position, volume, pitch)
    -- Check pool for available sound
    local poolKey = soundId .. "_sfx"
    if not soundPools[poolKey] then
        soundPools[poolKey] = {}
    end
    
    local sound = nil
    
    -- Get from pool if available
    for _, pooledSound in ipairs(soundPools[poolKey]) do
        if not pooledSound.Playing then
            sound = pooledSound
            break
        end
    end
    
    -- Create new if not in pool or pool exhausted
    if not sound then
        sound = SoundLoader.LoadSound(soundId, SoundCategories.SFX)
        
        if #soundPools[poolKey] < maxPooledSounds then
            table.insert(soundPools[poolKey], sound)
        end
    end
    
    -- Configure sound
    sound.Volume = (volume or 1.0) * categoryVolumes[SoundCategories.SFX] * masterVolume
    sound.PlaybackSpeed = pitch or 1.0
    
    -- Set 3D position if provided
    if position and soundPreferences.spatialSound then
        -- Create attachment for 3D sound
        local part = Instance.new("Part")
        part.Anchored = true
        part.CanCollide = false
        part.Transparency = 1
        part.Size = Vector3.new(1, 1, 1)
        part.Position = position
        part.Parent = workspace
        
        sound.Parent = part
        
        -- Clean up part after sound ends
        sound.Ended:Connect(function()
            part:Destroy()
            sound.Parent = SoundService  -- Return to service for pooling
        end)
    else
        sound.Parent = SoundService
    end
    
    sound:Play()
    
    -- Track active sound
    table.insert(activeSounds, sound)
    
    -- Clean up tracking when done
    sound.Ended:Connect(function()
        local index = table.find(activeSounds, sound)
        if index then
            table.remove(activeSounds, index)
        end
    end)
    
    return sound
end

function SFXSystem.PlayRandomSFX(soundIds, position, volumeRange, pitchRange)
    if #soundIds == 0 then return end
    
    local randomIndex = math.random(1, #soundIds)
    
    -- Add variation
    local volume = 1.0
    local pitch = 1.0
    
    if volumeRange then
        volume = math.random() * (volumeRange[2] - volumeRange[1]) + volumeRange[1]
    end
    
    if pitchRange then
        pitch = math.random() * (pitchRange[2] - pitchRange[1]) + pitchRange[1]
    else
        -- Default slight pitch variation
        pitch = 0.9 + math.random() * 0.2
    end
    
    return SFXSystem.PlaySFX(soundIds[randomIndex], position, volume, pitch)
end

-- Additional SFX functions
function SFXSystem.PlayFootstep(material, position)
    local footstepSounds = {
        Grass = {"rbxassetid://5869822439", "rbxassetid://5869822573"},
        Concrete = {"rbxassetid://5869820344", "rbxassetid://5869820471"},
        Wood = {"rbxassetid://5869819966", "rbxassetid://5869820095"},
        Metal = {"rbxassetid://5869819675", "rbxassetid://5869819814"},
        Water = {"rbxassetid://1838067089", "rbxassetid://1838067205"}
    }
    
    local sounds = footstepSounds[material.Name] or footstepSounds.Concrete
    SFXSystem.PlayRandomSFX(sounds, position, {0.3, 0.5}, {0.95, 1.05})
end

-- TODO: Implement voice over system
local VoiceSystem = {}
local currentVoice = nil
local voiceQueue = {}

function VoiceSystem.PlayVoiceOver(soundId, subtitle, priority, duration)
    priority = priority or 0
    
    -- Check if should interrupt current voice
    if currentVoice and currentVoice.Playing then
        if priority <= VoiceSystem.currentPriority then
            -- Queue this voice instead
            VoiceSystem.QueueVoiceOver(soundId, subtitle, priority, duration)
            return
        else
            -- Stop current voice for higher priority
            VoiceSystem.StopVoiceOver()
        end
    end
    
    VoiceSystem.currentPriority = priority
    currentVoice = SoundLoader.LoadSound(soundId, SoundCategories.VOICE)
    currentVoice.Parent = SoundService
    currentVoice:Play()
    
    -- Display subtitles
    if subtitle then
        VoiceSystem.ShowSubtitle(subtitle, duration or currentVoice.TimeLength)
    end
    
    -- Handle completion
    currentVoice.Ended:Connect(function()
        VoiceSystem.HideSubtitle()
        currentVoice = nil
        VoiceSystem.currentPriority = 0
        
        -- Play next in queue
        if #voiceQueue > 0 then
            local nextVoice = table.remove(voiceQueue, 1)
            VoiceSystem.PlayVoiceOver(
                nextVoice.soundId,
                nextVoice.subtitle,
                nextVoice.priority,
                nextVoice.duration
            )
        end
    end)
    
    -- Track active sound
    table.insert(activeSounds, currentVoice)
    
    return currentVoice
end

function VoiceSystem.ShowSubtitle(text, duration)
    local playerGui = player:WaitForChild("PlayerGui")
    local subtitleGui = playerGui:FindFirstChild("SubtitleGui")
    
    if not subtitleGui then
        subtitleGui = Instance.new("ScreenGui")
        subtitleGui.Name = "SubtitleGui"
        subtitleGui.DisplayOrder = 10
        subtitleGui.Parent = playerGui
    end
    
    -- Clear existing subtitles
    subtitleGui:ClearAllChildren()
    
    -- Create subtitle frame
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0.7, 0, 0.15, 0)
    frame.Position = UDim2.new(0.15, 0, 0.8, 0)
    frame.BackgroundColor3 = Color3.new(0, 0, 0)
    frame.BackgroundTransparency = 0.3
    frame.BorderSizePixel = 0
    frame.Parent = subtitleGui
    
    -- Add rounded corners
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 8)
    corner.Parent = frame
    
    -- Create text label
    local textLabel = Instance.new("TextLabel")
    textLabel.Size = UDim2.new(1, -20, 1, -10)
    textLabel.Position = UDim2.new(0, 10, 0, 5)
    textLabel.BackgroundTransparency = 1
    textLabel.Text = text
    textLabel.TextScaled = true
    textLabel.TextColor3 = Color3.new(1, 1, 1)
    textLabel.TextStrokeTransparency = 0.5
    textLabel.TextStrokeColor3 = Color3.new(0, 0, 0)
    textLabel.Font = Enum.Font.SourceSans
    textLabel.Parent = frame
    
    -- Fade in animation
    frame.BackgroundTransparency = 1
    textLabel.TextTransparency = 1
    
    TweenService:Create(
        frame,
        TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        {BackgroundTransparency = 0.3}
    ):Play()
    
    TweenService:Create(
        textLabel,
        TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        {TextTransparency = 0}
    ):Play()
    
    -- Auto-hide after duration
    if duration then
        task.wait(duration - 0.5)  -- Start fade out before end
        VoiceSystem.HideSubtitle()
    end
end

function VoiceSystem.HideSubtitle()
    local playerGui = player:WaitForChild("PlayerGui")
    local subtitleGui = playerGui:FindFirstChild("SubtitleGui")
    
    if subtitleGui then
        for _, child in ipairs(subtitleGui:GetChildren()) do
            if child:IsA("Frame") then
                -- Fade out animation
                TweenService:Create(
                    child,
                    TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
                    {BackgroundTransparency = 1}
                ):Play()
                
                local textLabel = child:FindFirstChildOfClass("TextLabel")
                if textLabel then
                    TweenService:Create(
                        textLabel,
                        TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
                        {TextTransparency = 1}
                    ):Play()
                end
            end
        end
        
        task.wait(0.3)
        subtitleGui:ClearAllChildren()
    end
end

function VoiceSystem.QueueVoiceOver(soundId, subtitle, priority, duration)
    table.insert(voiceQueue, {
        soundId = soundId,
        subtitle = subtitle,
        priority = priority or 0,
        duration = duration
    })
    
    -- Sort queue by priority
    table.sort(voiceQueue, function(a, b)
        return a.priority > b.priority
    end)
end

function VoiceSystem.StopVoiceOver()
    if currentVoice then
        currentVoice:Stop()
        currentVoice:Destroy()
        
        -- Remove from active sounds
        local index = table.find(activeSounds, currentVoice)
        if index then
            table.remove(activeSounds, index)
        end
        
        currentVoice = nil
        VoiceSystem.currentPriority = 0
    end
    
    VoiceSystem.HideSubtitle()
end

function VoiceSystem.ClearQueue()
    voiceQueue = {}
end

-- TODO: Implement ambient sound system
local AmbientSystem = {}
local ambientSounds = {}

function AmbientSystem.SetAmbience(soundId, volume, fadeTime)
    volume = volume or categoryVolumes[SoundCategories.AMBIENT]
    fadeTime = fadeTime or 2
    
    -- Fade out existing ambient sounds
    for _, ambient in ipairs(ambientSounds) do
        if ambient and ambient.Playing then
            TweenService:Create(
                ambient,
                TweenInfo.new(fadeTime, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
                {Volume = 0}
            ):Play()
            
            task.wait(fadeTime)
            ambient:Stop()
            ambient:Destroy()
        end
    end
    
    ambientSounds = {}
    
    -- Create new ambient sound
    local ambient = SoundLoader.LoadSound(soundId, SoundCategories.AMBIENT)
    ambient.Looped = true
    ambient.Volume = 0
    ambient.Parent = SoundService
    ambient:Play()
    
    -- Fade in
    TweenService:Create(
        ambient,
        TweenInfo.new(fadeTime, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        {Volume = volume * masterVolume}
    ):Play()
    
    table.insert(ambientSounds, ambient)
    table.insert(activeSounds, ambient)
    
    return ambient
end

function AmbientSystem.AddEnvironmentalSound(soundId, position, radius, interval)
    radius = radius or 50
    interval = interval or {5, 15}  -- Random interval between plays
    
    -- Create anchor part for sound
    local soundPart = Instance.new("Part")
    soundPart.Name = "EnvironmentalSound"
    soundPart.Anchored = true
    soundPart.CanCollide = false
    soundPart.Transparency = 1
    soundPart.Size = Vector3.new(1, 1, 1)
    soundPart.Position = position
    soundPart.Parent = workspace
    
    -- Create sound
    local sound = SoundLoader.LoadSound(soundId, SoundCategories.AMBIENT)
    sound.RollOffMaxDistance = radius
    sound.RollOffMinDistance = radius * 0.3
    sound.RollOffMode = Enum.RollOffMode.Linear
    sound.Parent = soundPart
    
    -- Randomized playback loop
    spawn(function()
        while soundPart and soundPart.Parent do
            local waitTime = math.random(interval[1], interval[2])
            wait(waitTime)
            
            if soundPart and soundPart.Parent then
                -- Only play if player is within range
                local character = player.Character
                if character and character:FindFirstChild("HumanoidRootPart") then
                    local distance = (character.HumanoidRootPart.Position - position).Magnitude
                    if distance <= radius * 1.5 then
                        sound:Play()
                    end
                end
            end
        end
    end)
    
    -- Store for cleanup
    table.insert(ambientSounds, sound)
    
    return soundPart
end

-- TODO: Implement UI sound system
local UISystem = {}

-- UI sound library
local uiSounds = {
    click = "rbxassetid://421058925",
    hover = "rbxassetid://10066936758",
    success = "rbxassetid://1838079553",
    error = "rbxassetid://2767090868",
    open = "rbxassetid://9119713951",
    close = "rbxassetid://9119720233",
    notification = "rbxassetid://1838079990",
    typing = "rbxassetid://1838064509",
    transition = "rbxassetid://1838054829",
    popup = "rbxassetid://10066931761"
}

-- Track last UI sound time to prevent spam
local lastUISoundTime = {}
local uiSoundCooldown = 0.05  -- Minimum time between same sounds

function UISystem.PlayUISound(soundType, volume, pitch)
    if not uiSounds[soundType] then
        warn("Unknown UI sound type:", soundType)
        return
    end
    
    -- Check cooldown
    local currentTime = tick()
    if lastUISoundTime[soundType] then
        if currentTime - lastUISoundTime[soundType] < uiSoundCooldown then
            return  -- Skip if too soon
        end
    end
    
    lastUISoundTime[soundType] = currentTime
    
    -- Play with slight variation for repeated sounds
    local pitchVariation = 1
    if soundType == "click" or soundType == "hover" then
        pitchVariation = 0.95 + math.random() * 0.1
    end
    
    SFXSystem.PlaySFX(
        uiSounds[soundType],
        nil,  -- No position for UI sounds
        volume or categoryVolumes[SoundCategories.UI],
        pitch or pitchVariation
    )
end

-- Automatic UI sound binding
function UISystem.BindToGui(gui)
    for _, descendant in ipairs(gui:GetDescendants()) do
        if descendant:IsA("GuiButton") then
            -- Click sound
            descendant.MouseButton1Click:Connect(function()
                UISystem.PlayUISound("click")
            end)
            
            -- Hover sound
            descendant.MouseEnter:Connect(function()
                UISystem.PlayUISound("hover", 0.5)
            end)
        elseif descendant:IsA("TextBox") then
            -- Typing sound
            descendant:GetPropertyChangedSignal("Text"):Connect(function()
                UISystem.PlayUISound("typing", 0.3)
            end)
        end
    end
end

-- TODO: Implement adaptive audio system
local AdaptiveAudio = {}

function AdaptiveAudio.AdjustToActivity(activityType)
    local adjustments = {
        quiz = {
            music = 0.3,
            sfx = 1.0,
            voice = 1.0,
            ambient = 0.2
        },
        lesson = {
            music = 0.4,
            sfx = 0.6,
            voice = 1.0,
            ambient = 0.3
        },
        exploration = {
            music = 0.7,
            sfx = 1.0,
            voice = 0.8,
            ambient = 0.8
        },
        achievement = {
            music = 1.0,
            sfx = 1.0,
            voice = 1.0,
            ambient = 0.5
        },
        menu = {
            music = 0.6,
            sfx = 1.0,
            voice = 1.0,
            ambient = 0.4
        }
    }
    
    local settings = adjustments[activityType] or adjustments.exploration
    
    -- Smoothly adjust volumes
    for category, targetVolume in pairs(settings) do
        local soundGroup = soundGroups[SoundCategories[string.upper(category)]]
        if soundGroup then
            TweenService:Create(
                soundGroup,
                TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut),
                {Volume = targetVolume * masterVolume}
            ):Play()
        end
    end
    
    -- Play activity-specific sound
    if activityType == "achievement" then
        SFXSystem.PlaySFX("rbxassetid://1847600267")  -- Victory sound
    elseif activityType == "quiz" then
        MusicSystem.PlayMusic("rbxassetid://1838639660", true)  -- Quiz music
    end
end

function AdaptiveAudio.AdjustToPerformance(performance)
    -- Performance levels: struggling, improving, succeeding, mastering
    
    if performance == "struggling" then
        -- Calming, encouraging audio
        if currentMusic then
            currentMusic.PlaybackSpeed = 0.9  -- Slower tempo
        end
        
        -- Play encouraging sound
        VoiceSystem.PlayVoiceOver(
            "rbxassetid://1838080123",
            "You're doing great! Keep trying!",
            1
        )
        
        -- Reduce distracting sounds
        VolumeControl.SetCategoryVolume(SoundCategories.AMBIENT, 0.2)
        
    elseif performance == "improving" then
        -- Normal audio with positive reinforcement
        if currentMusic then
            currentMusic.PlaybackSpeed = 1.0
        end
        
        -- Play positive feedback
        SFXSystem.PlaySFX("rbxassetid://1838062910")  -- Correct sound
        
    elseif performance == "succeeding" then
        -- Upbeat, energizing audio
        if currentMusic then
            currentMusic.PlaybackSpeed = 1.05  -- Slightly faster
        end
        
        -- Play success sounds
        SFXSystem.PlaySFX("rbxassetid://1838079553")  -- Complete sound
        
        -- Increase ambient energy
        VolumeControl.SetCategoryVolume(SoundCategories.AMBIENT, 0.6)
        
    elseif performance == "mastering" then
        -- Celebratory audio
        if currentMusic then
            currentMusic.PlaybackSpeed = 1.1  -- Energetic tempo
        end
        
        -- Play celebration
        MusicSystem.PlayMusic("rbxassetid://1847600267", true)  -- Victory music
        SFXSystem.PlaySFX("rbxassetid://1838052928")  -- Level up sound
        
        VoiceSystem.PlayVoiceOver(
            "rbxassetid://1838080456",
            "Amazing work! You've mastered this!",
            2
        )
    end
end

-- TODO: Implement volume control system
local VolumeControl = {}

function VolumeControl.SetMasterVolume(volume)
    masterVolume = math.clamp(volume, 0, 1)
    
    -- Apply to all sound groups
    for category, group in pairs(soundGroups) do
        group.Volume = masterVolume * categoryVolumes[category]
    end
    
    -- Update current sounds
    if currentMusic then
        currentMusic.Volume = categoryVolumes[SoundCategories.MUSIC] * masterVolume
    end
    
    for _, ambient in ipairs(ambientSounds) do
        if ambient and ambient.Parent then
            ambient.Volume = categoryVolumes[SoundCategories.AMBIENT] * masterVolume
        end
    end
    
    -- Save preference
    AudioSettings.SaveSettings()
end

function VolumeControl.SetCategoryVolume(category, volume)
    categoryVolumes[category] = math.clamp(volume, 0, 1)
    
    if soundGroups[category] then
        soundGroups[category].Volume = masterVolume * categoryVolumes[category]
    end
    
    -- Update active sounds in category
    if category == SoundCategories.MUSIC and currentMusic then
        currentMusic.Volume = categoryVolumes[category] * masterVolume
    elseif category == SoundCategories.AMBIENT then
        for _, ambient in ipairs(ambientSounds) do
            if ambient and ambient.Parent then
                ambient.Volume = categoryVolumes[category] * masterVolume
            end
        end
    end
    
    -- Save preference
    AudioSettings.SaveSettings()
end

VolumeControl.mutedCategories = {}
VolumeControl.previousVolumes = {}

function VolumeControl.MuteCategory(category, muted)
    if muted then
        -- Store previous volume and mute
        VolumeControl.previousVolumes[category] = categoryVolumes[category]
        VolumeControl.mutedCategories[category] = true
        VolumeControl.SetCategoryVolume(category, 0)
    else
        -- Restore previous volume
        VolumeControl.mutedCategories[category] = false
        local previousVolume = VolumeControl.previousVolumes[category] or 1.0
        VolumeControl.SetCategoryVolume(category, previousVolume)
    end
end

function VolumeControl.ToggleMute(category)
    VolumeControl.MuteCategory(category, not VolumeControl.mutedCategories[category])
end

function VolumeControl.MuteAll(muted)
    for category, _ in pairs(SoundCategories) do
        VolumeControl.MuteCategory(category, muted)
    end
end

-- TODO: Implement audio settings persistence
local AudioSettings = {}

function AudioSettings.SaveSettings()
    local settings = {
        masterVolume = masterVolume,
        categoryVolumes = categoryVolumes,
        mutedCategories = VolumeControl.mutedCategories,
        preferences = soundPreferences,
        timestamp = tick()
    }
    
    -- Save to ReplicatedStorage for server to persist
    local success, result = pcall(function()
        return ReplicatedStorage:WaitForChild("SaveAudioSettings"):InvokeServer(settings)
    end)
    
    if success then
        print("Audio settings saved")
    else
        warn("Failed to save audio settings:", result)
    end
end

function AudioSettings.LoadSettings()
    local success, settings = pcall(function()
        return ReplicatedStorage:WaitForChild("LoadAudioSettings"):InvokeServer()
    end)
    
    if success and settings then
        -- Apply loaded settings
        if settings.masterVolume then
            masterVolume = settings.masterVolume
        end
        
        if settings.categoryVolumes then
            for category, volume in pairs(settings.categoryVolumes) do
                categoryVolumes[category] = volume
            end
        end
        
        if settings.mutedCategories then
            VolumeControl.mutedCategories = settings.mutedCategories
        end
        
        if settings.preferences then
            for key, value in pairs(settings.preferences) do
                soundPreferences[key] = value
            end
        end
        
        -- Apply volumes to sound groups
        for category, group in pairs(soundGroups) do
            group.Volume = masterVolume * categoryVolumes[category]
        end
        
        print("Audio settings loaded")
    else
        print("Using default audio settings")
    end
end

-- TODO: Implement audio ducking system
local AudioDucking = {}

AudioDucking.activeDucks = {}

function AudioDucking.DuckAudio(category, amount, duration)
    amount = math.clamp(amount, 0, 1)
    duration = duration or 2
    
    -- Store original volume if not already ducked
    if not AudioDucking.activeDucks[category] then
        AudioDucking.activeDucks[category] = categoryVolumes[category]
    end
    
    local targetVolume = AudioDucking.activeDucks[category] * (1 - amount)
    
    -- Duck the audio
    local soundGroup = soundGroups[category]
    if soundGroup then
        TweenService:Create(
            soundGroup,
            TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
            {Volume = targetVolume * masterVolume}
        ):Play()
    end
    
    -- Restore after duration
    task.wait(duration)
    
    if soundGroup then
        TweenService:Create(
            soundGroup,
            TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
            {Volume = AudioDucking.activeDucks[category] * masterVolume}
        ):Play()
    end
    
    AudioDucking.activeDucks[category] = nil
end

function AudioDucking.DuckAllExcept(exceptCategory, amount, duration)
    for category, _ in pairs(SoundCategories) do
        if category ~= exceptCategory then
            spawn(function()
                AudioDucking.DuckAudio(category, amount, duration)
            end)
        end
    end
end

-- TODO: Implement positional audio helpers
local PositionalAudio = {}

function PositionalAudio.Calculate3DVolume(soundPosition, listenerPosition, maxDistance, minDistance)
    minDistance = minDistance or referenceDistance
    maxDistance = maxDistance or maxAudioDistance
    
    local distance = (soundPosition - listenerPosition).Magnitude
    
    -- Different falloff curves
    local volume = 1
    
    if rolloffMode == Enum.RollOffMode.Linear then
        -- Linear falloff
        if distance <= minDistance then
            volume = 1
        elseif distance >= maxDistance then
            volume = 0
        else
            volume = 1 - ((distance - minDistance) / (maxDistance - minDistance))
        end
    elseif rolloffMode == Enum.RollOffMode.InverseTapered then
        -- Inverse tapered falloff
        volume = minDistance / (minDistance + (distance - minDistance))
    else
        -- Inverse falloff
        volume = (minDistance / distance) ^ 2
    end
    
    -- Account for obstacles if enabled
    if soundPreferences.spatialSound then
        local ray = workspace:Raycast(
            listenerPosition,
            soundPosition - listenerPosition,
            RaycastParams.new()
        )
        
        if ray and ray.Instance then
            -- Muffle sound if obstructed
            volume = volume * 0.3
        end
    end
    
    return math.clamp(volume, 0, 1)
end

function PositionalAudio.CalculatePanning(soundPosition, listenerCFrame)
    -- Calculate stereo panning based on position
    local relativePos = listenerCFrame:PointToObjectSpace(soundPosition)
    local angle = math.atan2(relativePos.X, relativePos.Z)
    
    -- Convert to panning value (-1 to 1)
    local pan = math.sin(angle)
    return math.clamp(pan, -1, 1)
end

-- Initialize the sound system
InitializeSoundGroups()
AudioSettings.LoadSettings()

-- TODO: Clean up on player leaving
-- Additional utility functions
local function CleanupAllSounds()
    -- Stop all active sounds
    for _, sound in ipairs(activeSounds) do
        if sound and sound.Parent then
            sound:Stop()
            sound:Destroy()
        end
    end
    activeSounds = {}
    
    -- Clear music
    if currentMusic then
        currentMusic:Stop()
        currentMusic:Destroy()
        currentMusic = nil
    end
    
    -- Clear ambient
    for _, ambient in ipairs(ambientSounds) do
        if ambient and ambient.Parent then
            ambient:Stop()
            ambient:Destroy()
        end
    end
    ambientSounds = {}
    
    -- Clear voice
    if currentVoice then
        currentVoice:Stop()
        currentVoice:Destroy()
        currentVoice = nil
    end
    
    -- Clear pools
    for _, pool in pairs(soundPools) do
        for _, sound in ipairs(pool) do
            if sound and sound.Parent then
                sound:Destroy()
            end
        end
    end
    soundPools = {}
end

Players.PlayerRemoving:Connect(function(leavingPlayer)
    if leavingPlayer == player then
        -- Save settings before cleanup
        AudioSettings.SaveSettings()
        
        -- Clean up all audio
        CleanupAllSounds()
        
        -- Clear cache
        sounds = {}
    end
end)

-- Export sound manager API
_G.SoundManager = {
    -- Music
    PlayMusic = MusicSystem.PlayMusic,
    StopMusic = MusicSystem.StopMusic,
    CreatePlaylist = MusicSystem.CreatePlaylist,
    NextTrack = MusicSystem.NextTrack,
    PreviousTrack = MusicSystem.PreviousTrack,
    
    -- Sound Effects
    PlaySFX = SFXSystem.PlaySFX,
    PlayRandomSFX = SFXSystem.PlayRandomSFX,
    PlayFootstep = SFXSystem.PlayFootstep,
    
    -- Voice
    PlayVoiceOver = VoiceSystem.PlayVoiceOver,
    QueueVoiceOver = VoiceSystem.QueueVoiceOver,
    StopVoiceOver = VoiceSystem.StopVoiceOver,
    ClearVoiceQueue = VoiceSystem.ClearQueue,
    
    -- Ambient
    SetAmbience = AmbientSystem.SetAmbience,
    AddEnvironmentalSound = AmbientSystem.AddEnvironmentalSound,
    
    -- UI
    PlayUISound = UISystem.PlayUISound,
    BindToGui = UISystem.BindToGui,
    
    -- Adaptive
    AdjustToActivity = AdaptiveAudio.AdjustToActivity,
    AdjustToPerformance = AdaptiveAudio.AdjustToPerformance,
    
    -- Volume
    SetMasterVolume = VolumeControl.SetMasterVolume,
    SetCategoryVolume = VolumeControl.SetCategoryVolume,
    MuteCategory = VolumeControl.MuteCategory,
    ToggleMute = VolumeControl.ToggleMute,
    MuteAll = VolumeControl.MuteAll,
    
    -- Ducking
    DuckAudio = AudioDucking.DuckAudio,
    DuckAllExcept = AudioDucking.DuckAllExcept,
    
    -- Settings
    SaveSettings = AudioSettings.SaveSettings,
    LoadSettings = AudioSettings.LoadSettings,
    
    -- Utility
    CleanupAllSounds = CleanupAllSounds,
    Calculate3DVolume = PositionalAudio.Calculate3DVolume,
    CalculatePanning = PositionalAudio.CalculatePanning
}

print("SoundManager initialized")