/**
 * Roblox Character Avatar Component
 * 
 * Displays character avatars from the parsed design assets
 * with fun animations and interactions for kids
 */

import React, { useState, useEffect } from 'react';
import {
  Avatar,
  Box,
  Tooltip,
  Zoom,
  Fade,
  Badge,
  IconButton,
  Typography,
  Chip,
  Stack,
  useTheme,
  alpha
} from '@mui/material';
import {
  RocketLaunch,
  Star,
  EmojiEvents,
  AutoAwesome
} from '@mui/icons-material';

interface CharacterData {
  name: string;
  type: 'astronaut' | 'alien' | 'robot';
  level: number;
  xp: number;
  achievements: string[];
  isActive: boolean;
  imagePath: string;
}

interface RobloxCharacterAvatarProps {
  character: CharacterData;
  size?: 'small' | 'medium' | 'large';
  showLevel?: boolean;
  showXP?: boolean;
  animated?: boolean;
  onClick?: () => void;
}

const CHARACTER_IMAGES = {
  astronaut: '/images/characters/PNG/Astronauto (variation)/01.png',
  alien: '/images/characters/PNG/Aliens/back.png',
  robot: '/images/characters/PNG/Astronauto (variation)/02.png'
};

export const RobloxCharacterAvatar: React.FC<RobloxCharacterAvatarProps> = ({
  character,
  size = 'medium',
  showLevel = true,
  showXP = true,
  animated = true,
  onClick
}) => {
  const theme = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  const sizeMap = {
    small: 40,
    medium: 64,
    large: 96
  };

  const avatarSize = sizeMap[size];

  useEffect(() => {
    if (animated && character.isActive) {
      const interval = setInterval(() => {
        setIsAnimating(true);
        setTimeout(() => setIsAnimating(false), 1000);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [animated, character.isActive]);

  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };

  return (
    <Box
      sx={{
        position: 'relative',
        display: 'inline-block',
        cursor: onClick ? 'pointer' : 'default',
        transform: isHovered ? 'scale(1.1)' : 'scale(1)',
        transition: 'transform 0.3s ease',
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
    >
      <Tooltip
        title={
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              {character.name}
            </Typography>
            {showLevel && (
              <Typography variant="body2" color="text.secondary">
                Level {character.level}
              </Typography>
            )}
            {showXP && (
              <Typography variant="body2" color="text.secondary">
                {character.xp} XP
              </Typography>
            )}
            {character.achievements.length > 0 && (
              <Stack direction="row" spacing={0.5} sx={{ mt: 1 }}>
                {character.achievements.slice(0, 3).map((achievement, index) => (
                  <Chip
                    key={index}
                    label={achievement}
                    size="small"
                    sx={{
                      fontSize: '0.7rem',
                      height: 20,
                      background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                      color: 'white'
                    }}
                  />
                ))}
              </Stack>
            )}
          </Box>
        }
        arrow
        placement="top"
      >
        <Badge
          overlap="circular"
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          badgeContent={
            character.isActive ? (
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background: `linear-gradient(135deg, #4caf50, #8bc34a)`,
                  boxShadow: `0 0 10px #4caf50`,
                  animation: isAnimating ? 'pulse 1s ease-in-out' : 'none',
                  '@keyframes pulse': {
                    '0%': { transform: 'scale(1)', opacity: 1 },
                    '50%': { transform: 'scale(1.2)', opacity: 0.7 },
                    '100%': { transform: 'scale(1)', opacity: 1 }
                  }
                }}
              />
            ) : null
          }
        >
          <Avatar
            src={CHARACTER_IMAGES[character.type]}
            sx={{
              width: avatarSize,
              height: avatarSize,
              border: `3px solid ${alpha(theme.palette.primary.main, 0.3)}`,
              boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.3)}`,
              transition: 'all 0.3s ease',
              '&:hover': {
                border: `3px solid ${theme.palette.primary.main}`,
                boxShadow: `0 8px 30px ${alpha(theme.palette.primary.main, 0.5)}`,
              }
            }}
          />
        </Badge>
      </Tooltip>

      {/* Floating icons for active characters */}
      {character.isActive && animated && (
        <Box
          sx={{
            position: 'absolute',
            top: -10,
            right: -10,
            animation: 'float 2s ease-in-out infinite',
            '@keyframes float': {
              '0%, 100%': { transform: 'translateY(0px)' },
              '50%': { transform: 'translateY(-10px)' }
            }
          }}
        >
          <IconButton
            size="small"
            sx={{
              color: theme.palette.warning.main,
              background: alpha(theme.palette.warning.main, 0.1),
              '&:hover': {
                background: alpha(theme.palette.warning.main, 0.2),
              }
            }}
          >
            <Star fontSize="small" />
          </IconButton>
        </Box>
      )}
    </Box>
  );
};

export default RobloxCharacterAvatar;
