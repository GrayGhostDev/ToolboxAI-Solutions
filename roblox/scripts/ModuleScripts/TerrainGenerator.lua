--[[
    ToolboxAI Terrain Generator Module
    Version: 1.0.0
    Description: Generates educational terrain based on AI-generated specifications
                 Supports various terrain types, materials, and generation methods
--]]

local TerrainGenerator = {}
TerrainGenerator.__index = TerrainGenerator

-- Services
local workspace = game:GetService("Workspace")
local RunService = game:GetService("RunService")

-- Configuration
local CONFIG = {
    DEFAULT_MATERIAL = Enum.Material.Grass,
    DEFAULT_RESOLUTION = 4,
    MAX_REGION_SIZE = 2048,
    CHUNK_SIZE = 64,
    MATERIALS_MAP = {
        ["grass"] = Enum.Material.Grass,
        ["rock"] = Enum.Material.Rock,
        ["sand"] = Enum.Material.Sand,
        ["water"] = Enum.Material.Water,
        ["snow"] = Enum.Material.Snow,
        ["ice"] = Enum.Material.Ice,
        ["mud"] = Enum.Material.Mud,
        ["ground"] = Enum.Material.Ground,
        ["leafygrass"] = Enum.Material.LeafyGrass,
        ["concrete"] = Enum.Material.Concrete,
        ["cobblestone"] = Enum.Material.Cobblestone,
        ["brick"] = Enum.Material.Brick,
        ["woodplanks"] = Enum.Material.WoodPlanks,
        ["slate"] = Enum.Material.Slate,
        ["limestone"] = Enum.Material.Limestone,
        ["granite"] = Enum.Material.Granite,
        ["pavement"] = Enum.Material.Pavement,
        ["sandstone"] = Enum.Material.Sandstone,
        ["basalt"] = Enum.Material.Basalt,
        ["cracked_lava"] = Enum.Material.CrackedLava,
        ["glacier"] = Enum.Material.Glacier,
        ["asphalt"] = Enum.Material.Asphalt,
        ["salt"] = Enum.Material.Salt
    }
}

-- Constructor
function TerrainGenerator.new()
    local self = setmetatable({}, TerrainGenerator)
    self.terrain = workspace.Terrain
    self.generatedRegions = {}
    self.isGenerating = false
    return self
end

-- Clear existing terrain
function TerrainGenerator:clear()
    self.terrain:Clear()
    self.generatedRegions = {}
end

-- Generate terrain from data
function TerrainGenerator:generate(terrainData)
    if self.isGenerating then
        warn("Terrain generation already in progress")
        return false
    end
    
    self.isGenerating = true
    local success = false
    
    -- Determine generation method
    if terrainData.clear_existing then
        self:clear()
    end
    
    if terrainData.regions then
        success = self:generateRegions(terrainData.regions)
    elseif terrainData.heightmap then
        success = self:generateHeightmap(terrainData.heightmap)
    elseif terrainData.biomes then
        success = self:generateBiomes(terrainData.biomes)
    elseif terrainData.shapes then
        success = self:generateShapes(terrainData.shapes)
    else
        warn("No valid terrain generation method specified")
    end
    
    self.isGenerating = false
    return success
end

-- Generate terrain regions
function TerrainGenerator:generateRegions(regions)
    local generatedCount = 0
    
    for _, region in ipairs(regions) do
        local success = pcall(function()
            local material = self:getMaterial(region.material)
            local position = Vector3.new(
                region.position and region.position.x or 0,
                region.position and region.position.y or 0,
                region.position and region.position.z or 0
            )
            local size = Vector3.new(
                region.size and region.size.x or 4,
                region.size and region.size.y or 4,
                region.size and region.size.z or 4
            )
            
            -- Create region
            local minPoint = position - size/2
            local maxPoint = position + size/2
            
            -- Align to voxel grid (4x4x4)
            minPoint = Vector3.new(
                math.floor(minPoint.X/4)*4,
                math.floor(minPoint.Y/4)*4,
                math.floor(minPoint.Z/4)*4
            )
            maxPoint = Vector3.new(
                math.ceil(maxPoint.X/4)*4,
                math.ceil(maxPoint.Y/4)*4,
                math.ceil(maxPoint.Z/4)*4
            )
            
            local regionObj = Region3.new(minPoint, maxPoint)
            regionObj = regionObj:ExpandToGrid(4)
            
            self.terrain:FillBlock(
                CFrame.new((minPoint + maxPoint)/2),
                maxPoint - minPoint,
                material
            )
            
            generatedCount = generatedCount + 1
            table.insert(self.generatedRegions, {
                position = position,
                size = size,
                material = material
            })
        end)
        
        if not success then
            warn("Failed to generate region:", region)
        end
    end
    
    return generatedCount > 0
end

-- Generate terrain from heightmap
function TerrainGenerator:generateHeightmap(heightmapData)
    local size = heightmapData.size or {x = 100, y = 50, z = 100}
    local resolution = heightmapData.resolution or 4
    local scale = heightmapData.scale or 1
    local materials = heightmapData.materials or {}
    
    -- Generate base terrain
    local position = Vector3.new(
        heightmapData.position and heightmapData.position.x or 0,
        heightmapData.position and heightmapData.position.y or 0,
        heightmapData.position and heightmapData.position.z or 0
    )
    
    -- Create heightmap grid
    for x = 0, size.x, resolution do
        for z = 0, size.z, resolution do
            -- Calculate height using noise or provided data
            local height = self:calculateHeight(x, z, heightmapData)
            
            -- Determine material based on height
            local material = self:getMaterialByHeight(height, materials)
            
            -- Fill terrain voxel
            local voxelPos = position + Vector3.new(x, 0, z)
            local voxelSize = Vector3.new(resolution, height * scale, resolution)
            
            self.terrain:FillBlock(
                CFrame.new(voxelPos + voxelSize/2),
                voxelSize,
                material
            )
        end
        
        -- Yield periodically to prevent lag
        if x % (resolution * 10) == 0 then
            RunService.Heartbeat:Wait()
        end
    end
    
    return true
end

-- Generate biome-based terrain
function TerrainGenerator:generateBiomes(biomes)
    local generatedCount = 0
    
    for _, biome in ipairs(biomes) do
        local success = pcall(function()
            if biome.type == "forest" then
                self:generateForest(biome)
            elseif biome.type == "desert" then
                self:generateDesert(biome)
            elseif biome.type == "ocean" then
                self:generateOcean(biome)
            elseif biome.type == "mountains" then
                self:generateMountains(biome)
            elseif biome.type == "plains" then
                self:generatePlains(biome)
            elseif biome.type == "tundra" then
                self:generateTundra(biome)
            elseif biome.type == "cave" then
                self:generateCave(biome)
            else
                warn("Unknown biome type:", biome.type)
                return
            end
            generatedCount = generatedCount + 1
        end)
        
        if not success then
            warn("Failed to generate biome:", biome.type)
        end
    end
    
    return generatedCount > 0
end

-- Generate terrain shapes
function TerrainGenerator:generateShapes(shapes)
    local generatedCount = 0
    
    for _, shape in ipairs(shapes) do
        local success = pcall(function()
            local material = self:getMaterial(shape.material)
            local position = Vector3.new(
                shape.position and shape.position.x or 0,
                shape.position and shape.position.y or 0,
                shape.position and shape.position.z or 0
            )
            
            if shape.type == "sphere" then
                self.terrain:FillBall(
                    position,
                    shape.radius or 10,
                    material
                )
            elseif shape.type == "block" or shape.type == "cube" then
                local size = Vector3.new(
                    shape.size and shape.size.x or 10,
                    shape.size and shape.size.y or 10,
                    shape.size and shape.size.z or 10
                )
                self.terrain:FillBlock(
                    CFrame.new(position),
                    size,
                    material
                )
            elseif shape.type == "wedge" then
                local size = Vector3.new(
                    shape.size and shape.size.x or 10,
                    shape.size and shape.size.y or 10,
                    shape.size and shape.size.z or 10
                )
                self.terrain:FillWedge(
                    CFrame.new(position) * CFrame.Angles(
                        shape.rotation and math.rad(shape.rotation.x) or 0,
                        shape.rotation and math.rad(shape.rotation.y) or 0,
                        shape.rotation and math.rad(shape.rotation.z) or 0
                    ),
                    size,
                    material
                )
            elseif shape.type == "cylinder" then
                -- Approximate cylinder with multiple spheres
                local height = shape.height or 20
                local radius = shape.radius or 10
                local steps = math.ceil(height / 4)
                
                for i = 0, steps do
                    local y = position.Y + (i * height / steps)
                    self.terrain:FillBall(
                        Vector3.new(position.X, y, position.Z),
                        radius,
                        material
                    )
                end
            end
            
            generatedCount = generatedCount + 1
        end)
        
        if not success then
            warn("Failed to generate shape:", shape.type)
        end
    end
    
    return generatedCount > 0
end

-- Helper function to get material enum
function TerrainGenerator:getMaterial(materialName)
    if not materialName then
        return CONFIG.DEFAULT_MATERIAL
    end
    
    if type(materialName) == "string" then
        local material = CONFIG.MATERIALS_MAP[materialName:lower()]
        return material or CONFIG.DEFAULT_MATERIAL
    end
    
    return CONFIG.DEFAULT_MATERIAL
end

-- Calculate height for heightmap
function TerrainGenerator:calculateHeight(x, z, heightmapData)
    if heightmapData.heights and heightmapData.heights[x] and heightmapData.heights[x][z] then
        return heightmapData.heights[x][z]
    end
    
    -- Use Perlin noise as fallback
    local frequency = heightmapData.frequency or 0.05
    local amplitude = heightmapData.amplitude or 20
    local octaves = heightmapData.octaves or 3
    
    local height = 0
    local maxValue = 0
    local amp = 1
    
    for i = 1, octaves do
        height = height + math.noise(x * frequency, z * frequency, heightmapData.seed or 0) * amp
        maxValue = maxValue + amp
        amp = amp * 0.5
        frequency = frequency * 2
    end
    
    height = (height / maxValue) * amplitude + (heightmapData.baseHeight or 10)
    return math.max(1, height)
end

-- Get material based on height
function TerrainGenerator:getMaterialByHeight(height, materials)
    materials = materials or {}
    
    -- Default height-based materials
    if height < 5 then
        return self:getMaterial(materials.low or "sand")
    elseif height < 15 then
        return self:getMaterial(materials.medium or "grass")
    elseif height < 30 then
        return self:getMaterial(materials.high or "rock")
    else
        return self:getMaterial(materials.peak or "snow")
    end
end

-- Biome generation functions
function TerrainGenerator:generateForest(biome)
    local center = Vector3.new(
        biome.center and biome.center.x or 0,
        biome.center and biome.center.y or 0,
        biome.center and biome.center.z or 0
    )
    local radius = biome.radius or 50
    
    -- Generate forest floor
    self.terrain:FillBlock(
        CFrame.new(center),
        Vector3.new(radius * 2, 4, radius * 2),
        Enum.Material.LeafyGrass
    )
    
    -- Add hills
    for i = 1, biome.hillCount or 3 do
        local hillPos = center + Vector3.new(
            math.random(-radius, radius),
            2,
            math.random(-radius, radius)
        )
        self.terrain:FillBall(
            hillPos,
            math.random(10, 20),
            Enum.Material.Grass
        )
    end
end

function TerrainGenerator:generateDesert(biome)
    local center = Vector3.new(
        biome.center and biome.center.x or 0,
        biome.center and biome.center.y or 0,
        biome.center and biome.center.z or 0
    )
    local radius = biome.radius or 50
    
    -- Generate sandy base
    self.terrain:FillBlock(
        CFrame.new(center),
        Vector3.new(radius * 2, 4, radius * 2),
        Enum.Material.Sand
    )
    
    -- Add dunes
    for i = 1, biome.duneCount or 5 do
        local dunePos = center + Vector3.new(
            math.random(-radius, radius),
            2,
            math.random(-radius, radius)
        )
        self.terrain:FillBall(
            dunePos,
            math.random(8, 15),
            Enum.Material.Sand
        )
    end
    
    -- Add occasional rock formations
    for i = 1, biome.rockCount or 2 do
        local rockPos = center + Vector3.new(
            math.random(-radius, radius),
            5,
            math.random(-radius, radius)
        )
        self.terrain:FillBlock(
            CFrame.new(rockPos) * CFrame.Angles(
                math.rad(math.random(0, 45)),
                math.rad(math.random(0, 360)),
                math.rad(math.random(0, 45))
            ),
            Vector3.new(
                math.random(5, 10),
                math.random(10, 20),
                math.random(5, 10)
            ),
            Enum.Material.Sandstone
        )
    end
end

function TerrainGenerator:generateOcean(biome)
    local center = Vector3.new(
        biome.center and biome.center.x or 0,
        biome.center and biome.center.y or 0,
        biome.center and biome.center.z or 0
    )
    local radius = biome.radius or 100
    local depth = biome.depth or 30
    
    -- Generate ocean floor
    self.terrain:FillBlock(
        CFrame.new(center - Vector3.new(0, depth/2, 0)),
        Vector3.new(radius * 2, 4, radius * 2),
        Enum.Material.Sand
    )
    
    -- Fill with water
    self.terrain:FillBlock(
        CFrame.new(center),
        Vector3.new(radius * 2, depth, radius * 2),
        Enum.Material.Water
    )
    
    -- Add underwater features
    if biome.hasReef then
        for i = 1, biome.reefCount or 3 do
            local reefPos = center + Vector3.new(
                math.random(-radius/2, radius/2),
                -depth/2 + 5,
                math.random(-radius/2, radius/2)
            )
            self.terrain:FillBall(
                reefPos,
                math.random(5, 10),
                Enum.Material.Rock
            )
        end
    end
end

function TerrainGenerator:generateMountains(biome)
    local center = Vector3.new(
        biome.center and biome.center.x or 0,
        biome.center and biome.center.y or 0,
        biome.center and biome.center.z or 0
    )
    local radius = biome.radius or 75
    local height = biome.height or 100
    
    -- Generate mountain base
    self.terrain:FillBlock(
        CFrame.new(center),
        Vector3.new(radius * 2, 10, radius * 2),
        Enum.Material.Rock
    )
    
    -- Create mountain peaks
    for i = 1, biome.peakCount or 3 do
        local peakPos = center + Vector3.new(
            math.random(-radius/2, radius/2),
            0,
            math.random(-radius/2, radius/2)
        )
        
        -- Layer approach for realistic mountains
        local currentHeight = height
        local currentRadius = radius/2
        
        while currentHeight > 10 and currentRadius > 5 do
            self.terrain:FillBall(
                peakPos + Vector3.new(0, currentHeight/2, 0),
                currentRadius,
                currentHeight > height * 0.7 and Enum.Material.Snow or Enum.Material.Rock
            )
            currentHeight = currentHeight * 0.7
            currentRadius = currentRadius * 0.8
            peakPos = peakPos + Vector3.new(
                math.random(-5, 5),
                0,
                math.random(-5, 5)
            )
        end
    end
end

function TerrainGenerator:generatePlains(biome)
    local center = Vector3.new(
        biome.center and biome.center.x or 0,
        biome.center and biome.center.y or 0,
        biome.center and biome.center.z or 0
    )
    local radius = biome.radius or 75
    
    -- Generate flat grassland
    self.terrain:FillBlock(
        CFrame.new(center),
        Vector3.new(radius * 2, 4, radius * 2),
        Enum.Material.Grass
    )
    
    -- Add gentle rolling hills
    for i = 1, biome.hillCount or 2 do
        local hillPos = center + Vector3.new(
            math.random(-radius, radius),
            0,
            math.random(-radius, radius)
        )
        self.terrain:FillBall(
            hillPos,
            math.random(15, 25),
            Enum.Material.LeafyGrass
        )
    end
    
    -- Add occasional water features
    if biome.hasWater then
        local waterPos = center + Vector3.new(
            math.random(-radius/2, radius/2),
            -2,
            math.random(-radius/2, radius/2)
        )
        self.terrain:FillBall(
            waterPos,
            math.random(10, 20),
            Enum.Material.Water
        )
    end
end

function TerrainGenerator:generateTundra(biome)
    local center = Vector3.new(
        biome.center and biome.center.x or 0,
        biome.center and biome.center.y or 0,
        biome.center and biome.center.z or 0
    )
    local radius = biome.radius or 75
    
    -- Generate frozen ground
    self.terrain:FillBlock(
        CFrame.new(center),
        Vector3.new(radius * 2, 4, radius * 2),
        Enum.Material.Snow
    )
    
    -- Add ice patches
    for i = 1, biome.iceCount or 5 do
        local icePos = center + Vector3.new(
            math.random(-radius, radius),
            1,
            math.random(-radius, radius)
        )
        self.terrain:FillBall(
            icePos,
            math.random(8, 15),
            Enum.Material.Glacier
        )
    end
    
    -- Add snow drifts
    for i = 1, biome.driftCount or 3 do
        local driftPos = center + Vector3.new(
            math.random(-radius, radius),
            2,
            math.random(-radius, radius)
        )
        self.terrain:FillBall(
            driftPos,
            math.random(5, 12),
            Enum.Material.Snow
        )
    end
end

function TerrainGenerator:generateCave(biome)
    local center = Vector3.new(
        biome.center and biome.center.x or 0,
        biome.center and biome.center.y or 10,
        biome.center and biome.center.z or 0
    )
    local radius = biome.radius or 30
    
    -- Create cave shell
    self.terrain:FillBall(
        center,
        radius + 10,
        Enum.Material.Rock
    )
    
    -- Hollow out cave interior
    self.terrain:FillBall(
        center,
        radius,
        Enum.Material.Air
    )
    
    -- Add cave features
    if biome.hasStalactites then
        for i = 1, biome.stalactiteCount or 5 do
            local stalPos = center + Vector3.new(
                math.random(-radius/2, radius/2),
                radius - 5,
                math.random(-radius/2, radius/2)
            )
            self.terrain:FillWedge(
                CFrame.new(stalPos) * CFrame.Angles(math.pi, 0, 0),
                Vector3.new(3, math.random(5, 10), 3),
                Enum.Material.Rock
            )
        end
    end
    
    -- Add floor detail
    self.terrain:FillBlock(
        CFrame.new(center - Vector3.new(0, radius - 2, 0)),
        Vector3.new(radius * 2, 4, radius * 2),
        Enum.Material.Ground
    )
end

-- Get terrain statistics
function TerrainGenerator:getStatistics()
    local stats = {
        regionsGenerated = #self.generatedRegions,
        totalVolume = 0,
        materialsUsed = {}
    }
    
    for _, region in ipairs(self.generatedRegions) do
        local volume = region.size.X * region.size.Y * region.size.Z
        stats.totalVolume = stats.totalVolume + volume
        
        local materialName = tostring(region.material)
        stats.materialsUsed[materialName] = (stats.materialsUsed[materialName] or 0) + 1
    end
    
    return stats
end

-- Export terrain data (for saving/loading)
function TerrainGenerator:exportData()
    return {
        regions = self.generatedRegions,
        timestamp = os.time(),
        statistics = self:getStatistics()
    }
end

return TerrainGenerator