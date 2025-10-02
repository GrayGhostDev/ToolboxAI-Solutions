/**
 * Roblox Character Avatar Component
 *
 * Displays character avatars from the parsed design assets
 * with fun animations and interactions for kids
 */

import React, { useState } from 'react';
import {
  Box,
  Tooltip,
  Badge,
  ActionIcon,
  Text,
  Group,
  useMantineTheme
} from '@mantine/core';
import {
  IconStar
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

// CSS animation classes - defined in global styles or inline
const floatAnimationCSS = `
  @keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
  }
`;

const pulseAnimationCSS = `
  @keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.2); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
  }
`;

// Inline styles function
const getStyles = (isHovered: boolean, isActive: boolean) => ({
  container: {
    position: 'relative' as const,
    display: 'inline-block',
    cursor: 'pointer',
    transform: isHovered ? 'scale(1.1)' : 'scale(1)',
    transition: 'transform 0.3s ease'
  },
  activeIndicator: {
    width: 12,
    height: 12,
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #4caf50, #8bc34a)',
    boxShadow: '0 0 10px #4caf50',
    animation: isActive ? 'pulse 1s ease-in-out infinite' : 'none'
  },
  floatingIcon: {
    position: 'absolute' as const,
    top: -10,
    right: -10,
    animation: 'float 2s ease-in-out infinite'
  }
});

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
  const styles = getStyles(isHovered, character.isActive);

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

  return (
    <Box
      style={{
        position: 'relative',
        display: 'inline-block',
        cursor: 'pointer',
        transition: 'transform 0.3s ease',
        transform: isHovered ? 'scale(1.05)' : 'scale(1)',
        animation: animated ? 'float 3s ease-in-out infinite' : 'none'
      }}
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
              <Group spacing="xs" mt="xs">
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
        <Badge
          variant="dot"
          color={character.isActive ? 'green' : 'gray'}
          size="lg"
          style={{
            position: 'relative'
          }}
          styles={{
            indicator: {
              width: 8,
              height: 8,
              borderRadius: '50%',
              animation: character.isActive ? 'pulse 2s ease-in-out infinite' : 'none'
            }
          }}
        >
          <Procedural3DCharacter
            characterType={character.type}
            size={size}
            animated={animated}
            style={{
              width: avatarSize,
              height: avatarSize,
              boxShadow: `0 4px 20px rgba(37, 99, 235, 0.3)`,
              transition: 'all 0.3s ease',
              borderRadius: '50%'
            }}
          />
        </Badge>
      </Tooltip>

      {/* Floating icons for active characters */}
      {character.isActive && animated && (
        <Box style={{
          position: 'absolute',
          top: -10,
          right: -10,
          animation: 'float 2s ease-in-out infinite',
          zIndex: 1
        }}>
          <ActionIcon
            size="sm"
            variant="light"
            color="yellow"
            style={{
              background: 'rgba(255, 193, 7, 0.1)'
            }}
            styles={{
              root: {
                '&:hover': {
                  background: 'rgba(255, 193, 7, 0.2)'
                }
              }
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
