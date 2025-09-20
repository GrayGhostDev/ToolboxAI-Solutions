--!strict
--[[
    Asset Manager Service
    Manages generated assets with versioning, search, and organization
]]

local HttpService = game:GetService("HttpService")
local ContentProvider = game:GetService("ContentProvider")
local AssetService = game:GetService("AssetService")
local InsertService = game:GetService("InsertService")
local MarketplaceService = game:GetService("MarketplaceService")
local ThumbnailGenerator = game:GetService("ThumbnailGenerator")
local RunService = game:GetService("RunService")

-- Types
type AssetType =
    "Model" | "Script" | "LocalScript" | "ModuleScript" |
    "Part" | "MeshPart" | "Union" |
    "Decal" | "Texture" | "Sound" |
    "Animation" | "AnimationController" |
    "GUI" | "SurfaceGui" | "BillboardGui" |
    "ParticleEmitter" | "Beam" | "Trail"

type AssetMetadata = {
    id: string,
    name: string,
    type: AssetType,
    category: string,
    tags: {string},
    description: string,
    creator: string,
    createdAt: number,
    modifiedAt: number,
    version: number,
    size: number,
    thumbnailUrl: string?,
    dependencies: {string}?,
    permissions: {
        canEdit: boolean,
        canShare: boolean,
        canDelete: boolean
    }
}

type AssetVersion = {
    version: number,
    timestamp: number,
    changes: string,
    author: string,
    data: any,
    checksum: string
}

type SearchFilters = {
    type: AssetType?,
    category: string?,
    tags: {string}?,
    creator: string?,
    dateRange: {start: number, end: number}?,
    searchText: string?,
    sortBy: string?,
    sortOrder: "asc" | "desc"?
}

type AssetCollection = {
    id: string,
    name: string,
    description: string,
    assets: {string},
    thumbnail: string?,
    isPublic: boolean,
    createdAt: number,
    modifiedAt: number
}

-- Asset Manager Class
local AssetManager = {}
AssetManager.__index = AssetManager

function AssetManager.new(config: any, stateManager: any, eventEmitter: any)
    local self = setmetatable({}, AssetManager)

    self.config = config
    self.stateManager = stateManager
    self.eventEmitter = eventEmitter

    -- Asset storage
    self.assets = {} -- Map of asset ID to metadata
    self.versions = {} -- Map of asset ID to version history
    self.collections = {} -- User-defined collections
    self.thumbnails = {} -- Cached thumbnails

    -- Search index
    self.searchIndex = {
        byType = {},
        byCategory = {},
        byTag = {},
        byCreator = {},
        byDate = {}
    }

    -- Local storage paths
    self.storagePath = "ToolboxAI_Assets"
    self.thumbnailPath = "ToolboxAI_Thumbnails"

    -- Statistics
    self.stats = {
        totalAssets = 0,
        totalSize = 0,
        totalVersions = 0,
        recentlyUsed = {},
        popular = {}
    }

    -- Initialize
    self:initialize()

    return self
end

function AssetManager:initialize()
    -- Load saved assets from local storage
    self:loadLocalAssets()

    -- Sync with backend
    self:syncWithBackend()

    -- Build search index
    self:buildSearchIndex()

    -- Start auto-save timer
    self:startAutoSave()

    print("[AssetManager] Initialized with", self.stats.totalAssets, "assets")
end

function AssetManager:loadLocalAssets()
    -- Load from plugin settings
    local savedData = self.config.plugin:GetSetting("AssetManager_Data")
    if savedData then
        local data = HttpService:JSONDecode(savedData)
        self.assets = data.assets or {}
        self.collections = data.collections or {}
        self.stats = data.stats or self.stats
    end
end

function AssetManager:saveLocalAssets()
    -- Save to plugin settings
    local data = {
        assets = self.assets,
        collections = self.collections,
        stats = self.stats,
        timestamp = os.time()
    }

    self.config.plugin:SetSetting("AssetManager_Data", HttpService:JSONEncode(data))
end

function AssetManager:syncWithBackend()
    task.spawn(function()
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = self.config.backendUrl .. "/api/assets/sync",
                Method = "POST",
                Headers = {
                    ["Content-Type"] = "application/json",
                    ["Authorization"] = "Bearer " .. (self.config.authToken or "")
                },
                Body = HttpService:JSONEncode({
                    localAssets = self:getAssetIds(),
                    lastSync = self.stats.lastSync or 0
                })
            })
        end)

        if success and response.Success then
            local syncData = HttpService:JSONDecode(response.Body)
            self:processSyncData(syncData)
        end
    end)
end

function AssetManager:processSyncData(syncData: any)
    -- Add new assets
    for _, asset in ipairs(syncData.newAssets or {}) do
        self:addAsset(asset, false) -- Don't sync back
    end

    -- Update existing assets
    for _, update in ipairs(syncData.updates or {}) do
        self:updateAssetMetadata(update.id, update.metadata)
    end

    -- Remove deleted assets
    for _, assetId in ipairs(syncData.deleted or {}) do
        self:removeAsset(assetId, false)
    end

    self.stats.lastSync = os.time()
    self.eventEmitter:emit("assetsSynced", {
        added = #(syncData.newAssets or {}),
        updated = #(syncData.updates or {}),
        deleted = #(syncData.deleted or {})
    })
end

function AssetManager:createAsset(instance: Instance, metadata: AssetMetadata?): string
    local assetId = HttpService:GenerateGUID(false)

    -- Generate metadata if not provided
    local meta = metadata or {
        id = assetId,
        name = instance.Name,
        type = instance.ClassName as AssetType,
        category = "Uncategorized",
        tags = {},
        description = "",
        creator = game:GetService("StudioService"):GetUserId(),
        createdAt = os.time(),
        modifiedAt = os.time(),
        version = 1,
        size = self:calculateSize(instance),
        permissions = {
            canEdit = true,
            canShare = true,
            canDelete = true
        }
    }

    -- Store asset
    self.assets[assetId] = meta

    -- Create first version
    self:createVersion(assetId, instance, "Initial version")

    -- Generate thumbnail
    self:generateThumbnail(assetId, instance)

    -- Update search index
    self:indexAsset(meta)

    -- Update stats
    self.stats.totalAssets = self.stats.totalAssets + 1
    self.stats.totalSize = self.stats.totalSize + meta.size

    -- Emit event
    self.eventEmitter:emit("assetCreated", meta)

    -- Sync with backend
    self:syncAssetToBackend(meta)

    return assetId
end

function AssetManager:addAsset(assetData: any, syncToBackend: boolean?)
    syncToBackend = syncToBackend ~= false -- Default true

    -- Store asset
    self.assets[assetData.id] = assetData

    -- Index for search
    self:indexAsset(assetData)

    -- Update stats
    self.stats.totalAssets = self.stats.totalAssets + 1
    self.stats.totalSize = self.stats.totalSize + (assetData.size or 0)

    -- Sync if needed
    if syncToBackend then
        self:syncAssetToBackend(assetData)
    end

    -- Emit event
    self.eventEmitter:emit("assetAdded", assetData)
end

function AssetManager:updateAsset(assetId: string, instance: Instance, changes: string?)
    local asset = self.assets[assetId]
    if not asset then
        warn("[AssetManager] Asset not found:", assetId)
        return
    end

    -- Update metadata
    asset.modifiedAt = os.time()
    asset.version = asset.version + 1
    asset.size = self:calculateSize(instance)

    -- Create new version
    self:createVersion(assetId, instance, changes or "Updated")

    -- Regenerate thumbnail if needed
    if self:shouldRegenerateThumbnail(asset.type) then
        self:generateThumbnail(assetId, instance)
    end

    -- Update search index
    self:reindexAsset(asset)

    -- Emit event
    self.eventEmitter:emit("assetUpdated", asset)

    -- Sync with backend
    self:syncAssetToBackend(asset)
end

function AssetManager:createVersion(assetId: string, instance: Instance, changes: string)
    if not self.versions[assetId] then
        self.versions[assetId] = {}
    end

    local version: AssetVersion = {
        version = #self.versions[assetId] + 1,
        timestamp = os.time(),
        changes = changes,
        author = tostring(game:GetService("StudioService"):GetUserId()),
        data = self:serializeInstance(instance),
        checksum = self:generateChecksum(instance)
    }

    table.insert(self.versions[assetId], version)
    self.stats.totalVersions = self.stats.totalVersions + 1

    -- Keep only last N versions
    local maxVersions = self.config.maxVersionsPerAsset or 10
    if #self.versions[assetId] > maxVersions then
        table.remove(self.versions[assetId], 1)
    end

    return version
end

function AssetManager:getAsset(assetId: string): (Instance?, AssetMetadata?)
    local metadata = self.assets[assetId]
    if not metadata then
        return nil, nil
    end

    -- Get latest version
    local versions = self.versions[assetId]
    if not versions or #versions == 0 then
        return nil, metadata
    end

    local latestVersion = versions[#versions]
    local instance = self:deserializeInstance(latestVersion.data)

    -- Track usage
    self:trackUsage(assetId)

    return instance, metadata
end

function AssetManager:getAssetVersion(assetId: string, version: number): Instance?
    local versions = self.versions[assetId]
    if not versions then
        return nil
    end

    for _, v in ipairs(versions) do
        if v.version == version then
            return self:deserializeInstance(v.data)
        end
    end

    return nil
end

function AssetManager:removeAsset(assetId: string, syncToBackend: boolean?)
    syncToBackend = syncToBackend ~= false

    local asset = self.assets[assetId]
    if not asset then
        return false
    end

    -- Check permissions
    if not asset.permissions.canDelete then
        warn("[AssetManager] Cannot delete protected asset:", assetId)
        return false
    end

    -- Remove from collections
    for _, collection in pairs(self.collections) do
        local index = table.find(collection.assets, assetId)
        if index then
            table.remove(collection.assets, index)
        end
    end

    -- Update stats
    self.stats.totalAssets = self.stats.totalAssets - 1
    self.stats.totalSize = self.stats.totalSize - asset.size

    -- Remove from search index
    self:deindexAsset(asset)

    -- Delete data
    self.assets[assetId] = nil
    self.versions[assetId] = nil
    self.thumbnails[assetId] = nil

    -- Sync if needed
    if syncToBackend then
        self:deleteAssetFromBackend(assetId)
    end

    -- Emit event
    self.eventEmitter:emit("assetRemoved", assetId)

    return true
end

function AssetManager:searchAssets(filters: SearchFilters): {AssetMetadata}
    local results = {}
    local searchText = filters.searchText and string.lower(filters.searchText)

    for assetId, asset in pairs(self.assets) do
        local matches = true

        -- Type filter
        if filters.type and asset.type ~= filters.type then
            matches = false
        end

        -- Category filter
        if matches and filters.category and asset.category ~= filters.category then
            matches = false
        end

        -- Tag filter
        if matches and filters.tags then
            local hasTag = false
            for _, filterTag in ipairs(filters.tags) do
                for _, assetTag in ipairs(asset.tags) do
                    if filterTag == assetTag then
                        hasTag = true
                        break
                    end
                end
                if hasTag then break end
            end
            if not hasTag then
                matches = false
            end
        end

        -- Creator filter
        if matches and filters.creator and asset.creator ~= filters.creator then
            matches = false
        end

        -- Date range filter
        if matches and filters.dateRange then
            if asset.createdAt < filters.dateRange.start or
               asset.createdAt > filters.dateRange.end then
                matches = false
            end
        end

        -- Text search
        if matches and searchText then
            local nameMatch = string.find(string.lower(asset.name), searchText)
            local descMatch = string.find(string.lower(asset.description or ""), searchText)
            local tagMatch = false

            for _, tag in ipairs(asset.tags) do
                if string.find(string.lower(tag), searchText) then
                    tagMatch = true
                    break
                end
            end

            if not (nameMatch or descMatch or tagMatch) then
                matches = false
            end
        end

        if matches then
            table.insert(results, asset)
        end
    end

    -- Sort results
    if filters.sortBy then
        self:sortResults(results, filters.sortBy, filters.sortOrder or "asc")
    end

    return results
end

function AssetManager:sortResults(results: {AssetMetadata}, sortBy: string, order: string)
    table.sort(results, function(a, b)
        local aVal = a[sortBy]
        local bVal = b[sortBy]

        if aVal == nil or bVal == nil then
            return false
        end

        if order == "asc" then
            return aVal < bVal
        else
            return aVal > bVal
        end
    end)
end

function AssetManager:createCollection(name: string, description: string?): string
    local collectionId = HttpService:GenerateGUID(false)

    local collection: AssetCollection = {
        id = collectionId,
        name = name,
        description = description or "",
        assets = {},
        isPublic = false,
        createdAt = os.time(),
        modifiedAt = os.time()
    }

    self.collections[collectionId] = collection

    self.eventEmitter:emit("collectionCreated", collection)

    return collectionId
end

function AssetManager:addToCollection(collectionId: string, assetId: string)
    local collection = self.collections[collectionId]
    local asset = self.assets[assetId]

    if not collection or not asset then
        return false
    end

    if not table.find(collection.assets, assetId) then
        table.insert(collection.assets, assetId)
        collection.modifiedAt = os.time()

        self.eventEmitter:emit("assetAddedToCollection", {
            collectionId = collectionId,
            assetId = assetId
        })

        return true
    end

    return false
end

function AssetManager:removeFromCollection(collectionId: string, assetId: string)
    local collection = self.collections[collectionId]
    if not collection then
        return false
    end

    local index = table.find(collection.assets, assetId)
    if index then
        table.remove(collection.assets, index)
        collection.modifiedAt = os.time()

        self.eventEmitter:emit("assetRemovedFromCollection", {
            collectionId = collectionId,
            assetId = assetId
        })

        return true
    end

    return false
end

function AssetManager:getCollection(collectionId: string): AssetCollection?
    return self.collections[collectionId]
end

function AssetManager:getCollections(): {AssetCollection}
    local collections = {}
    for _, collection in pairs(self.collections) do
        table.insert(collections, collection)
    end
    return collections
end

function AssetManager:generateThumbnail(assetId: string, instance: Instance)
    task.spawn(function()
        -- Create a viewport frame for thumbnail
        local viewport = Instance.new("ViewportFrame")
        viewport.Size = UDim2.new(0, 256, 0, 256)
        viewport.BackgroundColor3 = Color3.fromRGB(40, 40, 40)

        local camera = Instance.new("Camera")
        camera.Parent = viewport
        viewport.CurrentCamera = camera

        -- Clone instance for thumbnail
        local clone = instance:Clone()
        clone.Parent = viewport

        -- Position camera
        if clone:IsA("Model") then
            local cf, size = clone:GetBoundingBox()
            camera.CFrame = CFrame.lookAt(
                cf.Position + Vector3.new(size.X, size.Y, size.Z) * 2,
                cf.Position,
                Vector3.new(0, 1, 0)
            )
        else
            camera.CFrame = CFrame.lookAt(
                Vector3.new(10, 10, 10),
                Vector3.new(0, 0, 0),
                Vector3.new(0, 1, 0)
            )
        end

        -- Wait a frame for render
        RunService.RenderStepped:Wait()

        -- Store thumbnail reference
        self.thumbnails[assetId] = viewport

        -- Update asset metadata
        local asset = self.assets[assetId]
        if asset then
            asset.thumbnailUrl = "viewport:" .. assetId
        end

        self.eventEmitter:emit("thumbnailGenerated", assetId)
    end)
end

function AssetManager:getThumbnail(assetId: string): ViewportFrame?
    return self.thumbnails[assetId]
end

function AssetManager:indexAsset(asset: AssetMetadata)
    -- Index by type
    if not self.searchIndex.byType[asset.type] then
        self.searchIndex.byType[asset.type] = {}
    end
    table.insert(self.searchIndex.byType[asset.type], asset.id)

    -- Index by category
    if not self.searchIndex.byCategory[asset.category] then
        self.searchIndex.byCategory[asset.category] = {}
    end
    table.insert(self.searchIndex.byCategory[asset.category], asset.id)

    -- Index by tags
    for _, tag in ipairs(asset.tags) do
        if not self.searchIndex.byTag[tag] then
            self.searchIndex.byTag[tag] = {}
        end
        table.insert(self.searchIndex.byTag[tag], asset.id)
    end

    -- Index by creator
    if not self.searchIndex.byCreator[asset.creator] then
        self.searchIndex.byCreator[asset.creator] = {}
    end
    table.insert(self.searchIndex.byCreator[asset.creator], asset.id)

    -- Index by date (monthly buckets)
    local monthKey = os.date("%Y-%m", asset.createdAt)
    if not self.searchIndex.byDate[monthKey] then
        self.searchIndex.byDate[monthKey] = {}
    end
    table.insert(self.searchIndex.byDate[monthKey], asset.id)
end

function AssetManager:deindexAsset(asset: AssetMetadata)
    -- Remove from all indexes
    local function removeFromIndex(index: any, key: any, assetId: string)
        if index[key] then
            local pos = table.find(index[key], assetId)
            if pos then
                table.remove(index[key], pos)
            end
        end
    end

    removeFromIndex(self.searchIndex.byType, asset.type, asset.id)
    removeFromIndex(self.searchIndex.byCategory, asset.category, asset.id)

    for _, tag in ipairs(asset.tags) do
        removeFromIndex(self.searchIndex.byTag, tag, asset.id)
    end

    removeFromIndex(self.searchIndex.byCreator, asset.creator, asset.id)

    local monthKey = os.date("%Y-%m", asset.createdAt)
    removeFromIndex(self.searchIndex.byDate, monthKey, asset.id)
end

function AssetManager:reindexAsset(asset: AssetMetadata)
    self:deindexAsset(asset)
    self:indexAsset(asset)
end

function AssetManager:buildSearchIndex()
    -- Clear existing index
    self.searchIndex = {
        byType = {},
        byCategory = {},
        byTag = {},
        byCreator = {},
        byDate = {}
    }

    -- Rebuild from all assets
    for _, asset in pairs(self.assets) do
        self:indexAsset(asset)
    end
end

function AssetManager:serializeInstance(instance: Instance): string
    -- Serialize instance to JSON-compatible format
    local data = {
        ClassName = instance.ClassName,
        Name = instance.Name,
        Properties = {},
        Children = {}
    }

    -- Serialize properties (simplified)
    local success, properties = pcall(function()
        local props = {}
        if instance:IsA("BasePart") then
            props.Position = {instance.Position.X, instance.Position.Y, instance.Position.Z}
            props.Size = {instance.Size.X, instance.Size.Y, instance.Size.Z}
            props.Color = {instance.Color.R, instance.Color.G, instance.Color.B}
            props.Material = instance.Material.Name
            props.Transparency = instance.Transparency
        elseif instance:IsA("Script") or instance:IsA("LocalScript") or instance:IsA("ModuleScript") then
            props.Source = instance.Source
        end
        return props
    end)

    if success then
        data.Properties = properties
    end

    -- Serialize children
    for _, child in ipairs(instance:GetChildren()) do
        table.insert(data.Children, self:serializeInstance(child))
    end

    return HttpService:JSONEncode(data)
end

function AssetManager:deserializeInstance(data: string): Instance?
    local success, parsed = pcall(function()
        return HttpService:JSONDecode(data)
    end)

    if not success then
        return nil
    end

    local function deserializeNode(node: any): Instance?
        local instance = Instance.new(node.ClassName)
        instance.Name = node.Name

        -- Apply properties
        for prop, value in pairs(node.Properties or {}) do
            pcall(function()
                if prop == "Position" then
                    instance.Position = Vector3.new(value[1], value[2], value[3])
                elseif prop == "Size" then
                    instance.Size = Vector3.new(value[1], value[2], value[3])
                elseif prop == "Color" then
                    instance.Color = Color3.new(value[1], value[2], value[3])
                elseif prop == "Material" then
                    instance.Material = Enum.Material[value]
                else
                    instance[prop] = value
                end
            end)
        end

        -- Deserialize children
        for _, childNode in ipairs(node.Children or {}) do
            local child = deserializeNode(childNode)
            if child then
                child.Parent = instance
            end
        end

        return instance
    end

    return deserializeNode(parsed)
end

function AssetManager:calculateSize(instance: Instance): number
    -- Estimate size in bytes
    local size = 100 -- Base size

    -- Add for properties
    size = size + 50

    -- Add for children
    for _, child in ipairs(instance:GetDescendants()) do
        size = size + 100

        if child:IsA("Script") or child:IsA("LocalScript") or child:IsA("ModuleScript") then
            size = size + #(child.Source or "")
        end
    end

    return size
end

function AssetManager:generateChecksum(instance: Instance): string
    -- Simple checksum based on instance properties
    local str = instance.ClassName .. instance.Name

    if instance:IsA("Script") or instance:IsA("LocalScript") or instance:IsA("ModuleScript") then
        str = str .. (instance.Source or "")
    end

    -- Basic hash
    local hash = 0
    for i = 1, #str do
        hash = (hash * 31 + string.byte(str, i)) % 2147483647
    end

    return tostring(hash)
end

function AssetManager:shouldRegenerateThumbnail(assetType: AssetType): boolean
    -- Determine if thumbnail should be regenerated
    local visualTypes = {
        "Model", "Part", "MeshPart", "Union",
        "GUI", "SurfaceGui", "BillboardGui",
        "ParticleEmitter", "Beam", "Trail"
    }

    return table.find(visualTypes, assetType) ~= nil
end

function AssetManager:trackUsage(assetId: string)
    -- Track asset usage for popularity
    if not self.stats.recentlyUsed then
        self.stats.recentlyUsed = {}
    end

    -- Add to recently used
    table.insert(self.stats.recentlyUsed, 1, {
        assetId = assetId,
        timestamp = os.time()
    })

    -- Keep only last 100
    if #self.stats.recentlyUsed > 100 then
        table.remove(self.stats.recentlyUsed)
    end

    -- Update popularity score
    if not self.stats.popular then
        self.stats.popular = {}
    end

    self.stats.popular[assetId] = (self.stats.popular[assetId] or 0) + 1
end

function AssetManager:getAssetIds(): {string}
    local ids = {}
    for assetId in pairs(self.assets) do
        table.insert(ids, assetId)
    end
    return ids
end

function AssetManager:syncAssetToBackend(asset: AssetMetadata)
    task.spawn(function()
        HttpService:RequestAsync({
            Url = self.config.backendUrl .. "/api/assets",
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json",
                ["Authorization"] = "Bearer " .. (self.config.authToken or "")
            },
            Body = HttpService:JSONEncode(asset)
        })
    end)
end

function AssetManager:deleteAssetFromBackend(assetId: string)
    task.spawn(function()
        HttpService:RequestAsync({
            Url = self.config.backendUrl .. "/api/assets/" .. assetId,
            Method = "DELETE",
            Headers = {
                ["Authorization"] = "Bearer " .. (self.config.authToken or "")
            }
        })
    end)
end

function AssetManager:updateAssetMetadata(assetId: string, metadata: any)
    local asset = self.assets[assetId]
    if not asset then
        return
    end

    -- Update fields
    for key, value in pairs(metadata) do
        asset[key] = value
    end

    asset.modifiedAt = os.time()

    -- Reindex if needed
    self:reindexAsset(asset)

    self.eventEmitter:emit("assetMetadataUpdated", asset)
end

function AssetManager:startAutoSave()
    task.spawn(function()
        while true do
            task.wait(30) -- Save every 30 seconds
            self:saveLocalAssets()
        end
    end)
end

function AssetManager:getStatistics()
    return {
        totalAssets = self.stats.totalAssets,
        totalSize = self.stats.totalSize,
        totalVersions = self.stats.totalVersions,
        totalCollections = 0,
        recentlyUsed = #self.stats.recentlyUsed,
        byType = {},
        byCategory = {}
    }
end

function AssetManager:exportAsset(assetId: string, format: string?): string?
    local instance, metadata = self:getAsset(assetId)
    if not instance then
        return nil
    end

    format = format or "rbxm"

    if format == "rbxm" then
        -- Export as Roblox model (would need actual implementation)
        return self:serializeInstance(instance)
    elseif format == "json" then
        return HttpService:JSONEncode({
            metadata = metadata,
            data = self:serializeInstance(instance)
        })
    else
        return nil
    end
end

function AssetManager:importAsset(data: string, format: string?): string?
    format = format or "json"

    if format == "json" then
        local success, parsed = pcall(function()
            return HttpService:JSONDecode(data)
        end)

        if success and parsed.data then
            local instance = self:deserializeInstance(parsed.data)
            if instance then
                return self:createAsset(instance, parsed.metadata)
            end
        end
    end

    return nil
end

function AssetManager:cleanup()
    -- Save before cleanup
    self:saveLocalAssets()

    -- Clear caches
    self.thumbnails = {}

    -- Clear search index
    self.searchIndex = {
        byType = {},
        byCategory = {},
        byTag = {},
        byCreator = {},
        byDate = {}
    }

    print("[AssetManager] Cleanup completed")
end

return AssetManager