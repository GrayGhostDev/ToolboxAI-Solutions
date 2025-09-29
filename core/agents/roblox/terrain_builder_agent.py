"""
RobloxTerrainBuilder Agent - Dynamic terrain and environment generation

Generates Roblox terrain using the Terrain API with procedural generation
algorithms optimized for educational environments.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import random
import math

from ..base_agent import BaseAgent, AgentConfig, AgentState, TaskResult

logger = logging.getLogger(__name__)


class TerrainType:
    """Roblox terrain material types"""
    GRASS = "Grass"
    SAND = "Sand"
    ROCK = "Rock"
    GROUND = "Ground"
    WATER = "Water"
    SNOW = "Snow"
    ICE = "Ice"
    SANDSTONE = "Sandstone"
    MUD = "Mud"
    BASALT = "Basalt"
    CONCRETE = "Concrete"
    GLACIER = "Glacier"
    PAVEMENT = "Pavement"
    COBBLESTONE = "Cobblestone"
    BRICK = "Brick"
    WOODPLANKS = "WoodPlanks"
    SLATE = "Slate"
    LIMESTONE = "Limestone"
    ASPHALT = "Asphalt"
    SALT = "Salt"
    LEAFYGRASS = "LeafyGrass"


class RobloxTerrainBuilderAgent(BaseAgent):
    """
    Agent responsible for generating Roblox terrain and environments.
    
    Capabilities:
    - Procedural terrain generation
    - Theme-based environment creation
    - Educational landmark placement
    - Performance optimization
    - Interactive element integration
    - Terrain painting and sculpting
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if not config:
            config = AgentConfig(
                name="RobloxTerrainBuilder",
                model="gpt-3.5-turbo",
                temperature=0.6,
                system_prompt=self._get_terrain_prompt()
            )
        super().__init__(config)
        
        # Terrain generation templates
        self.terrain_templates = {
            "space": self._generate_space_terrain,
            "underwater": self._generate_underwater_terrain,
            "medieval": self._generate_medieval_terrain,
            "modern_city": self._generate_city_terrain,
            "fantasy": self._generate_fantasy_terrain,
            "jungle": self._generate_jungle_terrain,
            "desert": self._generate_desert_terrain,
            "arctic": self._generate_arctic_terrain,
            "laboratory": self._generate_lab_terrain,
            "classroom": self._generate_classroom_terrain
        }
    
    def _get_terrain_prompt(self) -> str:
        """Get specialized terrain generation prompt"""
        return """You are a Roblox Terrain Builder specializing in educational environment creation.
        
Your responsibilities:
- Generate engaging 3D terrain using Roblox Terrain API
- Create theme-appropriate environments
- Place educational landmarks and points of interest
- Optimize for performance and playability
- Add interactive terrain features
- Ensure accessibility and navigation
- Balance aesthetics with functionality

Focus on creating immersive worlds that enhance learning experiences.
"""
    
    async def _process_task(self, state: AgentState) -> Any:
        """Process terrain generation task"""
        context = state["context"]
        
        theme = context.get("theme", "classroom")
        world_size = context.get("world_size", "medium")
        educational_elements = context.get("educational_elements", [])
        
        # Generate base terrain
        terrain_data = await self._generate_base_terrain(theme, world_size)
        
        # Add educational landmarks
        landmarks = await self._add_educational_landmarks(terrain_data, educational_elements)
        
        # Optimize terrain
        optimized = self._optimize_terrain(terrain_data)
        
        # Generate Luau script
        terrain_script = self._generate_terrain_script(optimized, landmarks)
        
        return {
            "terrain_data": optimized,
            "landmarks": landmarks,
            "luau_script": terrain_script,
            "metadata": {
                "theme": theme,
                "size": world_size,
                "materials_used": self._get_materials_list(optimized),
                "performance_score": self._calculate_performance_score(optimized)
            }
        }
    
    async def _generate_base_terrain(self, theme: str, world_size: str) -> Dict[str, Any]:
        """Generate base terrain for theme"""
        
        # Get size parameters
        size_params = self._get_size_parameters(world_size)
        
        # Generate terrain using template
        if theme in self.terrain_templates:
            terrain_data = self.terrain_templates[theme](size_params)
        else:
            terrain_data = self._generate_default_terrain(size_params)
        
        return terrain_data
    
    def _get_size_parameters(self, world_size: str) -> Dict[str, int]:
        """Get terrain size parameters"""
        sizes = {
            "small": {"width": 512, "height": 256, "depth": 512},
            "medium": {"width": 1024, "height": 512, "depth": 1024},
            "large": {"width": 2048, "height": 1024, "depth": 2048}
        }
        return sizes.get(world_size, sizes["medium"])
    
    def _generate_space_terrain(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate space-themed terrain"""
        return {
            "base_material": TerrainType.SLATE,
            "regions": [
                {
                    "name": "lunar_surface",
                    "material": TerrainType.SAND,
                    "position": [0, 0, 0],
                    "size": [size["width"], 50, size["depth"]],
                    "noise": {"frequency": 0.02, "amplitude": 20}
                },
                {
                    "name": "craters",
                    "type": "negative_spheres",
                    "count": random.randint(5, 15),
                    "radius_range": [20, 100]
                },
                {
                    "name": "space_station_platform",
                    "material": TerrainType.CONCRETE,
                    "position": [size["width"]//2, 100, size["depth"]//2],
                    "size": [200, 20, 200]
                }
            ],
            "lighting": "dark_with_stars",
            "atmosphere": "none",
            "gravity": 0.3
        }
    
    def _generate_underwater_terrain(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate underwater terrain"""
        return {
            "base_material": TerrainType.SAND,
            "regions": [
                {
                    "name": "ocean_floor",
                    "material": TerrainType.SAND,
                    "position": [0, 0, 0],
                    "size": [size["width"], 100, size["depth"]],
                    "noise": {"frequency": 0.03, "amplitude": 30}
                },
                {
                    "name": "coral_reef",
                    "material": TerrainType.ROCK,
                    "clusters": 20,
                    "cluster_size": [30, 40, 30]
                },
                {
                    "name": "water_volume",
                    "material": TerrainType.WATER,
                    "position": [0, 100, 0],
                    "size": [size["width"], size["height"]-100, size["depth"]]
                }
            ],
            "lighting": "underwater_caustics",
            "atmosphere": "foggy",
            "water_color": [0, 0.5, 0.8]
        }
    
    def _generate_medieval_terrain(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate medieval terrain"""
        return {
            "base_material": TerrainType.GRASS,
            "regions": [
                {
                    "name": "rolling_hills",
                    "material": TerrainType.GRASS,
                    "position": [0, 0, 0],
                    "size": [size["width"], 200, size["depth"]],
                    "noise": {"frequency": 0.01, "amplitude": 50}
                },
                {
                    "name": "castle_foundation",
                    "material": TerrainType.ROCK,
                    "position": [size["width"]//2, 150, size["depth"]//2],
                    "size": [300, 100, 300]
                },
                {
                    "name": "moat",
                    "material": TerrainType.WATER,
                    "type": "ring",
                    "center": [size["width"]//2, 50, size["depth"]//2],
                    "radius": 200,
                    "width": 30,
                    "depth": 20
                },
                {
                    "name": "forest_area",
                    "material": TerrainType.LEAFYGRASS,
                    "position": [0, 50, 0],
                    "size": [size["width"]//3, 100, size["depth"]]
                }
            ],
            "lighting": "medieval_torch",
            "atmosphere": "misty"
        }
    
    def _generate_city_terrain(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate modern city terrain"""
        return {
            "base_material": TerrainType.CONCRETE,
            "regions": [
                {
                    "name": "city_blocks",
                    "material": TerrainType.CONCRETE,
                    "grid": True,
                    "block_size": [100, 0, 100],
                    "street_width": 20,
                    "material_street": TerrainType.ASPHALT
                },
                {
                    "name": "park_area",
                    "material": TerrainType.GRASS,
                    "position": [size["width"]//4, 0, size["depth"]//4],
                    "size": [200, 10, 200]
                },
                {
                    "name": "water_feature",
                    "material": TerrainType.WATER,
                    "position": [size["width"]//4, 0, size["depth"]//4],
                    "size": [50, 5, 50]
                }
            ],
            "lighting": "urban_night",
            "atmosphere": "clear"
        }
    
    def _generate_fantasy_terrain(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate fantasy terrain"""
        return {
            "base_material": TerrainType.GRASS,
            "regions": [
                {
                    "name": "enchanted_forest",
                    "material": TerrainType.LEAFYGRASS,
                    "position": [0, 0, 0],
                    "size": [size["width"], 150, size["depth"]],
                    "noise": {"frequency": 0.02, "amplitude": 40}
                },
                {
                    "name": "floating_islands",
                    "material": TerrainType.ROCK,
                    "type": "floating",
                    "count": 5,
                    "height_range": [200, 400],
                    "size_range": [50, 150]
                },
                {
                    "name": "magic_crystals",
                    "material": TerrainType.GLACIER,
                    "type": "scattered",
                    "count": 20,
                    "size_range": [5, 20]
                },
                {
                    "name": "mystic_lake",
                    "material": TerrainType.WATER,
                    "position": [size["width"]//2, 50, size["depth"]//2],
                    "size": [150, 30, 150],
                    "glow": True
                }
            ],
            "lighting": "magical_glow",
            "atmosphere": "sparkles",
            "special_effects": ["floating_particles", "light_beams"]
        }
    
    def _generate_jungle_terrain(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate jungle terrain"""
        return {
            "base_material": TerrainType.MUD,
            "regions": [
                {
                    "name": "jungle_floor",
                    "material": TerrainType.MUD,
                    "position": [0, 0, 0],
                    "size": [size["width"], 100, size["depth"]],
                    "noise": {"frequency": 0.04, "amplitude": 20}
                },
                {
                    "name": "canopy_layer",
                    "material": TerrainType.LEAFYGRASS,
                    "position": [0, 100, 0],
                    "size": [size["width"], 50, size["depth"]],
                    "density": 0.8
                },
                {
                    "name": "river",
                    "material": TerrainType.WATER,
                    "type": "winding",
                    "start": [0, 30, size["depth"]//2],
                    "end": [size["width"], 30, size["depth"]//2],
                    "width": 30,
                    "depth": 10
                },
                {
                    "name": "temple_ruins",
                    "material": TerrainType.SANDSTONE,
                    "position": [size["width"]//3, 50, size["depth"]//3],
                    "size": [100, 80, 100]
                }
            ],
            "lighting": "filtered_sunlight",
            "atmosphere": "humid",
            "ambient_sounds": ["birds", "water", "insects"]
        }
    
    def _generate_desert_terrain(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate desert terrain"""
        return {
            "base_material": TerrainType.SAND,
            "regions": [
                {
                    "name": "sand_dunes",
                    "material": TerrainType.SAND,
                    "position": [0, 0, 0],
                    "size": [size["width"], 150, size["depth"]],
                    "noise": {"frequency": 0.01, "amplitude": 60}
                },
                {
                    "name": "oasis",
                    "material": TerrainType.WATER,
                    "position": [size["width"]//2, 20, size["depth"]//2],
                    "size": [80, 10, 80]
                },
                {
                    "name": "oasis_grass",
                    "material": TerrainType.GRASS,
                    "position": [size["width"]//2-40, 30, size["depth"]//2-40],
                    "size": [160, 5, 160]
                },
                {
                    "name": "rock_formations",
                    "material": TerrainType.SANDSTONE,
                    "type": "pillars",
                    "count": 10,
                    "height_range": [50, 150],
                    "radius_range": [10, 30]
                }
            ],
            "lighting": "harsh_sun",
            "atmosphere": "heat_shimmer",
            "weather": "sandstorm_possible"
        }
    
    def _generate_arctic_terrain(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate arctic terrain"""
        return {
            "base_material": TerrainType.SNOW,
            "regions": [
                {
                    "name": "snow_field",
                    "material": TerrainType.SNOW,
                    "position": [0, 0, 0],
                    "size": [size["width"], 100, size["depth"]],
                    "noise": {"frequency": 0.02, "amplitude": 30}
                },
                {
                    "name": "ice_formations",
                    "material": TerrainType.ICE,
                    "type": "scattered",
                    "count": 15,
                    "size_range": [20, 60]
                },
                {
                    "name": "frozen_lake",
                    "material": TerrainType.ICE,
                    "position": [size["width"]//2, 30, size["depth"]//2],
                    "size": [200, 5, 200]
                },
                {
                    "name": "glacier",
                    "material": TerrainType.GLACIER,
                    "position": [0, 50, 0],
                    "size": [size["width"]//3, 200, size["depth"]//3]
                }
            ],
            "lighting": "arctic_sun",
            "atmosphere": "clear_cold",
            "weather": "snow_particles"
        }
    
    def _generate_lab_terrain(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate laboratory terrain"""
        return {
            "base_material": TerrainType.CONCRETE,
            "regions": [
                {
                    "name": "lab_floor",
                    "material": TerrainType.CONCRETE,
                    "position": [0, 0, 0],
                    "size": [size["width"], 10, size["depth"]],
                    "smooth": True
                },
                {
                    "name": "test_areas",
                    "material": TerrainType.PAVEMENT,
                    "grid": True,
                    "cell_size": [100, 0, 100],
                    "padding": 10
                },
                {
                    "name": "hazard_zone",
                    "material": TerrainType.BASALT,
                    "position": [size["width"]*0.7, 0, size["depth"]*0.7],
                    "size": [150, 10, 150],
                    "warning_stripes": True
                }
            ],
            "lighting": "fluorescent",
            "atmosphere": "sterile",
            "special_features": ["observation_deck", "emergency_exits"]
        }
    
    def _generate_classroom_terrain(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate classroom terrain"""
        return {
            "base_material": TerrainType.WOODPLANKS,
            "regions": [
                {
                    "name": "classroom_floor",
                    "material": TerrainType.WOODPLANKS,
                    "position": [0, 0, 0],
                    "size": [size["width"], 10, size["depth"]]
                },
                {
                    "name": "playground",
                    "material": TerrainType.GRASS,
                    "position": [size["width"]*0.6, 0, 0],
                    "size": [size["width"]*0.4, 10, size["depth"]]
                },
                {
                    "name": "sandbox",
                    "material": TerrainType.SAND,
                    "position": [size["width"]*0.7, 0, size["depth"]*0.2],
                    "size": [50, 5, 50]
                }
            ],
            "lighting": "classroom_bright",
            "atmosphere": "comfortable"
        }
    
    def _generate_default_terrain(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate default terrain"""
        return {
            "base_material": TerrainType.GRASS,
            "regions": [
                {
                    "name": "default_terrain",
                    "material": TerrainType.GRASS,
                    "position": [0, 0, 0],
                    "size": [size["width"], 100, size["depth"]],
                    "noise": {"frequency": 0.02, "amplitude": 30}
                }
            ],
            "lighting": "default",
            "atmosphere": "clear"
        }
    
    async def _add_educational_landmarks(self, terrain_data: Dict[str, Any], 
                                        educational_elements: List[str]) -> List[Dict[str, Any]]:
        """Add educational landmarks to terrain"""
        landmarks = []
        
        for element in educational_elements:
            landmark = {
                "name": element,
                "type": self._determine_landmark_type(element),
                "position": self._find_suitable_position(terrain_data),
                "size": self._determine_landmark_size(element),
                "interactive": True,
                "educational_content": element
            }
            landmarks.append(landmark)
        
        return landmarks
    
    def _determine_landmark_type(self, element: str) -> str:
        """Determine landmark type from educational element"""
        element_lower = element.lower()
        
        if "station" in element_lower:
            return "learning_station"
        elif "puzzle" in element_lower:
            return "puzzle_area"
        elif "exhibit" in element_lower:
            return "exhibit"
        elif "lab" in element_lower:
            return "laboratory"
        elif "library" in element_lower:
            return "library"
        else:
            return "interactive_object"
    
    def _find_suitable_position(self, terrain_data: Dict[str, Any]) -> List[float]:
        """Find suitable position for landmark"""
        # Simple positioning algorithm
        regions = terrain_data.get("regions", [])
        if regions:
            main_region = regions[0]
            size = main_region.get("size", [1024, 512, 1024])
            return [
                random.uniform(size[0]*0.2, size[0]*0.8),
                100,  # Default height
                random.uniform(size[2]*0.2, size[2]*0.8)
            ]
        return [512, 100, 512]
    
    def _determine_landmark_size(self, element: str) -> List[float]:
        """Determine landmark size"""
        if "large" in element.lower() or "big" in element.lower():
            return [100, 50, 100]
        elif "small" in element.lower() or "tiny" in element.lower():
            return [20, 10, 20]
        else:
            return [50, 25, 50]
    
    def _optimize_terrain(self, terrain_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize terrain for performance"""
        optimized = terrain_data.copy()
        
        # Reduce polygon count in distant areas
        optimized["lod_levels"] = 3
        optimized["streaming_enabled"] = True
        optimized["chunk_size"] = 64
        
        # Optimize materials
        optimized["material_optimization"] = {
            "merge_similar": True,
            "reduce_texture_size": True,
            "cache_materials": True
        }
        
        return optimized
    
    def _generate_terrain_script(self, terrain_data: Dict[str, Any], 
                                landmarks: List[Dict[str, Any]]) -> str:
        """Generate Luau script for terrain creation"""
        
        script = """-- Roblox Terrain Generation Script
-- Generated by RobloxTerrainBuilder Agent

local Terrain = workspace.Terrain
local Region3 = Region3
local Vector3 = Vector3
local CFrame = CFrame
local Enum = Enum

-- Clear existing terrain
Terrain:Clear()

-- Function to generate terrain region
local function generateRegion(regionData)
    local position = Vector3.new(
        regionData.position[1], 
        regionData.position[2], 
        regionData.position[3]
    )
    local size = Vector3.new(
        regionData.size[1], 
        regionData.size[2], 
        regionData.size[3]
    )
    
    local region = Region3.new(position, position + size)
    region = region:ExpandToGrid(4)
    
    -- Fill with material
    local material = Enum.Material[regionData.material]
    Terrain:FillBlock(
        CFrame.new(position + size/2),
        size,
        material
    )
    
    -- Apply noise if specified
    if regionData.noise then
        -- Apply Perlin noise for realistic terrain
        local resolution = 4
        local noiseScale = regionData.noise.frequency or 0.02
        local amplitude = regionData.noise.amplitude or 30
        
        -- This would be expanded with actual noise generation
    end
end

-- Generate all regions
"""
        
        # Add region generation code
        for region in terrain_data.get("regions", []):
            region_code = f"""
generateRegion({{
    position = {{{region['position'][0]}, {region['position'][1]}, {region['position'][2]}}},
    size = {{{region['size'][0]}, {region['size'][1]}, {region['size'][2]}}},
    material = "{region['material']}"
}})
"""
            script += region_code
        
        # Add landmark placement
        script += "\n-- Place educational landmarks\n"
        for landmark in landmarks:
            landmark_code = f"""
-- Landmark: {landmark['name']}
local landmark{landmarks.index(landmark)} = Instance.new("Part")
landmark{landmarks.index(landmark)}.Name = "{landmark['name']}"
landmark{landmarks.index(landmark)}.Position = Vector3.new({landmark['position'][0]}, {landmark['position'][1]}, {landmark['position'][2]})
landmark{landmarks.index(landmark)}.Size = Vector3.new({landmark['size'][0]}, {landmark['size'][1]}, {landmark['size'][2]})
landmark{landmarks.index(landmark)}.Anchored = true
landmark{landmarks.index(landmark)}.Parent = workspace
"""
            script += landmark_code
        
        # Add lighting and atmosphere
        script += f"""
-- Configure lighting
game.Lighting.Brightness = 2
game.Lighting.OutdoorAmbient = Color3.fromRGB(128, 128, 128)
game.Lighting.TimeOfDay = "14:00:00"

-- Set atmosphere
local atmosphere = game.Lighting.Atmosphere or Instance.new("Atmosphere")
atmosphere.Density = {terrain_data.get('atmosphere', {}).get('density', 0.3)}
atmosphere.Parent = game.Lighting

print("Terrain generation complete!")
"""
        
        return script
    
    def _get_materials_list(self, terrain_data: Dict[str, Any]) -> List[str]:
        """Get list of materials used"""
        materials = set()
        for region in terrain_data.get("regions", []):
            materials.add(region.get("material", "Unknown"))
        return list(materials)
    
    def _calculate_performance_score(self, terrain_data: Dict[str, Any]) -> float:
        """Calculate terrain performance score"""
        score = 100.0
        
        # Penalize for too many regions
        regions_count = len(terrain_data.get("regions", []))
        if regions_count > 10:
            score -= (regions_count - 10) * 2
        
        # Bonus for optimization features
        if terrain_data.get("streaming_enabled"):
            score += 10
        if terrain_data.get("lod_levels", 0) > 1:
            score += 5
        
        return max(0, min(100, score))