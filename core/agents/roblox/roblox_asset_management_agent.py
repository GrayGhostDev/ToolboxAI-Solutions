"""
Roblox Asset Management Agent

AI agent for managing Roblox assets, optimization, and resource tracking.
Provides comprehensive asset catalog management, performance optimization,
and usage analytics for educational content.

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from core.agents.base_agent import AgentConfig, BaseAgent, TaskResult

logger = logging.getLogger(__name__)


class AssetType(Enum):
    """Types of Roblox assets"""
    MODEL = "model"
    MESH = "mesh"
    TEXTURE = "texture"
    SOUND = "sound"
    ANIMATION = "animation"
    SCRIPT = "script"
    DECAL = "decal"
    VIDEO = "video"


class OptimizationLevel(Enum):
    """Asset optimization levels"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class AssetMetadata:
    """Metadata for Roblox assets"""
    asset_id: str
    asset_type: AssetType
    name: str
    size_bytes: int
    created_at: datetime
    last_modified: datetime
    usage_count: int = 0
    performance_score: float = 0.0
    optimization_level: OptimizationLevel = OptimizationLevel.CONSERVATIVE
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class RobloxAssetManagementAgent(BaseAgent):
    """
    AI agent for managing Roblox assets and resources.

    Capabilities:
    - Asset catalog management
    - Model and sound optimization
    - Resource usage tracking
    - Performance monitoring
    - Automated asset validation
    """

    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="roblox_asset_management_agent",
                model="gpt-4-turbo-preview",
                temperature=0.3,
                max_tokens=4096
            )
        super().__init__(config)

        # Initialize asset catalog
        self.asset_catalog: Dict[str, AssetMetadata] = {}
        self.catalog_index = {
            "by_type": {},
            "by_tag": {},
            "by_usage": {}
        }

        # Optimization engine configuration
        self.optimization_engine = {
            "texture_compression": True,
            "model_simplification": True,
            "sound_compression": True,
            "animation_optimization": True,
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "target_performance_score": 0.85
        }

        # Usage tracker
        self.usage_tracker = {
            "tracking_enabled": True,
            "analytics_window": 30,  # days
            "performance_thresholds": {
                "high_usage": 1000,
                "medium_usage": 100,
                "low_usage": 10
            }
        }

        logger.info("RobloxAssetManagementAgent initialized")

    async def _process_task(self, state) -> Any:
        """Process asset management tasks"""
        task_type = state.context.get("task_type", "optimize")

        if task_type == "optimize":
            return await self._optimize_assets(state.context)
        elif task_type == "catalog":
            return await self._manage_catalog(state.context)
        elif task_type == "track":
            return await self._track_usage(state.context)
        elif task_type == "validate":
            return await self._validate_assets(state.context)
        elif task_type == "analyze":
            return await self._analyze_performance(state.context)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _optimize_assets(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize asset usage and performance"""
        assets = context.get("assets", [])
        optimization_level = OptimizationLevel(context.get("optimization_level", "balanced"))

        optimization_results = {
            "optimized_assets": [],
            "performance_improvements": {},
            "size_reductions": {},
            "quality_metrics": {}
        }

        for asset_info in assets:
            asset_id = asset_info.get("asset_id")
            asset_type = AssetType(asset_info.get("type", "model"))

            # Perform optimization based on asset type
            if asset_type == AssetType.MODEL:
                optimization = await self._optimize_model(asset_info, optimization_level)
            elif asset_type == AssetType.TEXTURE:
                optimization = await self._optimize_texture(asset_info, optimization_level)
            elif asset_type == AssetType.SOUND:
                optimization = await self._optimize_sound(asset_info, optimization_level)
            else:
                optimization = await self._optimize_generic_asset(asset_info, optimization_level)

            optimization_results["optimized_assets"].append(optimization)

            # Track improvements
            if optimization.get("performance_improvement"):
                optimization_results["performance_improvements"][asset_id] = optimization["performance_improvement"]

            if optimization.get("size_reduction"):
                optimization_results["size_reductions"][asset_id] = optimization["size_reduction"]

            # Update catalog
            if asset_id in self.asset_catalog:
                self.asset_catalog[asset_id].performance_score = optimization.get("new_performance_score", 0.0)
                self.asset_catalog[asset_id].optimization_level = optimization_level

        # Generate optimization report
        optimization_results["summary"] = self._generate_optimization_summary(optimization_results)
        optimization_results["recommendations"] = await self._generate_optimization_recommendations(optimization_results)

        logger.info("Optimized %d assets with %s level", len(assets), optimization_level.value)
        return optimization_results

    async def _optimize_model(self, asset_info: Dict[str, Any], level: OptimizationLevel) -> Dict[str, Any]:
        """Optimize 3D model assets"""
        current_size = asset_info.get("size_bytes", 1000000)
        current_triangles = asset_info.get("triangle_count", 10000)

        # Optimization parameters based on level
        optimization_params = {
            OptimizationLevel.CONSERVATIVE: {"triangle_reduction": 0.1, "texture_compression": 0.2},
            OptimizationLevel.BALANCED: {"triangle_reduction": 0.3, "texture_compression": 0.5},
            OptimizationLevel.AGGRESSIVE: {"triangle_reduction": 0.5, "texture_compression": 0.7}
        }

        params = optimization_params[level]

        # Simulate optimization
        await asyncio.sleep(0.1)  # Simulate processing time

        new_triangles = int(current_triangles * (1 - params["triangle_reduction"]))
        new_size = int(current_size * (1 - params["texture_compression"]))

        return {
            "asset_id": asset_info.get("asset_id"),
            "type": "model",
            "optimization_level": level.value,
            "original_triangles": current_triangles,
            "optimized_triangles": new_triangles,
            "triangle_reduction": params["triangle_reduction"],
            "original_size": current_size,
            "optimized_size": new_size,
            "size_reduction": (current_size - new_size) / current_size,
            "performance_improvement": params["triangle_reduction"] * 0.8,
            "new_performance_score": 0.85 + (params["triangle_reduction"] * 0.1),
            "quality_retained": 1.0 - (params["triangle_reduction"] * 0.3)
        }

    async def _optimize_texture(self, asset_info: Dict[str, Any], level: OptimizationLevel) -> Dict[str, Any]:
        """Optimize texture assets"""
        current_size = asset_info.get("size_bytes", 500000)
        current_resolution = asset_info.get("resolution", "1024x1024")

        # Optimization parameters
        compression_rates = {
            OptimizationLevel.CONSERVATIVE: 0.2,
            OptimizationLevel.BALANCED: 0.4,
            OptimizationLevel.AGGRESSIVE: 0.6
        }

        compression_rate = compression_rates[level]

        await asyncio.sleep(0.05)  # Simulate processing

        new_size = int(current_size * (1 - compression_rate))

        return {
            "asset_id": asset_info.get("asset_id"),
            "type": "texture",
            "optimization_level": level.value,
            "original_size": current_size,
            "optimized_size": new_size,
            "size_reduction": compression_rate,
            "compression_format": "DXT5" if level == OptimizationLevel.AGGRESSIVE else "DXT1",
            "performance_improvement": compression_rate * 0.6,
            "new_performance_score": 0.8 + (compression_rate * 0.15),
            "quality_retained": 1.0 - (compression_rate * 0.2)
        }

    async def _optimize_sound(self, asset_info: Dict[str, Any], level: OptimizationLevel) -> Dict[str, Any]:
        """Optimize sound assets"""
        current_size = asset_info.get("size_bytes", 1000000)
        current_bitrate = asset_info.get("bitrate", 128)

        # Optimization parameters
        bitrate_reductions = {
            OptimizationLevel.CONSERVATIVE: 0.1,
            OptimizationLevel.BALANCED: 0.25,
            OptimizationLevel.AGGRESSIVE: 0.4
        }

        reduction = bitrate_reductions[level]

        await asyncio.sleep(0.05)  # Simulate processing

        new_bitrate = int(current_bitrate * (1 - reduction))
        new_size = int(current_size * (1 - reduction))

        return {
            "asset_id": asset_info.get("asset_id"),
            "type": "sound",
            "optimization_level": level.value,
            "original_size": current_size,
            "optimized_size": new_size,
            "original_bitrate": current_bitrate,
            "optimized_bitrate": new_bitrate,
            "size_reduction": reduction,
            "performance_improvement": reduction * 0.7,
            "new_performance_score": 0.8 + (reduction * 0.2),
            "quality_retained": 1.0 - (reduction * 0.15)
        }

    async def _optimize_generic_asset(self, asset_info: Dict[str, Any], level: OptimizationLevel) -> Dict[str, Any]:
        """Optimize generic assets"""
        current_size = asset_info.get("size_bytes", 100000)

        # Generic optimization
        reduction_rates = {
            OptimizationLevel.CONSERVATIVE: 0.1,
            OptimizationLevel.BALANCED: 0.2,
            OptimizationLevel.AGGRESSIVE: 0.3
        }

        reduction = reduction_rates[level]

        await asyncio.sleep(0.02)  # Simulate processing

        new_size = int(current_size * (1 - reduction))

        return {
            "asset_id": asset_info.get("asset_id"),
            "type": asset_info.get("type", "generic"),
            "optimization_level": level.value,
            "original_size": current_size,
            "optimized_size": new_size,
            "size_reduction": reduction,
            "performance_improvement": reduction * 0.5,
            "new_performance_score": 0.75 + (reduction * 0.1)
        }

    async def _manage_catalog(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage asset catalog and metadata"""
        action = context.get("action", "list")

        if action == "add":
            return await self._add_asset_to_catalog(context)
        elif action == "remove":
            return await self._remove_asset_from_catalog(context)
        elif action == "update":
            return await self._update_asset_metadata(context)
        elif action == "search":
            return await self._search_catalog(context)
        elif action == "list":
            return await self._list_catalog(context)
        else:
            raise ValueError(f"Unknown catalog action: {action}")

    async def _add_asset_to_catalog(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add new asset to catalog"""
        asset_data = context.get("asset_data", {})

        asset_metadata = AssetMetadata(
            asset_id=asset_data.get("asset_id", str(uuid.uuid4())),
            asset_type=AssetType(asset_data.get("type", "model")),
            name=asset_data.get("name", "Unnamed Asset"),
            size_bytes=asset_data.get("size_bytes", 0),
            created_at=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
            tags=asset_data.get("tags", [])
        )

        # Add to catalog
        self.asset_catalog[asset_metadata.asset_id] = asset_metadata

        # Update indexes
        self._update_catalog_indexes(asset_metadata)

        logger.info("Added asset %s to catalog", asset_metadata.name)

        return {
            "action": "asset_added",
            "asset_id": asset_metadata.asset_id,
            "catalog_size": len(self.asset_catalog)
        }

    async def _track_usage(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Track asset usage and performance metrics"""
        asset_id = context.get("asset_id")
        usage_data = context.get("usage_data", {})

        if asset_id and asset_id in self.asset_catalog:
            asset = self.asset_catalog[asset_id]

            # Update usage count
            asset.usage_count += usage_data.get("usage_increment", 1)

            # Update performance metrics
            if "performance_data" in usage_data:
                perf_data = usage_data["performance_data"]
                asset.performance_score = self._calculate_performance_score(perf_data)

            # Update last modified
            asset.last_modified = datetime.now(timezone.utc)

            # Generate usage analytics
            analytics = await self._generate_usage_analytics(asset_id, usage_data)

            logger.info("Updated usage tracking for asset %s", asset_id)

            return {
                "action": "usage_tracked",
                "asset_id": asset_id,
                "new_usage_count": asset.usage_count,
                "performance_score": asset.performance_score,
                "analytics": analytics
            }
        else:
            return {"error": f"Asset {asset_id} not found in catalog"}

    async def _validate_assets(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate assets for compliance and quality"""
        asset_ids = context.get("asset_ids", list(self.asset_catalog.keys()))
        validation_results = {
            "validated_assets": [],
            "validation_errors": [],
            "compliance_issues": [],
            "quality_scores": {}
        }

        for asset_id in asset_ids:
            if asset_id not in self.asset_catalog:
                validation_results["validation_errors"].append(f"Asset {asset_id} not found")
                continue

            asset = self.asset_catalog[asset_id]

            # Validate asset
            validation = await self._validate_single_asset(asset)
            validation_results["validated_assets"].append(validation)

            # Check compliance
            compliance = await self._check_asset_compliance(asset)
            if not compliance["compliant"]:
                validation_results["compliance_issues"].extend(compliance["issues"])

            # Calculate quality score
            quality_score = await self._calculate_asset_quality_score(asset)
            validation_results["quality_scores"][asset_id] = quality_score

        # Generate validation summary
        validation_results["summary"] = {
            "total_validated": len(validation_results["validated_assets"]),
            "errors": len(validation_results["validation_errors"]),
            "compliance_issues": len(validation_results["compliance_issues"]),
            "average_quality": sum(validation_results["quality_scores"].values()) / len(validation_results["quality_scores"]) if validation_results["quality_scores"] else 0
        }

        logger.info("Validated %d assets", len(validation_results["validated_assets"]))
        return validation_results

    async def _analyze_performance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze asset performance and generate insights"""
        analysis_type = context.get("analysis_type", "comprehensive")
        time_window = context.get("time_window_days", 30)

        performance_analysis = {
            "asset_performance": {},
            "usage_patterns": {},
            "optimization_opportunities": [],
            "recommendations": []
        }

        # Analyze each asset in catalog
        for asset_id, asset in self.asset_catalog.items():
            # Performance metrics
            performance_analysis["asset_performance"][asset_id] = {
                "performance_score": asset.performance_score,
                "usage_count": asset.usage_count,
                "size_efficiency": self._calculate_size_efficiency(asset),
                "optimization_potential": self._calculate_optimization_potential(asset)
            }

            # Usage patterns
            performance_analysis["usage_patterns"][asset_id] = {
                "usage_category": self._categorize_usage(asset.usage_count),
                "last_used": asset.last_modified.isoformat(),
                "usage_trend": self._calculate_usage_trend(asset)
            }

        # Identify optimization opportunities
        performance_analysis["optimization_opportunities"] = await self._identify_optimization_opportunities()

        # Generate recommendations
        performance_analysis["recommendations"] = await self._generate_performance_recommendations(performance_analysis)

        logger.info("Completed performance analysis for %d assets", len(self.asset_catalog))
        return performance_analysis

    def _calculate_performance_score(self, performance_data: Dict[str, Any]) -> float:
        """Calculate performance score based on metrics"""
        load_time = performance_data.get("load_time", 1.0)
        memory_usage = performance_data.get("memory_usage", 10.0)
        render_impact = performance_data.get("render_impact", 0.5)

        # Normalize metrics (lower is better for load_time and memory_usage)
        load_score = max(0, 1.0 - (load_time / 5.0))  # 5s max load time
        memory_score = max(0, 1.0 - (memory_usage / 100.0))  # 100MB max memory
        render_score = max(0, 1.0 - render_impact)  # Lower render impact is better

        # Weighted average
        performance_score = (load_score * 0.4 + memory_score * 0.3 + render_score * 0.3)

        return min(max(performance_score, 0.0), 1.0)

    def _calculate_size_efficiency(self, asset: AssetMetadata) -> float:
        """Calculate size efficiency score"""
        # Efficiency based on usage vs size
        if asset.size_bytes == 0:
            return 1.0

        usage_per_byte = asset.usage_count / asset.size_bytes

        # Normalize to 0-1 scale (higher usage per byte is better)
        max_efficiency = 0.001  # 1 usage per 1000 bytes is excellent
        efficiency = min(usage_per_byte / max_efficiency, 1.0)

        return efficiency

    def _calculate_optimization_potential(self, asset: AssetMetadata) -> float:
        """Calculate optimization potential for an asset"""
        # Higher potential for larger, less optimized assets
        size_factor = min(asset.size_bytes / (10 * 1024 * 1024), 1.0)  # 10MB as reference
        performance_factor = 1.0 - asset.performance_score
        usage_factor = min(asset.usage_count / 1000, 1.0)  # High usage = more optimization value

        potential = (size_factor * 0.4 + performance_factor * 0.4 + usage_factor * 0.2)

        return min(max(potential, 0.0), 1.0)

    def _categorize_usage(self, usage_count: int) -> str:
        """Categorize asset usage level"""
        thresholds = self.usage_tracker["performance_thresholds"]

        if usage_count >= thresholds["high_usage"]:
            return "high"
        elif usage_count >= thresholds["medium_usage"]:
            return "medium"
        elif usage_count >= thresholds["low_usage"]:
            return "low"
        else:
            return "unused"

    def _calculate_usage_trend(self, asset: AssetMetadata) -> str:
        """Calculate usage trend for an asset"""
        # Simplified trend calculation based on recent activity
        days_since_modified = (datetime.now(timezone.utc) - asset.last_modified).days

        if days_since_modified <= 7:
            return "increasing"
        elif days_since_modified <= 30:
            return "stable"
        else:
            return "declining"

    async def _identify_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify assets with high optimization potential"""
        opportunities = []

        for asset_id, asset in self.asset_catalog.items():
            potential = self._calculate_optimization_potential(asset)

            if potential > 0.6:  # High optimization potential
                opportunities.append({
                    "asset_id": asset_id,
                    "asset_name": asset.name,
                    "optimization_potential": potential,
                    "current_performance": asset.performance_score,
                    "size_bytes": asset.size_bytes,
                    "usage_count": asset.usage_count,
                    "recommended_action": self._recommend_optimization_action(asset, potential)
                })

        # Sort by optimization potential
        opportunities.sort(key=lambda x: x["optimization_potential"], reverse=True)

        return opportunities[:10]  # Return top 10 opportunities

    def _recommend_optimization_action(self, asset: AssetMetadata, potential: float) -> str:
        """Recommend specific optimization action"""
        if potential > 0.8:
            return "aggressive_optimization"
        elif potential > 0.6:
            return "balanced_optimization"
        elif potential > 0.4:
            return "conservative_optimization"
        else:
            return "monitor_usage"

    async def _generate_performance_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []

        # Analyze optimization opportunities
        opportunities = analysis.get("optimization_opportunities", [])
        if len(opportunities) > 5:
            recommendations.append(f"Consider optimizing {len(opportunities)} high-potential assets")

        # Analyze usage patterns
        usage_patterns = analysis.get("usage_patterns", {})
        unused_assets = sum(1 for pattern in usage_patterns.values() if pattern.get("usage_category") == "unused")
        if unused_assets > 10:
            recommendations.append(f"Remove or archive {unused_assets} unused assets")

        # Performance recommendations
        avg_performance = sum(perf.get("performance_score", 0) for perf in analysis.get("asset_performance", {}).values())
        avg_performance = avg_performance / len(analysis.get("asset_performance", {})) if analysis.get("asset_performance") else 0

        if avg_performance < 0.7:
            recommendations.append("Overall asset performance is below target - consider comprehensive optimization")

        # Size recommendations
        total_size = sum(asset.size_bytes for asset in self.asset_catalog.values())
        if total_size > 100 * 1024 * 1024:  # 100MB
            recommendations.append("Total asset size exceeds recommended limit - implement aggressive compression")

        return recommendations

    def _generate_optimization_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization summary"""
        optimized_assets = results.get("optimized_assets", [])

        if not optimized_assets:
            return {"message": "No assets optimized"}

        total_size_reduction = sum(opt.get("size_reduction", 0) for opt in optimized_assets)
        avg_performance_improvement = sum(opt.get("performance_improvement", 0) for opt in optimized_assets) / len(optimized_assets)
        avg_quality_retained = sum(opt.get("quality_retained", 1.0) for opt in optimized_assets) / len(optimized_assets)

        return {
            "total_assets_optimized": len(optimized_assets),
            "average_size_reduction": total_size_reduction / len(optimized_assets),
            "average_performance_improvement": avg_performance_improvement,
            "average_quality_retained": avg_quality_retained,
            "optimization_success_rate": sum(1 for opt in optimized_assets if opt.get("performance_improvement", 0) > 0) / len(optimized_assets)
        }

    async def _generate_optimization_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on results"""
        recommendations = []

        summary = results.get("summary", {})

        if summary.get("average_performance_improvement", 0) > 0.3:
            recommendations.append("Excellent optimization results - consider applying to more assets")

        if summary.get("average_quality_retained", 1.0) < 0.8:
            recommendations.append("Quality retention is low - consider more conservative optimization")

        if summary.get("optimization_success_rate", 0) < 0.8:
            recommendations.append("Some optimizations failed - review asset types and parameters")

        return recommendations

    async def _validate_single_asset(self, asset: AssetMetadata) -> Dict[str, Any]:
        """Validate a single asset"""
        validation = {
            "asset_id": asset.asset_id,
            "valid": True,
            "issues": [],
            "warnings": []
        }

        # Size validation
        max_sizes = {
            AssetType.MODEL: 50 * 1024 * 1024,  # 50MB
            AssetType.TEXTURE: 10 * 1024 * 1024,  # 10MB
            AssetType.SOUND: 20 * 1024 * 1024,  # 20MB
        }

        max_size = max_sizes.get(asset.asset_type, 5 * 1024 * 1024)
        if asset.size_bytes > max_size:
            validation["issues"].append(f"Asset size {asset.size_bytes} exceeds limit {max_size}")
            validation["valid"] = False

        # Performance validation
        if asset.performance_score < 0.5:
            validation["warnings"].append("Low performance score - consider optimization")

        # Usage validation
        if asset.usage_count == 0:
            validation["warnings"].append("Asset has never been used - consider removal")

        return validation

    async def _check_asset_compliance(self, asset: AssetMetadata) -> Dict[str, Any]:
        """Check asset compliance with Roblox ToS and educational standards"""
        compliance = {
            "compliant": True,
            "issues": []
        }

        # Educational content compliance
        if asset.asset_type in [AssetType.TEXTURE, AssetType.DECAL]:
            # Check for educational appropriateness (simplified check)
            if any(tag in ["inappropriate", "violent", "adult"] for tag in asset.tags):
                compliance["compliant"] = False
                compliance["issues"].append("Content may not be appropriate for educational use")

        # Size compliance
        if asset.size_bytes > self.optimization_engine["max_file_size"]:
            compliance["issues"].append("Asset exceeds maximum file size limit")

        # Performance compliance
        if asset.performance_score < self.optimization_engine["target_performance_score"]:
            compliance["issues"].append("Asset performance below target threshold")

        return compliance

    async def _calculate_asset_quality_score(self, asset: AssetMetadata) -> float:
        """Calculate comprehensive quality score for an asset"""
        # Base score from performance
        quality_score = asset.performance_score * 0.4

        # Usage factor
        usage_factor = min(asset.usage_count / 1000, 1.0) * 0.3
        quality_score += usage_factor

        # Size efficiency factor
        size_efficiency = self._calculate_size_efficiency(asset) * 0.2
        quality_score += size_efficiency

        # Recency factor
        days_old = (datetime.now(timezone.utc) - asset.created_at).days
        recency_factor = max(0, 1.0 - (days_old / 365)) * 0.1  # Newer assets get slight bonus
        quality_score += recency_factor

        return min(max(quality_score, 0.0), 1.0)

    def _update_catalog_indexes(self, asset: AssetMetadata):
        """Update catalog indexes for efficient searching"""
        # Update type index
        if asset.asset_type.value not in self.catalog_index["by_type"]:
            self.catalog_index["by_type"][asset.asset_type.value] = []
        self.catalog_index["by_type"][asset.asset_type.value].append(asset.asset_id)

        # Update tag index
        for tag in asset.tags:
            if tag not in self.catalog_index["by_tag"]:
                self.catalog_index["by_tag"][tag] = []
            self.catalog_index["by_tag"][tag].append(asset.asset_id)

        # Update usage index
        usage_category = self._categorize_usage(asset.usage_count)
        if usage_category not in self.catalog_index["by_usage"]:
            self.catalog_index["by_usage"][usage_category] = []
        self.catalog_index["by_usage"][usage_category].append(asset.asset_id)

    async def _search_catalog(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search asset catalog with filters"""
        search_params = context.get("search_params", {})

        results = []
        for asset_id, asset in self.asset_catalog.items():
            if self._matches_search_criteria(asset, search_params):
                results.append({
                    "asset_id": asset_id,
                    "name": asset.name,
                    "type": asset.asset_type.value,
                    "size_bytes": asset.size_bytes,
                    "usage_count": asset.usage_count,
                    "performance_score": asset.performance_score,
                    "tags": asset.tags
                })

        # Sort by relevance (usage count and performance score)
        results.sort(key=lambda x: (x["usage_count"], x["performance_score"]), reverse=True)

        return {
            "search_results": results,
            "total_results": len(results),
            "search_params": search_params
        }

    def _matches_search_criteria(self, asset: AssetMetadata, criteria: Dict[str, Any]) -> bool:
        """Check if asset matches search criteria"""
        # Type filter
        if "asset_type" in criteria:
            if asset.asset_type.value != criteria["asset_type"]:
                return False

        # Tag filter
        if "tags" in criteria:
            required_tags = criteria["tags"]
            if not any(tag in asset.tags for tag in required_tags):
                return False

        # Size filter
        if "max_size" in criteria:
            if asset.size_bytes > criteria["max_size"]:
                return False

        # Performance filter
        if "min_performance" in criteria:
            if asset.performance_score < criteria["min_performance"]:
                return False

        # Usage filter
        if "min_usage" in criteria:
            if asset.usage_count < criteria["min_usage"]:
                return False

        return True

    async def _list_catalog(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """List catalog contents with pagination"""
        page = context.get("page", 1)
        page_size = context.get("page_size", 20)
        sort_by = context.get("sort_by", "usage_count")

        # Get all assets
        assets = list(self.asset_catalog.values())

        # Sort assets
        if sort_by == "usage_count":
            assets.sort(key=lambda x: x.usage_count, reverse=True)
        elif sort_by == "performance_score":
            assets.sort(key=lambda x: x.performance_score, reverse=True)
        elif sort_by == "size":
            assets.sort(key=lambda x: x.size_bytes, reverse=True)
        elif sort_by == "created_at":
            assets.sort(key=lambda x: x.created_at, reverse=True)

        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_assets = assets[start_idx:end_idx]

        return {
            "assets": [
                {
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "type": asset.asset_type.value,
                    "size_bytes": asset.size_bytes,
                    "usage_count": asset.usage_count,
                    "performance_score": asset.performance_score,
                    "created_at": asset.created_at.isoformat(),
                    "tags": asset.tags
                }
                for asset in page_assets
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_assets": len(assets),
                "total_pages": (len(assets) + page_size - 1) // page_size
            },
            "catalog_stats": {
                "total_assets": len(self.asset_catalog),
                "total_size": sum(asset.size_bytes for asset in self.asset_catalog.values()),
                "average_performance": sum(asset.performance_score for asset in self.asset_catalog.values()) / len(self.asset_catalog) if self.asset_catalog else 0
            }
        }

    async def _generate_usage_analytics(self, asset_id: str, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate usage analytics for an asset"""
        asset = self.asset_catalog.get(asset_id)
        if not asset:
            return {"error": "Asset not found"}

        analytics = {
            "usage_metrics": {
                "total_usage": asset.usage_count,
                "usage_category": self._categorize_usage(asset.usage_count),
                "usage_trend": self._calculate_usage_trend(asset),
                "usage_efficiency": self._calculate_size_efficiency(asset)
            },
            "performance_metrics": {
                "current_score": asset.performance_score,
                "optimization_potential": self._calculate_optimization_potential(asset),
                "quality_score": await self._calculate_asset_quality_score(asset)
            },
            "recommendations": []
        }

        # Generate specific recommendations
        if asset.usage_count == 0:
            analytics["recommendations"].append("Consider removing unused asset")
        elif asset.performance_score < 0.6:
            analytics["recommendations"].append("Optimize asset for better performance")
        elif asset.size_bytes > 10 * 1024 * 1024:
            analytics["recommendations"].append("Asset is large - consider compression")

        return analytics

    def get_agent_metrics(self) -> Dict[str, Any]:
        """Get comprehensive agent metrics"""
        return {
            "catalog_size": len(self.asset_catalog),
            "total_asset_size": sum(asset.size_bytes for asset in self.asset_catalog.values()),
            "average_performance_score": sum(asset.performance_score for asset in self.asset_catalog.values()) / len(self.asset_catalog) if self.asset_catalog else 0,
            "asset_type_distribution": {
                asset_type: len(assets) for asset_type, assets in self.catalog_index["by_type"].items()
            },
            "usage_distribution": {
                usage_level: len(assets) for usage_level, assets in self.catalog_index["by_usage"].items()
            },
            "optimization_opportunities": len([asset for asset in self.asset_catalog.values() if self._calculate_optimization_potential(asset) > 0.6])
        }
