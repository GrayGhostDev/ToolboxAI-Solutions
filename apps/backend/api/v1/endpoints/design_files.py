"""
Design Files API Endpoints

Provides REST API endpoints for processing design files and scanning the design folder.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query, Path as PathParam
from pydantic import BaseModel

from apps.backend.services.design_file_converter import design_file_converter
from apps.backend.services.design_folder_scanner import design_folder_scanner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/design", tags=["design-files"])


# Request/Response Models
class DesignFileProcessRequest(BaseModel):
    file_path: str
    include_content: bool = True


class DesignFileProcessResponse(BaseModel):
    success: bool
    file_path: str
    file_name: str
    file_type: str
    content: Optional[str] = None
    relative_path: Optional[str] = None
    error: Optional[str] = None


class DesignFolderScanResponse(BaseModel):
    success: bool
    design_root: str
    summary: Dict[str, Any]
    categories: Dict[str, List[Dict[str, Any]]]
    folder_structure: Dict[str, Any]
    file_contents: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class DesignFileSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None


class DesignFileSearchResponse(BaseModel):
    success: bool
    query: str
    category: Optional[str]
    results: List[Dict[str, Any]]
    total_results: int


# API Endpoints


@router.post("/process-file", response_model=DesignFileProcessResponse)
async def process_design_file(request: DesignFileProcessRequest):
    """
    Process a single design file and return readable content.
    Output is automatically saved to the images folder.

    Supports: .fig, .sketch, .xd, .blend, .obj, .png, .jpg, .mp4, .txt
    """
    try:
        from apps.backend.services.enhanced_design_parser import enhanced_design_parser

        # Use enhanced parser with images folder output
        result = await enhanced_design_parser.parse_design_file(request.file_path, save_output=True)

        return DesignFileProcessResponse(
            success=result["success"],
            file_path=result.get("file_path", request.file_path),
            file_name=result.get("file_name", ""),
            file_type=result.get("file_type", ""),
            content=str(result.get("parsed_data", "")),
            relative_path=result.get("output_file"),
            error=result.get("error"),
        )
    except Exception as e:
        logger.error(f"Error processing design file {request.file_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan-folder", response_model=DesignFolderScanResponse)
async def scan_design_folder(
    include_content: bool = Query(True, description="Include file contents in response"),
    folder_path: Optional[str] = Query(
        None, description="Specific folder to scan (relative to design root)"
    ),
):
    """
    Scan the design folder and return organized file information.

    Args:
        include_content: Whether to include file contents (may be large)
        folder_path: Specific subfolder to scan (optional)
    """
    try:
        if folder_path:
            result = await design_folder_scanner.get_folder_contents(folder_path)
            if not result["success"]:
                raise HTTPException(status_code=404, detail=result["error"])

            # Convert to scan format
            return DesignFolderScanResponse(
                success=True,
                design_root=str(design_folder_scanner.design_root),
                summary={
                    "total_files": result["file_count"],
                    "by_category": {},
                    "by_folder": {folder_path: result["file_count"]},
                    "processed_files": result["file_count"],
                    "errors": 0,
                },
                categories={"files": result["files"], "folders": result["folders"]},
                folder_structure={},
                file_contents=None,
            )
        else:
            result = await design_folder_scanner.scan_design_folder(include_content)

            return DesignFolderScanResponse(
                success=result["success"],
                design_root=result.get("design_root", ""),
                summary=result.get("summary", {}),
                categories=result.get("categories", {}),
                folder_structure=result.get("folder_structure", {}),
                file_contents=result.get("file_contents"),
                error=result.get("error"),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning design folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_design_summary():
    """
    Get a human-readable summary of the design folder.
    """
    try:
        summary = await design_folder_scanner.get_design_summary()
        return {"success": True, "summary": summary}
    except Exception as e:
        logger.error(f"Error getting design summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=DesignFileSearchResponse)
async def search_design_files(request: DesignFileSearchRequest):
    """
    Search for files in the design folder.

    Args:
        query: Search term (searches filename and path)
        category: Optional category filter (design_files, 3d_files, images, videos, text_files, other)
    """
    try:
        results = await design_folder_scanner.search_design_files(request.query, request.category)

        return DesignFileSearchResponse(
            success=True,
            query=request.query,
            category=request.category,
            results=results,
            total_results=len(results),
        )
    except Exception as e:
        logger.error(f"Error searching design files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/folder/{folder_path:path}")
async def get_folder_contents(folder_path: str):
    """
    Get contents of a specific folder in the design directory.

    Args:
        folder_path: Path to folder (relative to design root)
    """
    try:
        result = await design_folder_scanner.get_folder_contents(folder_path)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting folder contents for {folder_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_file_categories():
    """
    Get available file categories and their supported extensions.
    """
    return {"success": True, "categories": design_folder_scanner.file_categories}


@router.get("/supported-extensions")
async def get_supported_extensions():
    """
    Get list of all supported file extensions.
    """
    extensions = []
    for category_extensions in design_folder_scanner.file_categories.values():
        extensions.extend(category_extensions)

    return {
        "success": True,
        "extensions": sorted(set(extensions)),
        "total_count": len(set(extensions)),
    }


# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Check if design file processing services are healthy.
    """
    try:
        # Test basic functionality
        test_result = await design_folder_scanner.get_design_summary()

        return {
            "success": True,
            "status": "healthy",
            "services": {
                "design_file_converter": "available",
                "design_folder_scanner": "available",
            },
            "design_root": str(design_folder_scanner.design_root),
            "design_root_exists": design_folder_scanner.design_root.exists(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"success": False, "status": "unhealthy", "error": str(e)}
