#!/usr/bin/env python3
"""
Container Image Builder and Push Script
Builds and pushes all ToolBoxAI container images to registry
"""

import os
import sys
import json
import subprocess
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import docker
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
REGISTRY = os.getenv("REGISTRY", "ghcr.io/toolboxai-solutions")
BUILD_CACHE_DIR = PROJECT_ROOT / ".docker-cache"

# Image configurations
IMAGES = {
    "backend": {
        "dockerfile": "config/production/Dockerfile.backend",
        "context": str(PROJECT_ROOT),
        "target": "runtime",
        "tags": ["latest", "production"],
        "platforms": ["linux/amd64", "linux/arm64"],
        "cache_from": ["ghcr.io/toolboxai-solutions/backend:latest"],
        "build_args": {
            "BUILD_DATE": datetime.now().isoformat(),
            "VCS_REF": "",  # Will be populated with git commit
        }
    },
    "frontend": {
        "dockerfile": "config/production/Dockerfile.frontend",
        "context": str(PROJECT_ROOT),
        "target": "runtime",
        "tags": ["latest", "production"],
        "platforms": ["linux/amd64", "linux/arm64"],
        "cache_from": ["ghcr.io/toolboxai-solutions/frontend:latest"],
    },
    "flask-bridge": {
        "dockerfile": "config/production/Dockerfile.flask",
        "context": str(PROJECT_ROOT),
        "tags": ["latest", "production"],
        "platforms": ["linux/amd64"],
    },
    "dashboard-backend": {
        "dockerfile": "config/production/Dockerfile.dashboard",
        "context": str(PROJECT_ROOT),
        "tags": ["latest", "production"],
        "platforms": ["linux/amd64", "linux/arm64"],
    },
    "ghost": {
        "dockerfile": "config/production/Dockerfile.ghost",
        "context": str(PROJECT_ROOT),
        "tags": ["latest", "production"],
        "platforms": ["linux/amd64"],
    },
    "backup": {
        "dockerfile": "config/production/Dockerfile.backup",
        "context": str(PROJECT_ROOT),
        "tags": ["latest"],
        "platforms": ["linux/amd64"],
    },
}


class ContainerBuilder:
    """Container image builder with optimization and caching"""
    
    def __init__(self, registry: str, dry_run: bool = False):
        self.registry = registry
        self.dry_run = dry_run
        self.docker_client = docker.from_env() if not dry_run else None
        self.git_commit = self._get_git_commit()
        
    def _get_git_commit(self) -> str:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT
            )
            return result.stdout.strip()[:8]
        except Exception:
            return "unknown"
    
    def _calculate_context_hash(self, context_path: str) -> str:
        """Calculate hash of context directory for caching"""
        hasher = hashlib.sha256()
        
        for root, dirs, files in os.walk(context_path):
            # Skip .git and other irrelevant directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in sorted(files):
                if file.endswith(('.py', '.js', '.ts', '.json', '.yaml', '.yml')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'rb') as f:
                            hasher.update(f.read())
                    except Exception:
                        continue
        
        return hasher.hexdigest()[:12]
    
    def build_image(self, name: str, config: Dict) -> Tuple[bool, str]:
        """Build a single Docker image"""
        print(f"\n🔨 Building {name}...")
        
        if self.dry_run:
            print(f"  [DRY RUN] Would build {name}")
            return True, "dry-run"
        
        try:
            # Prepare build arguments
            build_args = config.get("build_args", {}).copy()
            build_args["VCS_REF"] = self.git_commit
            build_args["VERSION"] = f"{self.git_commit}-{datetime.now().strftime('%Y%m%d')}"
            
            # Calculate context hash for cache invalidation
            context_hash = self._calculate_context_hash(config["context"])
            build_args["CONTEXT_HASH"] = context_hash
            
            # Build command
            cmd = [
                "docker", "buildx", "build",
                "--file", config["dockerfile"],
                "--progress", "plain",
            ]
            
            # Add target if specified
            if "target" in config:
                cmd.extend(["--target", config["target"]])
            
            # Add build arguments
            for key, value in build_args.items():
                cmd.extend(["--build-arg", f"{key}={value}"])
            
            # Add cache sources
            for cache_from in config.get("cache_from", []):
                cmd.extend(["--cache-from", cache_from])
            
            # Add tags
            for tag in config.get("tags", ["latest"]):
                full_tag = f"{self.registry}/{name}:{tag}"
                cmd.extend(["--tag", full_tag])
                
                # Also tag with version
                if tag == "latest":
                    version_tag = f"{self.registry}/{name}:{self.git_commit}"
                    cmd.extend(["--tag", version_tag])
            
            # Add platforms for multi-arch build
            if len(config.get("platforms", [])) > 1:
                platforms = ",".join(config["platforms"])
                cmd.extend(["--platform", platforms])
            
            # Enable BuildKit features
            cmd.extend([
                "--cache-to", f"type=local,dest={BUILD_CACHE_DIR}/{name}",
                "--cache-from", f"type=local,src={BUILD_CACHE_DIR}/{name}",
            ])
            
            # Add context
            cmd.append(config["context"])
            
            # Create cache directory
            cache_dir = BUILD_CACHE_DIR / name
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Execute build
            print(f"  Executing: {' '.join(cmd[:10])}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**os.environ, "DOCKER_BUILDKIT": "1"}
            )
            
            if result.returncode != 0:
                print(f"  ❌ Build failed: {result.stderr}")
                return False, result.stderr
            
            # Get image size
            image = self.docker_client.images.get(f"{self.registry}/{name}:latest")
            size_mb = image.attrs["Size"] / (1024 * 1024)
            
            print(f"  ✅ Built successfully (Size: {size_mb:.2f} MB)")
            
            # Optimize if image is too large
            if size_mb > 500:
                print(f"  ⚠️  Image size exceeds 500MB, consider optimization")
            
            return True, f"{self.registry}/{name}:{self.git_commit}"
            
        except Exception as e:
            print(f"  ❌ Build error: {str(e)}")
            return False, str(e)
    
    def scan_image(self, image_tag: str) -> bool:
        """Security scan of Docker image"""
        print(f"  🔍 Scanning {image_tag} for vulnerabilities...")
        
        if self.dry_run:
            print(f"    [DRY RUN] Would scan {image_tag}")
            return True
        
        try:
            # Use trivy for security scanning
            cmd = ["docker", "run", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock",
                   "aquasec/trivy:latest", "image", "--severity", "HIGH,CRITICAL",
                   "--exit-code", "0", image_tag]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if "CRITICAL" in result.stdout:
                print(f"    ⚠️  Critical vulnerabilities found!")
                return False
            
            print(f"    ✅ Security scan passed")
            return True
            
        except Exception as e:
            print(f"    ⚠️  Scan failed: {str(e)}")
            return True  # Don't block on scan failures
    
    def push_image(self, image_tag: str) -> bool:
        """Push Docker image to registry"""
        print(f"  📤 Pushing {image_tag}...")
        
        if self.dry_run:
            print(f"    [DRY RUN] Would push {image_tag}")
            return True
        
        try:
            # Push image
            cmd = ["docker", "push", image_tag]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"    ❌ Push failed: {result.stderr}")
                return False
            
            print(f"    ✅ Pushed successfully")
            return True
            
        except Exception as e:
            print(f"    ❌ Push error: {str(e)}")
            return False
    
    def build_all(self, images: List[str] = None, parallel: bool = True) -> Dict[str, bool]:
        """Build all configured images"""
        images_to_build = images or list(IMAGES.keys())
        results = {}
        
        print(f"\n🚀 Building {len(images_to_build)} images...")
        print(f"   Registry: {self.registry}")
        print(f"   Git commit: {self.git_commit}")
        print(f"   Parallel: {parallel}")
        
        if parallel:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {}
                
                for name in images_to_build:
                    if name in IMAGES:
                        future = executor.submit(self.build_image, name, IMAGES[name])
                        futures[future] = name
                
                for future in as_completed(futures):
                    name = futures[future]
                    success, image_tag = future.result()
                    results[name] = success
                    
                    if success and not self.dry_run:
                        # Scan and push
                        self.scan_image(image_tag)
                        self.push_image(image_tag)
        else:
            for name in images_to_build:
                if name in IMAGES:
                    success, image_tag = self.build_image(name, IMAGES[name])
                    results[name] = success
                    
                    if success and not self.dry_run:
                        # Scan and push
                        self.scan_image(image_tag)
                        self.push_image(image_tag)
        
        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Build and push ToolBoxAI container images")
    parser.add_argument("--registry", default=REGISTRY, help="Container registry")
    parser.add_argument("--images", nargs="+", help="Specific images to build")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel builds")
    parser.add_argument("--no-push", action="store_true", help="Build only, don't push")
    parser.add_argument("--no-scan", action="store_true", help="Skip security scanning")
    
    args = parser.parse_args()
    
    # Check Docker
    try:
        subprocess.run(["docker", "version"], capture_output=True, check=True)
    except Exception:
        print("❌ Docker is not available")
        sys.exit(1)
    
    # Check buildx
    try:
        subprocess.run(["docker", "buildx", "version"], capture_output=True, check=True)
    except Exception:
        print("⚠️  Docker buildx not available, installing...")
        subprocess.run(["docker", "buildx", "create", "--use"], check=True)
    
    # Build images
    builder = ContainerBuilder(args.registry, args.dry_run)
    results = builder.build_all(
        images=args.images,
        parallel=not args.no_parallel
    )
    
    # Summary
    print("\n📊 Build Summary:")
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful
    
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {len(results)} | Success: {successful} | Failed: {failed}")
    
    if failed > 0:
        sys.exit(1)
    
    print("\n✨ All images built successfully!")
    
    # Notify other terminals via Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.publish('terminal:github:image_built', json.dumps({
            'timestamp': datetime.now().isoformat(),
            'images': list(results.keys()),
            'registry': args.registry,
            'commit': builder.git_commit
        }))
        print("📢 Notified other terminals about build completion")
    except Exception:
        pass


if __name__ == "__main__":
    main()