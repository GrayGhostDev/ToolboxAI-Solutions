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
import { createStyles, keyframes } from '@mantine/emotion';
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

// Animations
const floatAnimation = keyframes({
  '0%, 100%': { transform: 'translateY(0px)' },
  '50%': { transform: 'translateY(-10px)' }
});

const pulseAnimation = keyframes({
  '0%': { transform: 'scale(1)', opacity: 1 },
  '50%': { transform: 'scale(1.2)', opacity: 0.7 },
  '100%': { transform: 'scale(1)', opacity: 1 }
});

const useStyles = createStyles((theme, { isHovered, isActive }: { isHovered: boolean; isActive: boolean }) => ({
  container: {
    position: 'relative',
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
    animation: isActive ? `${pulseAnimation} 1s ease-in-out infinite` : 'none'
  },
  floatingIcon: {
    position: 'absolute',
    top: -10,
    right: -10,
    animation: `${floatAnimation} 2s ease-in-out infinite`
  }
}));

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
  const { classes } = useStyles({ isHovered, isActive: character.isActive });

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
      className={classes.container}
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
              ...classes.activeIndicator
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
              boxShadow: `0 4px 20px ${theme.fn.rgba(theme.colors.blue[6], 0.3)}`,
              transition: 'all 0.3s ease',
              borderRadius: '50%'
            }}
          />
        </Badge>
      </Tooltip>

      {/* Floating icons for active characters */}
      {character.isActive && animated && (
        <Box className={classes.floatingIcon}>
          <ActionIcon
            size="sm"
            variant="light"
            color="yellow"
            style={{
              background: theme.fn.rgba(theme.colors.yellow[6], 0.1)
            }}
            styles={{
              root: {
                '&:hover': {
                  background: theme.fn.rgba(theme.colors.yellow[6], 0.2)
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