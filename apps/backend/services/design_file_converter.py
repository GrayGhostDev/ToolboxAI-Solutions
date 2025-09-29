"""
Design File Converter Service

Handles conversion of design files (.fig, .sketch, .xd) and other design assets
to readable formats for chat processing.
"""

import asyncio
import json
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import subprocess
import os

logger = logging.getLogger(__name__)


def safe_json_serialize(data: Any, max_size: int = 50000) -> Any:
    """
    Safely serialize data for JSON, handling large content and encoding issues.

    Args:
        data: Data to serialize
        max_size: Maximum size in characters for string content

    Returns:
        JSON-safe version of the data
    """
    if isinstance(data, str):
        # Truncate large strings and ensure proper encoding
        if len(data) > max_size:
            data = data[:max_size] + "\n[Content truncated - too large]"
        # Ensure the string is properly encoded
        try:
            # Test if the string can be properly encoded as UTF-8
            data.encode("utf-8")
            return data
        except UnicodeEncodeError:
            # Replace problematic characters
            return data.encode("utf-8", errors="replace").decode("utf-8")
    elif isinstance(data, dict):
        return {k: safe_json_serialize(v, max_size) for k, v in data.items()}
    elif isinstance(data, list):
        return [safe_json_serialize(item, max_size) for item in data]
    elif isinstance(data, (bytes, bytearray)):
        # Convert binary data to base64 or skip it
        try:
            import base64

            return f"[Binary data: {len(data)} bytes]"
        except ImportError:
            return "[Binary data]"
    else:
        return data


class DesignFileConverter:
    """Converts design files to readable formats for chat processing"""

    def __init__(
        self,
        design_root: str = "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/design",
    ):
        self.design_root = Path(design_root)
        self.supported_extensions = {
            ".fig": self._convert_fig_file,
            ".sketch": self._convert_sketch_file,
            ".xd": self._convert_xd_file,
            ".blend": self._extract_blend_info,
            ".obj": self._extract_obj_info,
            ".png": self._extract_image_metadata,
            ".jpg": self._extract_image_metadata,
            ".jpeg": self._extract_image_metadata,
            ".mp4": self._extract_video_metadata,
            ".txt": self._read_text_file,
        }

    async def process_design_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Process any design file and return readable content"""
        file_path = Path(file_path)

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}", "content": None}

        extension = file_path.suffix.lower()

        if extension not in self.supported_extensions:
            return {
                "success": False,
                "error": f"Unsupported file type: {extension}",
                "content": None,
            }

        try:
            converter = self.supported_extensions[extension]
            result = await converter(file_path)

            # Safely serialize the result to prevent JSON encoding issues
            safe_result = safe_json_serialize(result)

            return {
                "success": True,
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_type": extension,
                "content": safe_result,
                "relative_path": (
                    str(file_path.relative_to(self.design_root))
                    if file_path.is_relative_to(self.design_root)
                    else str(file_path)
                ),
            }
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return {"success": False, "error": str(e), "content": None}

    async def scan_design_folder(
        self, folder_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """Scan entire design folder and process all supported files"""
        if folder_path is None:
            folder_path = self.design_root
        else:
            folder_path = Path(folder_path)

        if not folder_path.exists():
            return {"success": False, "error": f"Folder not found: {folder_path}", "files": []}

        results = []
        processed_count = 0
        error_count = 0

        # Recursively find all supported files
        for file_path in folder_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                result = await self.process_design_file(file_path)
                results.append(result)

                if result["success"]:
                    processed_count += 1
                else:
                    error_count += 1

        # Safely serialize all results to prevent JSON encoding issues
        safe_results = [safe_json_serialize(result) for result in results]

        return {
            "success": True,
            "folder_path": str(folder_path),
            "total_files": len(safe_results),
            "processed_count": processed_count,
            "error_count": error_count,
            "files": safe_results,
        }

    async def _convert_fig_file(self, file_path: Path) -> str:
        """Convert Figma .fig file to readable format"""
        try:
            # Try to use fig2sketch if available
            with tempfile.TemporaryDirectory() as temp_dir:
                sketch_path = Path(temp_dir) / "temp.sketch"

                # Convert fig to sketch
                result = await asyncio.create_subprocess_exec(
                    "fig2sketch",
                    str(file_path),
                    str(sketch_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await result.communicate()

                if result.returncode == 0 and sketch_path.exists():
                    # Convert sketch to JSON
                    return await self._convert_sketch_file(sketch_path)
                else:
                    # Fallback: extract basic info from fig file
                    return await self._extract_fig_basic_info(file_path)
        except FileNotFoundError:
            # fig2sketch not available, use fallback
            return await self._extract_fig_basic_info(file_path)
        except Exception as e:
            logger.warning(f"fig2sketch conversion failed: {e}")
            return await self._extract_fig_basic_info(file_path)

    async def _convert_sketch_file(self, file_path: Path) -> str:
        """Convert Sketch .sketch file to readable format"""
        try:
            # Try sketch-tool if available
            result = await asyncio.create_subprocess_exec(
                "sketch-tool",
                "dump",
                str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                return stdout.decode("utf-8")
            else:
                # Fallback: extract from ZIP structure
                return await self._extract_sketch_basic_info(file_path)
        except FileNotFoundError:
            # sketch-tool not available, use fallback
            return await self._extract_sketch_basic_info(file_path)
        except Exception as e:
            logger.warning(f"sketch-tool conversion failed: {e}")
            return await self._extract_sketch_basic_info(file_path)

    async def _convert_xd_file(self, file_path: Path) -> str:
        """Convert Adobe XD .xd file to readable format"""
        try:
            # XD files are ZIP archives
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                file_list = zip_ref.namelist()

                # Look for manifest and other important files
                manifest_content = ""
                if "manifest" in file_list:
                    manifest_content = zip_ref.read("manifest").decode("utf-8")

                # Look for artboards or pages
                artboard_files = [
                    f for f in file_list if "artboard" in f.lower() or "page" in f.lower()
                ]

                content = f"Adobe XD File: {file_path.name}\n"
                content += f"Files in archive: {len(file_list)}\n"
                content += f"Artboard/Page files: {len(artboard_files)}\n"

                if manifest_content:
                    content += f"\nManifest:\n{manifest_content}\n"

                if artboard_files:
                    content += f"\nArtboard files:\n" + "\n".join(
                        artboard_files[:10]
                    )  # Limit to first 10

                return content
        except Exception as e:
            return f"Adobe XD File: {file_path.name}\nError reading file: {str(e)}"

    async def _extract_blend_info(self, file_path: Path) -> str:
        """Extract information from Blender .blend file"""
        try:
            # Blender files are binary, but we can extract basic info
            stat = file_path.stat()
            content = f"Blender 3D File: {file_path.name}\n"
            content += f"Size: {stat.st_size} bytes\n"
            content += f"Type: 3D Model (.blend)\n"
            content += f"Description: 3D model file created with Blender\n"

            # Try to extract basic header info if possible
            try:
                with open(file_path, "rb") as f:
                    header = f.read(12)
                    if header.startswith(b"BLENDER"):
                        version = header[7:12].decode("ascii", errors="ignore")
                        content += f"Blender Version: {version}\n"
            except:
                pass

            return content
        except Exception as e:
            return f"Blender File: {file_path.name}\nError: {str(e)}"

    async def _extract_obj_info(self, file_path: Path) -> str:
        """Extract information from .obj 3D file"""
        try:
            content = f"3D Object File: {file_path.name}\n"

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            # Count different elements
            vertices = len([l for l in lines if l.startswith("v ")])
            faces = len([l for l in lines if l.startswith("f ")])
            normals = len([l for l in lines if l.startswith("vn ")])
            textures = len([l for l in lines if l.startswith("vt ")])

            content += f"Vertices: {vertices}\n"
            content += f"Faces: {faces}\n"
            content += f"Normals: {normals}\n"
            content += f"Texture coordinates: {textures}\n"

            # Look for material references
            materials = [l.strip() for l in lines if l.startswith("usemtl ")]
            if materials:
                content += f"Materials: {', '.join(materials[:5])}\n"  # First 5 materials

            return content
        except Exception as e:
            return f"3D Object File: {file_path.name}\nError: {str(e)}"

    async def _extract_image_metadata(self, file_path: Path) -> str:
        """Extract metadata from image files"""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS

            with Image.open(file_path) as img:
                metadata = {
                    "filename": file_path.name,
                    "format": img.format,
                    "mode": img.mode,
                    "size": f"{img.width}x{img.height}",
                    "width": img.width,
                    "height": img.height,
                }

                # Extract EXIF data if available
                if hasattr(img, "_getexif") and img._getexif():
                    exifdata = img._getexif()
                    exif = {}
                    for tag_id, value in exifdata.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif[tag] = value
                    metadata["exif"] = exif

                content = f"Image File: {file_path.name}\n"
                content += f"Format: {metadata['format']}\n"
                content += f"Dimensions: {metadata['size']}\n"
                content += f"Color Mode: {metadata['mode']}\n"

                if "exif" in metadata:
                    content += f"EXIF Data: Available\n"

                return content
        except ImportError:
            # PIL not available, basic info
            stat = file_path.stat()
            return f"Image File: {file_path.name}\nSize: {stat.st_size} bytes\nType: {file_path.suffix}"
        except Exception as e:
            return f"Image File: {file_path.name}\nError: {str(e)}"

    async def _extract_video_metadata(self, file_path: Path) -> str:
        """Extract metadata from video files"""
        try:
            # Try to use ffprobe if available
            result = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                data = json.loads(stdout.decode("utf-8"))
                format_info = data.get("format", {})
                streams = data.get("streams", [])

                content = f"Video File: {file_path.name}\n"
                content += f"Duration: {format_info.get('duration', 'Unknown')} seconds\n"
                content += f"Size: {format_info.get('size', 'Unknown')} bytes\n"
                content += f"Format: {format_info.get('format_name', 'Unknown')}\n"

                for stream in streams:
                    if stream.get("codec_type") == "video":
                        content += f"Video Codec: {stream.get('codec_name', 'Unknown')}\n"
                        content += (
                            f"Resolution: {stream.get('width', '?')}x{stream.get('height', '?')}\n"
                        )
                        content += f"Frame Rate: {stream.get('r_frame_rate', 'Unknown')}\n"
                    elif stream.get("codec_type") == "audio":
                        content += f"Audio Codec: {stream.get('codec_name', 'Unknown')}\n"
                        content += f"Sample Rate: {stream.get('sample_rate', 'Unknown')} Hz\n"

                return content
            else:
                # Fallback: basic file info
                stat = file_path.stat()
                return f"Video File: {file_path.name}\nSize: {stat.st_size} bytes\nType: {file_path.suffix}"
        except FileNotFoundError:
            # ffprobe not available, basic info
            stat = file_path.stat()
            return f"Video File: {file_path.name}\nSize: {stat.st_size} bytes\nType: {file_path.suffix}"
        except Exception as e:
            return f"Video File: {file_path.name}\nError: {str(e)}"

    async def _read_text_file(self, file_path: Path) -> str:
        """Read text files directly"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Limit content size to prevent JSON encoding issues
            max_content_size = 10000  # 10KB limit
            if len(content) > max_content_size:
                content = content[:max_content_size] + "\n\n[Content truncated - file too large]"

            return f"Text File: {file_path.name}\n\nContent:\n{content}"
        except Exception as e:
            return f"Text File: {file_path.name}\nError: {str(e)}"

    async def _extract_fig_basic_info(self, file_path: Path) -> str:
        """Extract basic info from .fig file when conversion tools aren't available"""
        stat = file_path.stat()
        return f"Figma File: {file_path.name}\nSize: {stat.st_size} bytes\nType: Design file (.fig)\nDescription: Figma design file"

    async def _extract_sketch_basic_info(self, file_path: Path) -> str:
        """Extract basic info from .sketch file when conversion tools aren't available"""
        try:
            # Sketch files are ZIP archives
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                file_list = zip_ref.namelist()

                content = f"Sketch File: {file_path.name}\n"
                content += f"Files in archive: {len(file_list)}\n"

                # Look for important files
                pages = [f for f in file_list if f.endswith(".json") and "pages" in f]
                if pages:
                    content += f"Pages: {len(pages)}\n"

                return content
        except Exception as e:
            stat = file_path.stat()
            return f"Sketch File: {file_path.name}\nSize: {stat.st_size} bytes\nType: Design file (.sketch)\nError: {str(e)}"


# Global instance
design_file_converter = DesignFileConverter()
