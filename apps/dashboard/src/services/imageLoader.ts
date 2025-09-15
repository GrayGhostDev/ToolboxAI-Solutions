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
    const jsonPath = `/images/png/3d_icon_${iconName}_${variant}.json`;
    return this.loadImage(jsonPath);
  }

  /**
   * Get character image path
   */
  async getCharacterPath(characterType: 'astronaut' | 'alien', variant: number = 1): Promise<string | null> {
    const jsonPath = `/images/png/${characterType}_${variant.toString().padStart(2, '0')}.json`;
    return this.loadImage(jsonPath);
  }

  /**
   * Get character variation image path
   */
  async getCharacterVariationPath(characterType: 'astronaut' | 'alien', variant: number = 1): Promise<string | null> {
    const jsonPath = `/images/png/${characterType}_variation_${variant.toString().padStart(2, '0')}.json`;
    return this.loadImage(jsonPath);
  }

  /**
   * Get scene/background image path
   */
  async getScenePath(sceneName: string, variant: number = 1): Promise<string | null> {
    const jsonPath = `/images/png/${sceneName}_${variant.toString().padStart(2, '0')}.json`;
    return this.loadImage(jsonPath);
  }

  /**
   * Get planet image path
   */
  async getPlanetPath(variant: number = 1): Promise<string | null> {
    const jsonPath = `/images/png/planet_${variant}.json`;
    return this.loadImage(jsonPath);
  }

  /**
   * Get item image path
   */
  async getItemPath(itemName: string): Promise<string | null> {
    const jsonPath = `/images/png/item_${itemName}.json`;
    return this.loadImage(jsonPath);
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
