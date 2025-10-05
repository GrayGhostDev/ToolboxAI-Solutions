/**
 * Roblox Character Avatar Component
 *
 * Displays character avatars from the parsed design assets
 * with fun animations and interactions for kids
 */

import React, { useState } from 'react';
import {
  Avatar,
  Box,
  Tooltip,
  Transition,
  Badge,
  ActionIcon,
  Text,
  Group,
  useMantineTheme,
  rem
} from '@mantine/core';
import {
  IconRocket,
  IconStar,
  IconTrophy,
  IconSparkles
} from '@tabler/icons-react';
import { Procedural3DCharacter } from './Procedural3DCharacter';

interface CharacterData {
  name: string;
  type: 'astronaut' | 'alien' | 'robot';
  level: number;
  xp: number;
  achievements: string[];
  isActive: boolean;
}

interface RobloxCharacterAvatarProps {
  character: CharacterData;
  size?: 'small' | 'medium' | 'large';
  showLevel?: boolean;
  showXP?: boolean;
  animated?: boolean;
  onClick?: () => void;
}

// Keyframe animations defined as string (CSS-in-JS)
const floatAnimation = `
  @keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
  }
`;

const pulseAnimation = `
  @keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.2); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
  }
`;

// Inject animations into document head
if (typeof document !== 'undefined') {
  const styleId = 'roblox-character-animations';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = floatAnimation + pulseAnimation;
    document.head.appendChild(style);
  }
}

// Character images will be loaded dynamically from design_files

export const RobloxCharacterAvatar: React.FunctionComponent<RobloxCharacterAvatarProps> = ({
  character,
  size = 'medium',
  showLevel = true,
  showXP = true,
  animated = true,
  onClick
}) => {
  const theme = useMantineTheme();
  const [isHovered, setIsHovered] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  const sizeMap = {
    small: 40,
    medium: 64,
    large: 96
  };

  const avatarSize = sizeMap[size];

  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };

  // Container styles
  const containerStyle: React.CSSProperties = {
    position: 'relative',
    display: 'inline-block',
    cursor: 'pointer',
    transform: isHovered ? 'scale(1.1)' : 'scale(1)',
    transition: 'transform 0.3s ease'
  };

  // Active indicator styles
  const activeIndicatorStyle: React.CSSProperties = {
    width: 12,
    height: 12,
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #4caf50, #8bc34a)',
    boxShadow: '0 0 10px #4caf50',
    animation: character.isActive ? 'pulse 1s ease-in-out infinite' : 'none'
  };

  // Floating icon styles
  const floatingIconStyle: React.CSSProperties = {
    position: 'absolute',
    top: -10,
    right: -10,
    animation: 'float 2s ease-in-out infinite'
  };

  return (
    <Box
      style={containerStyle}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
    >
      <Tooltip
        label={
          <Box>
            <Text size="sm" fw={600} mb="xs">
              {character.name}
            </Text>
            {showLevel && (
              <Text size="sm" c="dimmed">
                Level {character.level}
              </Text>
            )}
            {showXP && (
              <Text size="sm" c="dimmed">
                {character.xp} XP
              </Text>
            )}
            {character.achievements.length > 0 && (
              <Group gap="xs" mt="xs">
                {character.achievements.slice(0, 3).map((achievement, index) => (
                  <Badge
                    key={index}
                    size="xs"
                    style={{
                      background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
                      color: 'white'
                    }}
                  >
                    {achievement}
                  </Badge>
                ))}
              </Group>
            )}
          </Box>
        }
        withArrow
        position="top"
      >
        <Box style={{ position: 'relative' }}>
          {character.isActive && (
            <Box
              style={{
                position: 'absolute',
                top: -2,
                right: -2,
                zIndex: 1,
                ...activeIndicatorStyle
              }}
            />
          )}
          <Procedural3DCharacter
            characterType={character.type}
            size={size}
            animated={animated}
            style={{
              width: avatarSize,
              height: avatarSize,
              boxShadow: `0 4px 20px rgba(66, 153, 225, 0.3)`,
              transition: 'all 0.3s ease',
              borderRadius: '50%'
            }}
          />
        </Box>
      </Tooltip>

      {/* Floating icons for active characters */}
      {character.isActive && animated && (
        <Box style={floatingIconStyle}>
          <ActionIcon
            size="sm"
            variant="light"
            color="yellow"
            style={{
              background: 'rgba(250, 204, 21, 0.1)'
            }}
          >
            <IconStar size={16} />
          </ActionIcon>
        </Box>
      )}
    </Box>
  );
};

export default RobloxCharacterAvatar;
