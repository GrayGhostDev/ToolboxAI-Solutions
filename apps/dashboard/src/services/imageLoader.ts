/**
 * Image Loader Service
 * Loads actual images from design_files folder using JSON metadata
 */

interface ImageMetadata {
  success: boolean;
  file_path: string;
  file_name: string;
  file_type: string;
  parsed_data: {
    format: string;
    file_format: string;
    mode: string;
    size: {
      width: number;
      height: number;
      total_pixels: number;
    };
    has_transparency: boolean;
    color_channels: number;
    color_histogram: {
      unique_colors: number;
      most_common: Array<{ color: string; count: number }>;
    };
  };
}

class ImageLoaderService {
  private static instance: ImageLoaderService;
  private imageCache: Map<string, string> = new Map();
  private metadataCache: Map<string, ImageMetadata> = new Map();

  static getInstance(): ImageLoaderService {
    if (!ImageLoaderService.instance) {
      ImageLoaderService.instance = new ImageLoaderService();
    }
    return ImageLoaderService.instance;
  }

  /**
   * Load image metadata from JSON file
   */
  async loadImageMetadata(jsonPath: string): Promise<ImageMetadata | null> {
    if (this.metadataCache.has(jsonPath)) {
      return this.metadataCache.get(jsonPath)!;
    }

    try {
      const response = await fetch(jsonPath);
      if (!response.ok) {
        console.warn(`Failed to load metadata: ${jsonPath}`);
        return null;
      }

      const metadata: ImageMetadata = await response.json();
      this.metadataCache.set(jsonPath, metadata);
      return metadata;
    } catch (error) {
      console.warn(`Error loading metadata from ${jsonPath}:`, error);
      return null;
    }
  }

  /**
   * Get actual image path from JSON metadata
   */
  async getImagePath(jsonPath: string): Promise<string | null> {
    const metadata = await this.loadImageMetadata(jsonPath);
    if (!metadata || !metadata.success) {
      return null;
    }

    // Convert the file_path to a web-accessible path
    const actualPath = metadata.file_path.replace('design_files/', '/design_files/');
    return actualPath;
  }

  /**
   * Load and cache image
   */
  async loadImage(jsonPath: string): Promise<string | null> {
    if (this.imageCache.has(jsonPath)) {
      return this.imageCache.get(jsonPath)!;
    }

    const imagePath = await this.getImagePath(jsonPath);
    if (!imagePath) {
      return null;
    }

    // Preload the image to ensure it's available
    try {
      const img = new Image();
      img.src = imagePath;
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
      });

      this.imageCache.set(jsonPath, imagePath);
      return imagePath;
    } catch (error) {
      console.warn(`Error loading image from ${imagePath}:`, error);
      return null;
    }
  }

  /**
   * Get 3D icon image path
   */
  async get3DIconPath(iconName: string, variant: number = 1): Promise<string | null> {
    // Direct path to the actual PNG image in design_files
    const imagePath = `/design_files/stuudy-3d-icons_NjhhMjYzMmIyMzI4MmUwMDM5ZDY0Yzlj/PNG/${iconName}_${variant}.png`;
    
    // Preload the image to ensure it's available
    try {
      const img = new Image();
      img.src = imagePath;
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
      });
      return imagePath;
    } catch (error) {
      console.warn(`Error loading 3D icon ${iconName}_${variant}:`, error);
      return null;
    }
  }

  /**
   * Get character image path
   */
  async getCharacterPath(characterType: 'astronaut' | 'alien', variant: number = 1): Promise<string | null> {
    // Direct path to the actual PNG image in design_files
    const imagePath = `/design_files/characters/PNG/${characterType === 'astronaut' ? 'Astronaut' : 'Aliens'}/${variant.toString().padStart(2, '0')}.png`;
    
    try {
      const img = new Image();
      img.src = imagePath;
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
      });
      return imagePath;
    } catch (error) {
      console.warn(`Error loading character ${characterType}_${variant}:`, error);
      return null;
    }
  }

  /**
   * Get character variation image path
   */
  async getCharacterVariationPath(characterType: 'astronaut' | 'alien', variant: number = 1): Promise<string | null> {
    // Direct path to the actual PNG image in design_files
    const imagePath = `/design_files/characters/PNG/${characterType === 'astronaut' ? 'Astronauto (variation)' : 'Aliens (Variation)'}/${variant.toString().padStart(2, '0')}.png`;
    
    try {
      const img = new Image();
      img.src = imagePath;
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
      });
      return imagePath;
    } catch (error) {
      console.warn(`Error loading character variation ${characterType}_${variant}:`, error);
      return null;
    }
  }

  /**
   * Get scene/background image path
   */
  async getScenePath(sceneName: string, variant: number = 1): Promise<string | null> {
    // Direct path to the actual PNG image in design_files
    const imagePath = `/design_files/characters/PNG/Scene/${variant.toString().padStart(2, '0')}.png`;
    
    try {
      const img = new Image();
      img.src = imagePath;
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
      });
      return imagePath;
    } catch (error) {
      console.warn(`Error loading scene ${sceneName}_${variant}:`, error);
      return null;
    }
  }

  /**
   * Get planet image path
   */
  async getPlanetPath(variant: number = 1): Promise<string | null> {
    // Direct path to the actual PNG image in design_files
    const imagePath = `/design_files/characters/PNG/Planet/${variant}.png`;
    
    try {
      const img = new Image();
      img.src = imagePath;
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
      });
      return imagePath;
    } catch (error) {
      console.warn(`Error loading planet ${variant}:`, error);
      return null;
    }
  }

  /**
   * Get item image path
   */
  async getItemPath(itemName: string): Promise<string | null> {
    // Direct path to the actual PNG image in design_files
    const imagePath = `/design_files/characters/PNG/Item/${itemName}.png`;
    
    try {
      const img = new Image();
      img.src = imagePath;
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
      });
      return imagePath;
    } catch (error) {
      console.warn(`Error loading item ${itemName}:`, error);
      return null;
    }
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.imageCache.clear();
    this.metadataCache.clear();
  }
}

export const imageLoader = ImageLoaderService.getInstance();
export type { ImageMetadata };
