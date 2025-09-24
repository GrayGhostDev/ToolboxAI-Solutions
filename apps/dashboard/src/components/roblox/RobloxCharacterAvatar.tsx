/**
 * Roblox Character Avatar Component
 * 
 * Displays character avatars from the parsed design assets
 * with fun animations and interactions for kids
 */

import React, { useState } from 'react';
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Zoom from '@mui/material/Zoom';
import Fade from '@mui/material/Fade';
import Badge from '@mui/material/Badge';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import { useTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';
import CircularProgress from '@mui/material/CircularProgress';
import {
  RocketLaunch,
  Star,
  EmojiEvents,
  AutoAwesome
} from '@mui/icons-material';
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

// Character images will be loaded dynamically from design_files

export const RobloxCharacterAvatar: React.FunctionComponent<RobloxCharacterAvatarProps> = ({
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
      onClick={(e: React.MouseEvent) => handleClick}
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
          <Procedural3DCharacter
            characterType={character.type}
            size={size}
            animated={animated}
            style={{
              width: avatarSize,
              height: avatarSize,
              boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.3)}`,
              transition: 'all 0.3s ease',
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
