"""
Enhanced Design File Parser

Provides complete, interpretable parsing of design files for development and manipulation.
Extracts all design elements, properties, and relationships in a structured format.
"""

import asyncio
import json
import logging
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import subprocess
import base64

logger = logging.getLogger(__name__)


class EnhancedDesignParser:
    """Parses design files into complete, interpretable structures"""

    def __init__(
        self,
        output_dir: str = "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/images",
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.supported_formats = {
            ".fig": self._parse_figma_file,
            ".sketch": self._parse_sketch_file,
            ".xd": self._parse_xd_file,
            ".blend": self._parse_blend_file,
            ".obj": self._parse_obj_file,
            ".png": self._parse_image_file,
            ".jpg": self._parse_image_file,
            ".jpeg": self._parse_image_file,
            ".mp4": self._parse_video_file,
        }

    async def parse_design_file(
        self, file_path: Union[str, Path], save_output: bool = True
    ) -> Dict[str, Any]:
        """Parse a design file into complete interpretable structure"""
        file_path = Path(file_path)

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}", "parsed_data": None}

        extension = file_path.suffix.lower()

        if extension not in self.supported_formats:
            return {
                "success": False,
                "error": f"Unsupported format: {extension}",
                "parsed_data": None,
            }

        try:
            parser = self.supported_formats[extension]
            parsed_data = await parser(file_path)

            result = {
                "success": True,
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_type": extension,
                "parsed_data": parsed_data,
            }

            # Save output to images folder if requested
            if save_output:
                output_file = await self._save_parsed_data(result)
                result["output_file"] = str(output_file) if output_file else None

            return result
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return {"success": False, "error": str(e), "parsed_data": None}

    async def _save_parsed_data(self, result: Dict[str, Any]) -> Optional[Path]:
        """Save parsed data to the images folder"""
        try:
            # Create a safe filename
            safe_name = result["file_name"].replace(".", "_").replace(" ", "_")
            output_filename = f"parsed_{safe_name}.json"
            output_path = self.output_dir / output_filename

            # Save the complete result as JSON
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, default=str)

            logger.info(f"Saved parsed data to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving parsed data: {e}")
            return None

    async def _parse_figma_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse Figma .fig file into complete structure"""
        try:
            # Try fig2sketch conversion first
            with tempfile.TemporaryDirectory() as temp_dir:
                sketch_path = Path(temp_dir) / "temp.sketch"

                result = await asyncio.create_subprocess_exec(
                    "fig2sketch",
                    str(file_path),
                    str(sketch_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await result.communicate()

                if result.returncode == 0 and sketch_path.exists():
                    # Parse the converted sketch file
                    sketch_data = await self._parse_sketch_file(sketch_path)
                    return {
                        "source_format": "figma",
                        "converted_from": "sketch",
                        "figma_data": await self._extract_figma_metadata(file_path),
                        "sketch_data": sketch_data,
                    }
                else:
                    # Fallback: extract what we can from fig file
                    return await self._extract_figma_metadata(file_path)
        except FileNotFoundError:
            return await self._extract_figma_metadata(file_path)
        except Exception as e:
            logger.warning(f"fig2sketch conversion failed: {e}")
            return await self._extract_figma_metadata(file_path)

    async def _parse_sketch_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse Sketch .sketch file into complete structure"""
        try:
            # Sketch files are ZIP archives
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                file_list = zip_ref.namelist()

                parsed_data = {
                    "format": "sketch",
                    "version": "unknown",
                    "pages": [],
                    "symbols": [],
                    "artboards": [],
                    "layers": [],
                    "styles": [],
                    "fonts": [],
                    "colors": [],
                    "gradients": [],
                    "shadows": [],
                    "borders": [],
                }

                # Parse document.json for main structure
                if "document.json" in file_list:
                    doc_data = json.loads(zip_ref.read("document.json").decode("utf-8"))
                    parsed_data["version"] = doc_data.get("version", "unknown")
                    parsed_data["pages"] = self._extract_sketch_pages(doc_data)

                # Parse pages
                for page_file in [
                    f for f in file_list if f.startswith("pages/") and f.endswith(".json")
                ]:
                    page_data = json.loads(zip_ref.read(page_file).decode("utf-8"))
                    page_info = self._extract_sketch_page_info(page_data)
                    parsed_data["pages"].append(page_info)

                # Parse symbols
                if "meta.json" in file_list:
                    meta_data = json.loads(zip_ref.read("meta.json").decode("utf-8"))
                    parsed_data["symbols"] = self._extract_sketch_symbols(meta_data)

                # Extract colors and styles
                parsed_data["colors"] = self._extract_sketch_colors(zip_ref, file_list)
                parsed_data["styles"] = self._extract_sketch_styles(zip_ref, file_list)

                return parsed_data

        except Exception as e:
            logger.error(f"Error parsing Sketch file: {e}")
            return {
                "format": "sketch",
                "error": str(e),
                "basic_info": await self._get_basic_file_info(file_path),
            }

    async def _parse_xd_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse Adobe XD .xd file into complete structure"""
        try:
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                file_list = zip_ref.namelist()

                parsed_data = {
                    "format": "adobe_xd",
                    "version": "unknown",
                    "artboards": [],
                    "components": [],
                    "styles": [],
                    "assets": [],
                    "interactions": [],
                    "prototypes": [],
                }

                # Parse manifest
                if "manifest" in file_list:
                    manifest_data = json.loads(zip_ref.read("manifest").decode("utf-8"))
                    parsed_data["version"] = manifest_data.get("version", "unknown")

                # Parse artboards
                artboard_files = [
                    f for f in file_list if "artboard" in f.lower() and f.endswith(".json")
                ]
                for artboard_file in artboard_files:
                    artboard_data = json.loads(zip_ref.read(artboard_file).decode("utf-8"))
                    artboard_info = self._extract_xd_artboard(artboard_data)
                    parsed_data["artboards"].append(artboard_info)

                # Parse components
                component_files = [
                    f for f in file_list if "component" in f.lower() and f.endswith(".json")
                ]
                for component_file in component_files:
                    component_data = json.loads(zip_ref.read(component_file).decode("utf-8"))
                    component_info = self._extract_xd_component(component_data)
                    parsed_data["components"].append(component_info)

                # Parse interactions and prototypes
                parsed_data["interactions"] = self._extract_xd_interactions(zip_ref, file_list)
                parsed_data["prototypes"] = self._extract_xd_prototypes(zip_ref, file_list)

                return parsed_data

        except Exception as e:
            logger.error(f"Error parsing XD file: {e}")
            return {
                "format": "adobe_xd",
                "error": str(e),
                "basic_info": await self._get_basic_file_info(file_path),
            }

    async def _parse_blend_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse Blender .blend file into complete structure"""
        try:
            # Use blender to export data
            with tempfile.TemporaryDirectory() as temp_dir:
                json_path = Path(temp_dir) / "export.json"

                # Create a Python script to export blend data
                export_script = f"""
import bpy
import json
import sys

# Clear existing data
bpy.ops.wm.read_homefile(use_empty=True)

# Load the blend file
bpy.ops.wm.open_mainfile(filepath="{file_path}")

# Export data
data = {{
    'objects': [],
    'materials': [],
    'textures': [],
    'meshes': [],
    'cameras': [],
    'lights': [],
    'scenes': []
}}

# Export objects
for obj in bpy.data.objects:
    obj_data = {{
        'name': obj.name,
        'type': obj.type,
        'location': list(obj.location),
        'rotation': list(obj.rotation_euler),
        'scale': list(obj.scale),
        'visible': obj.visible_get()
    }}

    if obj.type == 'MESH':
        mesh = obj.data
        obj_data['mesh'] = {{
            'vertices': len(mesh.vertices),
            'faces': len(mesh.polygons),
            'edges': len(mesh.edges),
            'materials': [mat.name for mat in mesh.materials]
        }}

    data['objects'].append(obj_data)

# Export materials
for mat in bpy.data.materials:
    mat_data = {{
        'name': mat.name,
        'use_nodes': mat.use_nodes,
        'diffuse_color': list(mat.diffuse_color),
        'metallic': mat.metallic,
        'roughness': mat.roughness
    }}
    data['materials'].append(mat_data)

# Export scenes
for scene in bpy.data.scenes:
    scene_data = {{
        'name': scene.name,
        'frame_start': scene.frame_start,
        'frame_end': scene.frame_end,
        'fps': scene.render.fps,
        'resolution': [scene.render.resolution_x, scene.render.resolution_y]
    }}
    data['scenes'].append(scene_data)

# Write to file
with open('{json_path}', 'w') as f:
    json.dump(data, f, indent=2)
"""

                script_path = Path(temp_dir) / "export.py"
                script_path.write_text(export_script)

                # Run blender with the script
                result = await asyncio.create_subprocess_exec(
                    "blender",
                    "--background",
                    "--python",
                    str(script_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await result.communicate()

                if result.returncode == 0 and json_path.exists():
                    with open(json_path, "r") as f:
                        blend_data = json.load(f)
                    return {"format": "blender", "data": blend_data}
                else:
                    # Fallback: basic info
                    return await self._get_basic_blend_info(file_path)

        except FileNotFoundError:
            return await self._get_basic_blend_info(file_path)
        except Exception as e:
            logger.warning(f"Blender export failed: {e}")
            return await self._get_basic_blend_info(file_path)

    async def _parse_obj_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse .obj file into complete structure"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            parsed_data = {
                "format": "wavefront_obj",
                "vertices": [],
                "faces": [],
                "normals": [],
                "texture_coords": [],
                "materials": [],
                "groups": [],
                "objects": [],
                "statistics": {},
            }

            current_material = None
            current_group = None
            current_object = None

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split()
                if not parts:
                    continue

                command = parts[0].lower()

                if command == "v":  # Vertex
                    if len(parts) >= 4:
                        vertex = {
                            "x": float(parts[1]),
                            "y": float(parts[2]),
                            "z": float(parts[3]),
                            "w": float(parts[4]) if len(parts) > 4 else 1.0,
                        }
                        parsed_data["vertices"].append(vertex)

                elif command == "vt":  # Texture coordinate
                    if len(parts) >= 3:
                        tex_coord = {
                            "u": float(parts[1]),
                            "v": float(parts[2]),
                            "w": float(parts[3]) if len(parts) > 3 else 0.0,
                        }
                        parsed_data["texture_coords"].append(tex_coord)

                elif command == "vn":  # Normal
                    if len(parts) >= 4:
                        normal = {"x": float(parts[1]), "y": float(parts[2]), "z": float(parts[3])}
                        parsed_data["normals"].append(normal)

                elif command == "f":  # Face
                    if len(parts) >= 4:
                        face = {
                            "vertices": [],
                            "texture_coords": [],
                            "normals": [],
                            "material": current_material,
                            "group": current_group,
                            "object": current_object,
                        }

                        for vertex_data in parts[1:]:
                            # Parse vertex/texture/normal indices
                            indices = vertex_data.split("/")
                            face["vertices"].append(int(indices[0]) - 1 if indices[0] else -1)
                            face["texture_coords"].append(
                                int(indices[1]) - 1 if len(indices) > 1 and indices[1] else -1
                            )
                            face["normals"].append(
                                int(indices[2]) - 1 if len(indices) > 2 and indices[2] else -1
                            )

                        parsed_data["faces"].append(face)

                elif command == "usemtl":  # Material
                    current_material = parts[1] if len(parts) > 1 else None

                elif command == "g":  # Group
                    current_group = parts[1] if len(parts) > 1 else None

                elif command == "o":  # Object
                    current_object = parts[1] if len(parts) > 1 else None
                    parsed_data["objects"].append(current_object)

                elif command == "mtllib":  # Material library
                    if len(parts) > 1:
                        parsed_data["materials"].append(parts[1])

            # Calculate statistics
            parsed_data["statistics"] = {
                "vertex_count": len(parsed_data["vertices"]),
                "face_count": len(parsed_data["faces"]),
                "normal_count": len(parsed_data["normals"]),
                "texture_coord_count": len(parsed_data["texture_coords"]),
                "material_count": len(parsed_data["materials"]),
                "object_count": len(parsed_data["objects"]),
                "line_count": len(lines),
            }

            return parsed_data

        except Exception as e:
            logger.error(f"Error parsing OBJ file: {e}")
            return {
                "format": "wavefront_obj",
                "error": str(e),
                "basic_info": await self._get_basic_file_info(file_path),
            }

    async def _parse_image_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse image file into complete structure"""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS

            with Image.open(file_path) as img:
                # Basic image info
                image_data = {
                    "format": "image",
                    "file_format": img.format,
                    "mode": img.mode,
                    "size": {
                        "width": img.width,
                        "height": img.height,
                        "total_pixels": img.width * img.height,
                    },
                    "has_transparency": img.mode in ("RGBA", "LA", "P"),
                    "color_channels": len(img.getbands()),
                    "exif_data": {},
                    "color_histogram": {},
                    "dominant_colors": [],
                }

                # Extract EXIF data
                if hasattr(img, "_getexif") and img._getexif():
                    exifdata = img._getexif()
                    for tag_id, value in exifdata.items():
                        tag = TAGS.get(tag_id, tag_id)
                        image_data["exif_data"][tag] = str(value)

                # Analyze colors
                if img.mode == "RGB" or img.mode == "RGBA":
                    # Get color histogram
                    colors = img.getcolors(maxcolors=256 * 256 * 256)
                    if colors:
                        image_data["color_histogram"] = {
                            "unique_colors": len(colors),
                            "most_common": colors[:10],  # Top 10 colors
                        }

                # Extract dominant colors (simplified)
                if img.mode in ("RGB", "RGBA"):
                    # Resize for faster processing
                    small_img = img.resize((150, 150))
                    colors = small_img.getcolors(maxcolors=256 * 256 * 256)
                    if colors:
                        # Sort by frequency and get top colors
                        colors.sort(key=lambda x: x[0], reverse=True)
                        image_data["dominant_colors"] = [
                            {"color": color, "frequency": count} for count, color in colors[:5]
                        ]

                return image_data

        except ImportError:
            return {
                "format": "image",
                "error": "PIL not available",
                "basic_info": await self._get_basic_file_info(file_path),
            }
        except Exception as e:
            logger.error(f"Error parsing image file: {e}")
            return {
                "format": "image",
                "error": str(e),
                "basic_info": await self._get_basic_file_info(file_path),
            }

    async def _parse_video_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse video file into complete structure"""
        try:
            # Use ffprobe for detailed video analysis
            result = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                "-show_frames",
                str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                probe_data = json.loads(stdout.decode("utf-8"))

                video_data = {
                    "format": "video",
                    "file_format": probe_data.get("format", {}).get("format_name", "unknown"),
                    "duration": float(probe_data.get("format", {}).get("duration", 0)),
                    "size": int(probe_data.get("format", {}).get("size", 0)),
                    "bitrate": int(probe_data.get("format", {}).get("bit_rate", 0)),
                    "streams": [],
                    "metadata": probe_data.get("format", {}).get("tags", {}),
                }

                # Parse video and audio streams
                for stream in probe_data.get("streams", []):
                    stream_info = {
                        "index": stream.get("index"),
                        "codec_type": stream.get("codec_type"),
                        "codec_name": stream.get("codec_name"),
                        "codec_long_name": stream.get("codec_long_name"),
                        "profile": stream.get("profile"),
                        "level": stream.get("level"),
                    }

                    if stream.get("codec_type") == "video":
                        stream_info.update(
                            {
                                "width": stream.get("width"),
                                "height": stream.get("height"),
                                "aspect_ratio": stream.get("display_aspect_ratio"),
                                "frame_rate": stream.get("r_frame_rate"),
                                "pixel_format": stream.get("pix_fmt"),
                                "color_space": stream.get("color_space"),
                                "color_primaries": stream.get("color_primaries"),
                                "color_trc": stream.get("color_trc"),
                            }
                        )
                    elif stream.get("codec_type") == "audio":
                        stream_info.update(
                            {
                                "sample_rate": stream.get("sample_rate"),
                                "channels": stream.get("channels"),
                                "channel_layout": stream.get("channel_layout"),
                                "bit_rate": stream.get("bit_rate"),
                            }
                        )

                    video_data["streams"].append(stream_info)

                return video_data
            else:
                # Fallback: basic info
                return await self._get_basic_file_info(file_path)

        except FileNotFoundError:
            return await self._get_basic_file_info(file_path)
        except Exception as e:
            logger.warning(f"ffprobe analysis failed: {e}")
            return await self._get_basic_file_info(file_path)

    # Helper methods for extracting specific data structures

    def _extract_sketch_pages(self, doc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract page information from Sketch document"""
        pages = []
        for page in doc_data.get("pages", []):
            page_info = {
                "id": page.get("_ref"),
                "name": page.get("name", "Untitled"),
                "artboards": [],
            }
            pages.append(page_info)
        return pages

    def _extract_sketch_page_info(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed page information"""
        return {
            "name": page_data.get("name", "Untitled"),
            "artboards": self._extract_sketch_artboards(page_data),
            "layers": self._extract_sketch_layers(page_data),
        }

    def _extract_sketch_artboards(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract artboard information"""
        artboards = []
        for layer in page_data.get("layers", []):
            if layer.get("_class") == "artboard":
                artboard = {
                    "name": layer.get("name", "Untitled"),
                    "frame": layer.get("frame", {}),
                    "style": layer.get("style", {}),
                    "layers": self._extract_sketch_layers(layer),
                }
                artboards.append(artboard)
        return artboards

    def _extract_sketch_layers(self, container: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract layer information recursively"""
        layers = []
        for layer in container.get("layers", []):
            layer_info = {
                "name": layer.get("name", "Untitled"),
                "class": layer.get("_class"),
                "frame": layer.get("frame", {}),
                "style": layer.get("style", {}),
                "isVisible": layer.get("isVisible", True),
                "isLocked": layer.get("isLocked", False),
                "layers": self._extract_sketch_layers(layer) if layer.get("layers") else [],
            }
            layers.append(layer_info)
        return layers

    def _extract_sketch_symbols(self, meta_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract symbol information"""
        symbols = []
        for symbol in meta_data.get("symbols", []):
            symbol_info = {
                "name": symbol.get("name", "Untitled"),
                "id": symbol.get("symbolID"),
                "overrides": symbol.get("overrides", []),
            }
            symbols.append(symbol_info)
        return symbols

    def _extract_sketch_colors(
        self, zip_ref: zipfile.ZipFile, file_list: List[str]
    ) -> List[Dict[str, Any]]:
        """Extract color information from Sketch file"""
        colors = []
        # Look for color definitions in various files
        for file_name in file_list:
            if "color" in file_name.lower() and file_name.endswith(".json"):
                try:
                    color_data = json.loads(zip_ref.read(file_name).decode("utf-8"))
                    # Process color data based on structure
                    colors.extend(self._process_sketch_color_data(color_data))
                except:
                    continue
        return colors

    def _extract_sketch_styles(
        self, zip_ref: zipfile.ZipFile, file_list: List[str]
    ) -> List[Dict[str, Any]]:
        """Extract style information from Sketch file"""
        styles = []
        # Look for style definitions
        for file_name in file_list:
            if "style" in file_name.lower() and file_name.endswith(".json"):
                try:
                    style_data = json.loads(zip_ref.read(file_name).decode("utf-8"))
                    styles.extend(self._process_sketch_style_data(style_data))
                except:
                    continue
        return styles

    def _process_sketch_color_data(self, color_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process color data from Sketch file"""
        colors = []
        # Implementation depends on Sketch file structure
        # This is a simplified version
        if isinstance(color_data, dict):
            for key, value in color_data.items():
                if "color" in key.lower() and isinstance(value, (list, dict)):
                    colors.append({"name": key, "value": value})
        return colors

    def _process_sketch_style_data(self, style_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process style data from Sketch file"""
        styles = []
        # Implementation depends on Sketch file structure
        if isinstance(style_data, dict):
            for key, value in style_data.items():
                if "style" in key.lower():
                    styles.append({"name": key, "value": value})
        return styles

    def _extract_xd_artboard(self, artboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract artboard information from XD file"""
        return {
            "name": artboard_data.get("name", "Untitled"),
            "id": artboard_data.get("id"),
            "bounds": artboard_data.get("bounds", {}),
            "children": self._extract_xd_children(artboard_data.get("children", [])),
        }

    def _extract_xd_component(self, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract component information from XD file"""
        return {
            "name": component_data.get("name", "Untitled"),
            "id": component_data.get("id"),
            "bounds": component_data.get("bounds", {}),
            "children": self._extract_xd_children(component_data.get("children", [])),
        }

    def _extract_xd_children(self, children: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract children elements from XD file"""
        elements = []
        for child in children:
            element = {
                "type": child.get("type", "unknown"),
                "name": child.get("name", "Untitled"),
                "bounds": child.get("bounds", {}),
                "style": child.get("style", {}),
                "children": self._extract_xd_children(child.get("children", [])),
            }
            elements.append(element)
        return elements

    def _extract_xd_interactions(
        self, zip_ref: zipfile.ZipFile, file_list: List[str]
    ) -> List[Dict[str, Any]]:
        """Extract interaction data from XD file"""
        interactions = []
        # Look for interaction files
        for file_name in file_list:
            if "interaction" in file_name.lower() and file_name.endswith(".json"):
                try:
                    interaction_data = json.loads(zip_ref.read(file_name).decode("utf-8"))
                    interactions.append(interaction_data)
                except:
                    continue
        return interactions

    def _extract_xd_prototypes(
        self, zip_ref: zipfile.ZipFile, file_list: List[str]
    ) -> List[Dict[str, Any]]:
        """Extract prototype data from XD file"""
        prototypes = []
        # Look for prototype files
        for file_name in file_list:
            if "prototype" in file_name.lower() and file_name.endswith(".json"):
                try:
                    prototype_data = json.loads(zip_ref.read(file_name).decode("utf-8"))
                    prototypes.append(prototype_data)
                except:
                    continue
        return prototypes

    async def _extract_figma_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic metadata from Figma file when conversion tools aren't available"""
        stat = file_path.stat()
        return {
            "format": "figma",
            "file_size": stat.st_size,
            "modified_time": stat.st_mtime,
            "note": "Full parsing requires fig2sketch tool",
        }

    async def _get_basic_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get basic file information as fallback"""
        stat = file_path.stat()
        return {
            "file_size": stat.st_size,
            "modified_time": stat.st_mtime,
            "note": "Basic info only - full parsing not available",
        }

    async def _get_basic_blend_info(self, file_path: Path) -> Dict[str, Any]:
        """Get basic Blender file information"""
        stat = file_path.stat()
        return {
            "format": "blender",
            "file_size": stat.st_size,
            "note": "Full parsing requires Blender installation",
        }


# Global instance
enhanced_design_parser = EnhancedDesignParser()
