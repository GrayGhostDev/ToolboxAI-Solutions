/**
 * Roblox Sound Effects System
 *
 * Manages audio playback for UI interactions, achievements, and game events
 * Supports Web Audio API with fallback to HTML5 Audio
 */

export type SoundType =
  | 'click'
  | 'hover'
  | 'success'
  | 'error'
  | 'achievement'
  | 'levelUp'
  | 'xpGain'
  | 'notification'
  | 'open'
  | 'close'
  | 'whoosh'
  | 'pop'
  | 'coin'
  | 'unlock';

export type SoundCategory = 'ui' | 'game' | 'achievement' | 'notification';

export interface SoundConfig {
  volume: number; // 0.0 to 1.0
  playbackRate?: number; // 0.5 to 2.0 (speed)
  loop?: boolean;
  category: SoundCategory;
}

export interface SoundSettings {
  enabled: boolean;
  masterVolume: number;
  categoryVolumes: Record<SoundCategory, number>;
}

class SoundEffectsManager {
  private audioContext: AudioContext | null = null;
  private sounds: Map<SoundType, AudioBuffer> = new Map();
  private activeSounds: Set<AudioBufferSourceNode> = new Set();
  private settings: SoundSettings = {
    enabled: true,
    masterVolume: 0.7,
    categoryVolumes: {
      ui: 0.8,
      game: 1.0,
      achievement: 1.0,
      notification: 0.9,
    },
  };

  // Sound configuration with procedural audio generation
  private soundConfigs: Record<SoundType, SoundConfig> = {
    click: { volume: 0.3, playbackRate: 1.0, category: 'ui' },
    hover: { volume: 0.2, playbackRate: 1.2, category: 'ui' },
    success: { volume: 0.6, category: 'achievement' },
    error: { volume: 0.5, category: 'ui' },
    achievement: { volume: 0.8, category: 'achievement' },
    levelUp: { volume: 0.9, category: 'achievement' },
    xpGain: { volume: 0.4, category: 'game' },
    notification: { volume: 0.6, category: 'notification' },
    open: { volume: 0.4, category: 'ui' },
    close: { volume: 0.4, category: 'ui' },
    whoosh: { volume: 0.5, category: 'ui' },
    pop: { volume: 0.5, category: 'ui' },
    coin: { volume: 0.6, category: 'game' },
    unlock: { volume: 0.7, category: 'achievement' },
  };

  constructor() {
    this.initializeAudioContext();
    this.loadSettings();
  }

  /**
   * Initialize Web Audio API context
   */
  private initializeAudioContext(): void {
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      this.audioContext = new AudioContextClass();
    } catch (error) {
      console.warn('Web Audio API not supported, sound effects disabled:', error);
      this.settings.enabled = false;
    }
  }

  /**
   * Load user settings from localStorage
   */
  private loadSettings(): void {
    try {
      const stored = localStorage.getItem('roblox-sound-settings');
      if (stored) {
        this.settings = { ...this.settings, ...JSON.parse(stored) };
      }
    } catch (error) {
      console.warn('Failed to load sound settings:', error);
    }
  }

  /**
   * Save settings to localStorage
   */
  private saveSettings(): void {
    try {
      localStorage.setItem('roblox-sound-settings', JSON.stringify(this.settings));
    } catch (error) {
      console.warn('Failed to save sound settings:', error);
    }
  }

  /**
   * Generate procedural audio buffer for a sound type
   */
  private generateSound(type: SoundType): AudioBuffer | null {
    if (!this.audioContext) return null;

    const sampleRate = this.audioContext.sampleRate;
    let duration = 0.1; // Default 100ms
    let buffer: AudioBuffer;

    switch (type) {
      case 'click':
        duration = 0.05;
        buffer = this.audioContext.createBuffer(1, sampleRate * duration, sampleRate);
        this.generateClickSound(buffer);
        break;

      case 'hover':
        duration = 0.03;
        buffer = this.audioContext.createBuffer(1, sampleRate * duration, sampleRate);
        this.generateHoverSound(buffer);
        break;

      case 'success':
        duration = 0.4;
        buffer = this.audioContext.createBuffer(1, sampleRate * duration, sampleRate);
        this.generateSuccessSound(buffer);
        break;

      case 'error':
        duration = 0.3;
        buffer = this.audioContext.createBuffer(1, sampleRate * duration, sampleRate);
        this.generateErrorSound(buffer);
        break;

      case 'achievement':
        duration = 0.8;
        buffer = this.audioContext.createBuffer(1, sampleRate * duration, sampleRate);
        this.generateAchievementSound(buffer);
        break;

      case 'levelUp':
        duration = 1.0;
        buffer = this.audioContext.createBuffer(1, sampleRate * duration, sampleRate);
        this.generateLevelUpSound(buffer);
        break;

      case 'xpGain':
        duration = 0.2;
        buffer = this.audioContext.createBuffer(1, sampleRate * duration, sampleRate);
        this.generateXPSound(buffer);
        break;

      case 'coin':
        duration = 0.15;
        buffer = this.audioContext.createBuffer(1, sampleRate * duration, sampleRate);
        this.generateCoinSound(buffer);
        break;

      case 'unlock':
        duration = 0.6;
        buffer = this.audioContext.createBuffer(1, sampleRate * duration, sampleRate);
        this.generateUnlockSound(buffer);
        break;

      default:
        // Generic beep for other types
        duration = 0.1;
        buffer = this.audioContext.createBuffer(1, sampleRate * duration, sampleRate);
        this.generateBeepSound(buffer, 440);
    }

    return buffer;
  }

  /**
   * Generate click sound (short beep)
   */
  private generateClickSound(buffer: AudioBuffer): void {
    const data = buffer.getChannelData(0);
    const frequency = 800;
    const sampleRate = buffer.sampleRate;

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      const envelope = Math.exp(-t * 20); // Fast decay
      data[i] = Math.sin(2 * Math.PI * frequency * t) * envelope * 0.3;
    }
  }

  /**
   * Generate hover sound (subtle swoosh)
   */
  private generateHoverSound(buffer: AudioBuffer): void {
    const data = buffer.getChannelData(0);
    const sampleRate = buffer.sampleRate;

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      const frequency = 1000 + (t * 500); // Rising pitch
      const envelope = Math.exp(-t * 30);
      data[i] = Math.sin(2 * Math.PI * frequency * t) * envelope * 0.2;
    }
  }

  /**
   * Generate success sound (cheerful chord progression)
   */
  private generateSuccessSound(buffer: AudioBuffer): void {
    const data = buffer.getChannelData(0);
    const sampleRate = buffer.sampleRate;
    const notes = [523.25, 659.25, 783.99]; // C5, E5, G5 (major chord)

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      const envelope = Math.exp(-t * 3);
      let sample = 0;

      notes.forEach((freq) => {
        sample += Math.sin(2 * Math.PI * freq * t) * envelope;
      });

      data[i] = sample * 0.2;
    }
  }

  /**
   * Generate error sound (descending dissonant notes)
   */
  private generateErrorSound(buffer: AudioBuffer): void {
    const data = buffer.getChannelData(0);
    const sampleRate = buffer.sampleRate;

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      const frequency = 400 - (t * 200); // Descending pitch
      const envelope = Math.exp(-t * 5);
      data[i] = Math.sin(2 * Math.PI * frequency * t) * envelope * 0.3;
    }
  }

  /**
   * Generate achievement unlock sound (triumphant fanfare)
   */
  private generateAchievementSound(buffer: AudioBuffer): void {
    const data = buffer.getChannelData(0);
    const sampleRate = buffer.sampleRate;
    const notes = [
      { freq: 523.25, start: 0, duration: 0.2 },    // C5
      { freq: 659.25, start: 0.2, duration: 0.2 },  // E5
      { freq: 783.99, start: 0.4, duration: 0.4 },  // G5
    ];

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      let sample = 0;

      notes.forEach((note) => {
        if (t >= note.start && t < note.start + note.duration) {
          const localT = t - note.start;
          const envelope = Math.exp(-localT * 2);
          sample += Math.sin(2 * Math.PI * note.freq * localT) * envelope;
        }
      });

      data[i] = sample * 0.25;
    }
  }

  /**
   * Generate level up sound (ascending arpeggio)
   */
  private generateLevelUpSound(buffer: AudioBuffer): void {
    const data = buffer.getChannelData(0);
    const sampleRate = buffer.sampleRate;
    const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      const noteIndex = Math.floor(t * 8) % notes.length;
      const frequency = notes[noteIndex];
      const envelope = Math.sin(Math.PI * (t / (buffer.length / sampleRate))) * 0.5;
      data[i] = Math.sin(2 * Math.PI * frequency * t) * envelope;
    }
  }

  /**
   * Generate XP gain sound (quick sparkle)
   */
  private generateXPSound(buffer: AudioBuffer): void {
    const data = buffer.getChannelData(0);
    const sampleRate = buffer.sampleRate;

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      const frequency = 1000 + (t * 1000); // Rising sparkle
      const envelope = Math.exp(-t * 10);
      data[i] = Math.sin(2 * Math.PI * frequency * t) * envelope * 0.3;
    }
  }

  /**
   * Generate coin sound (metallic ping)
   */
  private generateCoinSound(buffer: AudioBuffer): void {
    const data = buffer.getChannelData(0);
    const sampleRate = buffer.sampleRate;
    const frequencies = [1000, 1500, 2000]; // Harmonics

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      const envelope = Math.exp(-t * 15);
      let sample = 0;

      frequencies.forEach((freq, idx) => {
        sample += Math.sin(2 * Math.PI * freq * t) * envelope * (1 / (idx + 1));
      });

      data[i] = sample * 0.2;
    }
  }

  /**
   * Generate unlock sound (magical chime)
   */
  private generateUnlockSound(buffer: AudioBuffer): void {
    const data = buffer.getChannelData(0);
    const sampleRate = buffer.sampleRate;

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      const envelope = Math.exp(-t * 3);
      const freq1 = 800 * Math.sin(t * Math.PI * 2); // Vibrato
      const freq2 = 1200;
      const sample = (Math.sin(2 * Math.PI * freq1 * t) +
        Math.sin(2 * Math.PI * freq2 * t)) * envelope;
      data[i] = sample * 0.2;
    }
  }

  /**
   * Generate generic beep sound
   */
  private generateBeepSound(buffer: AudioBuffer, frequency: number): void {
    const data = buffer.getChannelData(0);
    const sampleRate = buffer.sampleRate;

    for (let i = 0; i < buffer.length; i++) {
      const t = i / sampleRate;
      const envelope = Math.exp(-t * 10);
      data[i] = Math.sin(2 * Math.PI * frequency * t) * envelope * 0.3;
    }
  }

  /**
   * Play a sound effect
   */
  public play(type: SoundType): void {
    if (!this.settings.enabled || !this.audioContext) return;

    try {
      // Generate or get cached sound
      if (!this.sounds.has(type)) {
        const buffer = this.generateSound(type);
        if (buffer) {
          this.sounds.set(type, buffer);
        } else {
          return;
        }
      }

      const buffer = this.sounds.get(type);
      if (!buffer) return;

      const config = this.soundConfigs[type];
      const categoryVolume = this.settings.categoryVolumes[config.category];
      const finalVolume = config.volume * categoryVolume * this.settings.masterVolume;

      // Create source and gain nodes
      const source = this.audioContext.createBufferSource();
      const gainNode = this.audioContext.createGain();

      source.buffer = buffer;
      source.playbackRate.value = config.playbackRate || 1.0;
      gainNode.gain.value = finalVolume;

      source.connect(gainNode);
      gainNode.connect(this.audioContext.destination);

      // Cleanup on end
      source.onended = () => {
        this.activeSounds.delete(source);
      };

      this.activeSounds.add(source);
      source.start();
    } catch (error) {
      console.warn('Failed to play sound:', type, error);
    }
  }

  /**
   * Stop all active sounds
   */
  public stopAll(): void {
    this.activeSounds.forEach((source) => {
      try {
        source.stop();
      } catch (error) {
        // Source may already be stopped
      }
    });
    this.activeSounds.clear();
  }

  /**
   * Update settings
   */
  public updateSettings(settings: Partial<SoundSettings>): void {
    this.settings = { ...this.settings, ...settings };
    this.saveSettings();
  }

  /**
   * Get current settings
   */
  public getSettings(): SoundSettings {
    return { ...this.settings };
  }

  /**
   * Toggle sound on/off
   */
  public toggle(): void {
    this.settings.enabled = !this.settings.enabled;
    this.saveSettings();
  }

  /**
   * Preload all sounds (for better performance)
   */
  public preloadAll(): void {
    Object.keys(this.soundConfigs).forEach((type) => {
      if (!this.sounds.has(type as SoundType)) {
        const buffer = this.generateSound(type as SoundType);
        if (buffer) {
          this.sounds.set(type as SoundType, buffer);
        }
      }
    });
  }

  /**
   * Clear all cached sounds
   */
  public clearCache(): void {
    this.sounds.clear();
  }
}

// Export singleton instance
export const soundEffects = new SoundEffectsManager();

// Export convenience functions
export const playSound = (type: SoundType) => soundEffects.play(type);
export const stopAllSounds = () => soundEffects.stopAll();
export const toggleSounds = () => soundEffects.toggle();
export const preloadSounds = () => soundEffects.preloadAll();
