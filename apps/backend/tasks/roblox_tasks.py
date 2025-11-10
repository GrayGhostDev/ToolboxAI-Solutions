"""
Roblox Integration Tasks
========================
Background tasks for Roblox environment synchronization and deployment
"""

import json
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional
from celery import shared_task
from celery.utils.log import get_task_logger
import httpx

from apps.backend.core.config import settings
from apps.backend.services.pusher import pusher_service as pusher_client
from apps.backend.services.roblox.service import RobloxService

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="tasks.sync_roblox_environment",
    max_retries=3,
    default_retry_delay=120,
    queue="roblox",
    priority=4,
)
def sync_roblox_environment(
    self, universe_id: str, place_id: Optional[str] = None, sync_type: str = "incremental"
) -> Dict[str, Any]:
    """
    Sync educational content with Roblox environment

    Args:
        universe_id: Roblox universe identifier
        place_id: Specific place to sync (optional)
        sync_type: Type of sync (incremental, full, assets_only)

    Returns:
        Sync operation results
    """
    try:
        task_id = self.request.id
        start_time = datetime.utcnow()

        # Initialize Roblox service
        roblox_service = RobloxService()

        # Send initial progress
        if pusher_client:
            pusher_client.trigger(
                f"roblox-sync-{universe_id}",
                "sync-started",
                {
                    "task_id": task_id,
                    "universe_id": universe_id,
                    "sync_type": sync_type,
                    "timestamp": start_time.isoformat(),
                },
            )

        sync_results = {"scripts_synced": 0, "assets_synced": 0, "models_synced": 0, "errors": []}

        # Perform sync based on type
        if sync_type in ["full", "incremental"]:
            # Sync Luau scripts
            scripts_dir = os.path.join(settings.BASE_DIR, "roblox", "src")

            if os.path.exists(scripts_dir):
                for root, dirs, files in os.walk(scripts_dir):
                    for file in files:
                        if file.endswith((".lua", ".luau")):
                            filepath = os.path.join(root, file)
                            try:
                                # Read script content
                                with open(filepath, "r") as f:
                                    script_content = f.read()

                                # Determine script type from path
                                if "server" in root:
                                    script_type = "ServerScript"
                                elif "client" in root:
                                    script_type = "LocalScript"
                                else:
                                    script_type = "ModuleScript"

                                # Upload to Roblox
                                result = roblox_service.upload_script(
                                    universe_id=universe_id,
                                    script_name=file,
                                    script_content=script_content,
                                    script_type=script_type,
                                )

                                if result.get("success"):
                                    sync_results["scripts_synced"] += 1
                                    logger.info(f"Synced script: {file}")
                                else:
                                    sync_results["errors"].append(
                                        f"Failed to sync {file}: {result.get('error')}"
                                    )

                            except Exception as e:
                                logger.error(f"Error syncing script {file}: {e}")
                                sync_results["errors"].append(f"Script error {file}: {str(e)}")

        if sync_type in ["full", "assets_only"]:
            # Sync assets (models, textures, sounds)
            assets_dir = os.path.join(settings.BASE_DIR, "roblox", "assets")

            if os.path.exists(assets_dir):
                for asset_file in os.listdir(assets_dir):
                    if asset_file.endswith((".rbxm", ".rbxmx")):
                        filepath = os.path.join(assets_dir, asset_file)
                        try:
                            # Upload model asset
                            with open(filepath, "rb") as f:
                                asset_data = f.read()

                            result = roblox_service.upload_asset(
                                universe_id=universe_id,
                                asset_name=asset_file,
                                asset_data=asset_data,
                                asset_type="Model",
                            )

                            if result.get("success"):
                                sync_results["models_synced"] += 1
                                logger.info(f"Synced model: {asset_file}")
                            else:
                                sync_results["errors"].append(
                                    f"Failed to sync {asset_file}: {result.get('error')}"
                                )

                        except Exception as e:
                            logger.error(f"Error syncing asset {asset_file}: {e}")
                            sync_results["errors"].append(f"Asset error {asset_file}: {str(e)}")

        # Update DataStore with educational content metadata
        if sync_type == "full":
            try:
                from apps.backend.core.database import SessionLocal
                from database.models import EducationalContent

                with SessionLocal() as session:
                    # Get recent educational content
                    contents = (
                        session.query(EducationalContent)
                        .filter(EducationalContent.metadata.contains('"roblox_enabled": true'))
                        .limit(100)
                        .all()
                    )

                    content_manifest = []
                    for content in contents:
                        content_manifest.append(
                            {
                                "id": str(content.id),
                                "title": content.title,
                                "topic": content.topic,
                                "grade_level": content.grade_level,
                                "type": content.content_type,
                            }
                        )

                    # Update Roblox DataStore
                    result = roblox_service.update_datastore(
                        universe_id=universe_id,
                        key="educational_content_manifest",
                        value=json.dumps(content_manifest),
                    )

                    if result.get("success"):
                        logger.info(f"Updated DataStore with {len(content_manifest)} content items")
                    else:
                        sync_results["errors"].append(
                            f"DataStore update failed: {result.get('error')}"
                        )

            except Exception as e:
                logger.error(f"DataStore sync error: {e}")
                sync_results["errors"].append(f"DataStore error: {str(e)}")

        # Calculate sync duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Send completion notification
        if pusher_client:
            pusher_client.trigger(
                f"roblox-sync-{universe_id}",
                "sync-completed",
                {
                    "task_id": task_id,
                    "universe_id": universe_id,
                    "results": sync_results,
                    "duration": duration,
                    "timestamp": end_time.isoformat(),
                },
            )

        return {
            "status": "success",
            "task_id": task_id,
            "universe_id": universe_id,
            "sync_type": sync_type,
            "results": sync_results,
            "duration": duration,
            "timestamp": end_time.isoformat(),
        }

    except Exception as e:
        logger.error(f"Roblox sync failed: {e}")

        if pusher_client:
            pusher_client.trigger(
                f"roblox-sync-{universe_id}",
                "sync-failed",
                {"task_id": self.request.id, "error": str(e)},
            )

        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="tasks.deploy_to_roblox",
    max_retries=2,
    default_retry_delay=180,
    queue="roblox",
    priority=6,
)
def deploy_to_roblox(
    self, project_path: str, universe_id: str, deployment_type: str = "production"
) -> Dict[str, Any]:
    """
    Deploy complete project to Roblox using Rojo

    Args:
        project_path: Path to Rojo project
        universe_id: Target Roblox universe
        deployment_type: Type of deployment (production, staging, development)

    Returns:
        Deployment results
    """
    try:
        task_id = self.request.id

        # Validate project exists
        project_file = os.path.join(project_path, "default.project.json")
        if not os.path.exists(project_file):
            raise FileNotFoundError(f"Project file not found: {project_file}")

        # Build project with Rojo
        logger.info(f"Building Roblox project from {project_path}")

        with tempfile.NamedTemporaryFile(suffix=".rbxlx", delete=False) as build_file:
            build_output = build_file.name

            # Run Rojo build command
            build_cmd = ["rojo", "build", project_file, "--output", build_output]

            result = subprocess.run(build_cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise RuntimeError(f"Rojo build failed: {result.stderr}")

            logger.info(f"Project built successfully: {build_output}")

            # Deploy to Roblox based on deployment type
            roblox_service = RobloxService()

            deployment_config = {
                "production": {
                    "place_id": settings.ROBLOX_PRODUCTION_PLACE_ID,
                    "api_key": settings.ROBLOX_PRODUCTION_API_KEY,
                },
                "staging": {
                    "place_id": settings.ROBLOX_STAGING_PLACE_ID,
                    "api_key": settings.ROBLOX_STAGING_API_KEY,
                },
                "development": {
                    "place_id": settings.ROBLOX_DEV_PLACE_ID,
                    "api_key": settings.ROBLOX_DEV_API_KEY,
                },
            }

            config = deployment_config.get(deployment_type, deployment_config["development"])

            # Upload built place file
            with open(build_output, "rb") as f:
                place_data = f.read()

            upload_result = roblox_service.upload_place(
                universe_id=universe_id,
                place_id=config["place_id"],
                place_data=place_data,
                api_key=config["api_key"],
            )

            # Clean up temp file
            os.unlink(build_output)

            if not upload_result.get("success"):
                raise RuntimeError(f"Place upload failed: {upload_result.get('error')}")

            # Publish place if production deployment
            if deployment_type == "production":
                publish_result = roblox_service.publish_place(
                    universe_id=universe_id, place_id=config["place_id"]
                )

                if not publish_result.get("success"):
                    logger.warning(f"Place publish warning: {publish_result.get('error')}")

            deployment_info = {
                "status": "success",
                "task_id": task_id,
                "universe_id": universe_id,
                "place_id": config["place_id"],
                "deployment_type": deployment_type,
                "version": upload_result.get("version_number"),
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"Deployment completed: {deployment_info}")

            # Send notification
            if pusher_client:
                pusher_client.trigger("roblox-deployments", "deployment-complete", deployment_info)

            return deployment_info

    except Exception as e:
        logger.error(f"Roblox deployment failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="tasks.validate_roblox_assets",
    max_retries=2,
    default_retry_delay=60,
    queue="roblox",
    priority=2,
)
def validate_roblox_assets(self, asset_ids: List[str]) -> Dict[str, Any]:
    """
    Validate Roblox assets for compliance and quality

    Args:
        asset_ids: List of asset IDs to validate

    Returns:
        Validation results
    """
    try:
        roblox_service = RobloxService()
        validation_results = {"valid": [], "invalid": [], "warnings": []}

        for asset_id in asset_ids:
            try:
                # Get asset info
                asset_info = roblox_service.get_asset_info(asset_id)

                if not asset_info:
                    validation_results["invalid"].append(
                        {"id": asset_id, "reason": "Asset not found"}
                    )
                    continue

                # Validation checks
                issues = []

                # Check asset type
                if asset_info.get("type") not in ["Model", "Script", "Image", "Sound"]:
                    issues.append("Unsupported asset type")

                # Check size limits
                size_mb = asset_info.get("size_bytes", 0) / (1024 * 1024)
                if size_mb > 100:
                    issues.append(f"Asset too large: {size_mb:.2f} MB")

                # Check content rating
                if asset_info.get("content_rating") not in ["G", "PG"]:
                    issues.append("Content rating not suitable for educational use")

                # Check for malicious patterns in scripts
                if asset_info.get("type") == "Script":
                    script_content = roblox_service.get_script_content(asset_id)
                    if script_content:
                        # Check for dangerous patterns
                        dangerous_patterns = [
                            "loadstring",
                            "require(game:GetService",
                            "game.Players:ClearAllChildren()",
                            "while true do end",
                        ]

                        for pattern in dangerous_patterns:
                            if pattern in script_content:
                                issues.append(f"Dangerous pattern detected: {pattern}")

                # Categorize result
                if issues:
                    if len(issues) > 2:
                        validation_results["invalid"].append({"id": asset_id, "reasons": issues})
                    else:
                        validation_results["warnings"].append({"id": asset_id, "warnings": issues})
                else:
                    validation_results["valid"].append(asset_id)

                logger.info(f"Validated asset {asset_id}: {len(issues)} issues found")

            except Exception as e:
                logger.error(f"Error validating asset {asset_id}: {e}")
                validation_results["invalid"].append(
                    {"id": asset_id, "reason": f"Validation error: {str(e)}"}
                )

        summary = {
            "status": "success",
            "total_assets": len(asset_ids),
            "valid_count": len(validation_results["valid"]),
            "invalid_count": len(validation_results["invalid"]),
            "warning_count": len(validation_results["warnings"]),
            "results": validation_results,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Asset validation completed: {summary['valid_count']}/{summary['total_assets']} valid"
        )

        return summary

    except Exception as e:
        logger.error(f"Asset validation failed: {e}")
        raise self.retry(exc=e)
