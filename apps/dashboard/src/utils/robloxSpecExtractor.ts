/**
 * Roblox Specification Extractor
 * 
 * Utility functions for extracting structured Roblox environment specifications
 * from natural language input using pattern matching and NLP techniques.
 */

export interface RobloxSpec {
  environment_name?: string;
  theme?: string;
  map_type?: 'obby' | 'open_world' | 'dungeon' | 'lab' | 'classroom' | 'puzzle';
  difficulty?: 'easy' | 'medium' | 'hard';
  npc_count?: number;
  learning_objectives?: string[];
  terrain?: string;
  target_age?: string;
  duration?: number;
  features?: string[];
}

export interface ExtractionResult {
  spec: RobloxSpec;
  missingFields: string[];
  confidence: number;
  suggestions: string[];
}

const REQUIRED_FIELDS = ['environment_name', 'theme', 'map_type', 'learning_objectives'];

const FIELD_QUESTIONS: Record<string, string> = {
  environment_name: 'What should we name this Roblox environment?',
  theme: 'What is the theme or style (e.g., space station, medieval castle, jungle)?',
  map_type: 'Which map type fits best (obby, open_world, dungeon, lab, classroom, puzzle)?',
  learning_objectives: 'What are the key learning objectives or topics to cover?',
  difficulty: 'What difficulty level should this be (easy, medium, hard)?',
  target_age: 'What age group is this designed for?',
  npc_count: 'How many NPCs or characters should be included?'
};

/**
 * Extract environment name from text using various patterns
 */
function extractEnvironmentName(text: string): string | undefined {
  const patterns = [
    /(?:call it|named|name(?:d)?(?: as)?|title(?:d)?)\s+([\w\s'-]{3,40})/i,
    /environment\s*(?:name|title)\s*:?\s*([\w\s'-]{3,40})/i,
    /"([^"]{3,40})"/,
    /'([^']{3,40})'/
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return match[1].trim();
    }
  }
  return undefined;
}

/**
 * Extract map type from text
 */
function extractMapType(text: string): RobloxSpec['map_type'] {
  const lower = text.toLowerCase();
  
  if (lower.includes('obby') || lower.includes('obstacle course')) return 'obby';
  if (lower.includes('open world') || lower.includes('sandbox')) return 'open_world';
  if (lower.includes('dungeon') || lower.includes('cave')) return 'dungeon';
  if (lower.includes('lab') || lower.includes('laboratory')) return 'lab';
  if (lower.includes('classroom') || lower.includes('school')) return 'classroom';
  if (lower.includes('puzzle') || lower.includes('brain teaser')) return 'puzzle';
  
  return undefined;
}

/**
 * Extract theme from text
 */
function extractTheme(text: string): string | undefined {
  const patterns = [
    /(?:theme|style)\s*:?\s*([^
.!?]{3,50})/i,
    /(?:set in|takes place in|located in)\s+([^
.!?]{3,50})/i,
    /(?:medieval|space|jungle|underwater|desert|arctic|fantasy|sci-fi|historical)/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return match[1] ? match[1].trim() : match[0].trim();
    }
  }
  return undefined;
}

/**
 * Extract difficulty level
 */
function extractDifficulty(text: string): RobloxSpec['difficulty'] {
  const match = text.match(/\b(easy|medium|hard|beginner|intermediate|advanced)\b/i);
  if (match) {
    const level = match[1].toLowerCase();
    if (level === 'beginner') return 'easy';
    if (level === 'intermediate') return 'medium';
    if (level === 'advanced') return 'hard';
    return level as RobloxSpec['difficulty'];
  }
  return undefined;
}

/**
 * Extract NPC count
 */
function extractNpcCount(text: string): number | undefined {
  const patterns = [
    /(?:npc|enemies|characters|bots)\s*:?\s*(\d{1,3})/i,
    /(\d{1,3})\s*(?:npc|enemies|characters|bots)/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      const count = parseInt(match[1], 10);
      return count > 0 && count <= 100 ? count : undefined;
    }
  }
  return undefined;
}

/**
 * Extract learning objectives
 */
function extractLearningObjectives(text: string): string[] | undefined {
  const patterns = [
    /(?:objective|learning objective|goal)s?\s*:?\s*([^
]+)/i,
    /(?:teach|learn|practice|study)\s+([^
.!?]+)/i,
    /(?:about|covering|focusing on)\s+([^
.!?]+)/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return match[1]
        .split(/,|;|\band\b/i)
        .map(s => s.trim())
        .filter(s => s.length > 2);
    }
  }
  return undefined;
}

/**
 * Extract target age group
 */
function extractTargetAge(text: string): string | undefined {
  const patterns = [
    /(?:grade|year)\s*(\d{1,2})/i,
    /(?:age|ages)\s*(\d{1,2}(?:\s*-\s*\d{1,2})?)/i,
    /(\d{1,2})\s*(?:year|yr)\s*old/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return match[1];
    }
  }
  return undefined;
}

/**
 * Extract estimated duration
 */
function extractDuration(text: string): number | undefined {
  const patterns = [
    /(\d{1,3})\s*(?:minute|min)s?/i,
    /(\d{1,2})\s*(?:hour|hr)s?/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      const value = parseInt(match[1], 10);
      const unit = pattern.source.includes('hour') ? 'hours' : 'minutes';
      return unit === 'hours' ? value * 60 : value;
    }
  }
  return undefined;
}

/**
 * Calculate confidence score based on extracted fields
 */
function calculateConfidence(spec: RobloxSpec): number {
  const weights = {
    environment_name: 0.2,
    theme: 0.2,
    map_type: 0.2,
    learning_objectives: 0.3,
    difficulty: 0.1
  };

  let score = 0;
  for (const [field, weight] of Object.entries(weights)) {
    if (spec[field as keyof RobloxSpec]) {
      score += weight;
    }
  }

  return Math.round(score * 100);
}

/**
 * Generate suggestions based on missing fields and context
 */
function generateSuggestions(spec: RobloxSpec, missingFields: string[]): string[] {
  const suggestions: string[] = [];

  // Suggest based on existing fields
  if (spec.theme && !spec.map_type) {
    if (spec.theme.toLowerCase().includes('space')) {
      suggestions.push('Consider making this an open world space exploration environment');
    } else if (spec.theme.toLowerCase().includes('medieval')) {
      suggestions.push('This could work well as a dungeon or castle exploration map');
    }
  }

  if (spec.map_type && !spec.difficulty) {
    if (spec.map_type === 'obby') {
      suggestions.push('Obbies typically work well with medium difficulty for engagement');
    } else if (spec.map_type === 'classroom') {
      suggestions.push('Educational environments often benefit from easy to medium difficulty');
    }
  }

  // Add specific missing field suggestions
  missingFields.forEach(field => {
    if (FIELD_QUESTIONS[field]) {
      suggestions.push(FIELD_QUESTIONS[field]);
    }
  });

  return suggestions;
}

/**
 * Main extraction function
 */
export function extractRobloxSpec(text: string): ExtractionResult {
  const spec: RobloxSpec = {};

  // Extract all fields
  spec.environment_name = extractEnvironmentName(text);
  spec.theme = extractTheme(text);
  spec.map_type = extractMapType(text);
  spec.difficulty = extractDifficulty(text);
  spec.npc_count = extractNpcCount(text);
  spec.learning_objectives = extractLearningObjectives(text);
  spec.target_age = extractTargetAge(text);
  spec.duration = extractDuration(text);

  // Determine missing required fields
  const missingFields = REQUIRED_FIELDS.filter(field => {
    const value = spec[field as keyof RobloxSpec];
    return !value || (Array.isArray(value) && value.length === 0);
  });

  // Calculate confidence and generate suggestions
  const confidence = calculateConfidence(spec);
  const suggestions = generateSuggestions(spec, missingFields);

  return {
    spec,
    missingFields,
    confidence,
    suggestions
  };
}

/**
 * Validate a complete Roblox specification
 */
export function validateRobloxSpec(spec: RobloxSpec): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!spec.environment_name || spec.environment_name.length < 3) {
    errors.push('Environment name must be at least 3 characters long');
  }

  if (!spec.theme || spec.theme.length < 3) {
    errors.push('Theme must be specified and descriptive');
  }

  if (!spec.map_type) {
    errors.push('Map type must be selected');
  }

  if (!spec.learning_objectives || spec.learning_objectives.length === 0) {
    errors.push('At least one learning objective must be specified');
  }

  if (spec.npc_count && (spec.npc_count < 0 || spec.npc_count > 100)) {
    errors.push('NPC count must be between 0 and 100');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * Generate a human-readable summary of the specification
 */
export function summarizeSpec(spec: RobloxSpec): string {
  const parts: string[] = [];

  if (spec.environment_name) {
    parts.push(`"${spec.environment_name}"`);
  }

  if (spec.map_type) {
    parts.push(`${spec.map_type} environment`);
  }

  if (spec.theme) {
    parts.push(`with ${spec.theme} theme`);
  }

  if (spec.difficulty) {
    parts.push(`(${spec.difficulty} difficulty)`);
  }

  if (spec.learning_objectives && spec.learning_objectives.length > 0) {
    parts.push(`focusing on ${spec.learning_objectives.join(', ')}`);
  }

  return parts.join(' ') || 'Roblox environment specification';
}