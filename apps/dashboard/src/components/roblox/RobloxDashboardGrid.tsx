/**
 * Roblox Dashboard Grid Component
 * 
 * Displays a grid of 3D icons and interactive elements
 * with futuristic animations and hover effects
 */

import React, { useState, useEffect } from 'react';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Fade from '@mui/material/Fade';
import Zoom from '@mui/material/Zoom';
import Slide from '@mui/material/Slide';
import { useTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';
import {
  PlayArrow,
  Pause,
  Refresh,
  Star,
  EmojiEvents,
  TrendingUp,
  School,
  SportsEsports,
  Psychology,
  Groups,
  Games,
  AutoAwesome
} from '@mui/icons-material';
import { Roblox3DIcon } from './Roblox3DIcon';

interface DashboardItem {
  id: string;
  name: string;
  type: 'education' | 'gaming' | 'tool' | 'achievement';
  category: string;
  level: number;
  isUnlocked: boolean;
  progress: number;
  maxProgress: number;
  description: string;
  icon: string;
  isActive: boolean;
  lastUsed?: Date;
}

interface RobloxDashboardGridProps {
  items: DashboardItem[];
  onItemClick?: (item: DashboardItem) => void;
  onItemPlay?: (item: DashboardItem) => void;
  onItemPause?: (item: DashboardItem) => void;
  onItemRefresh?: (item: DashboardItem) => void;
}

const SAMPLE_ITEMS: DashboardItem[] = [
  {
    id: '1',
    name: 'ABC_CUBE',
    type: 'education',
    category: 'Language',
    level: 3,
    isUnlocked: true,
    progress: 75,
    maxProgress: 100,
    description: 'Learn the alphabet with interactive 3D cubes',
    icon: 'ABC_CUBE',
    isActive: true,
    lastUsed: new Date()
  },
  {
    id: '2',
    name: 'MATH_BOARD',
    type: 'education',
    category: 'Mathematics',
    level: 2,
    isUnlocked: true,
    progress: 45,
    maxProgress: 100,
    description: 'Solve math problems on the interactive board',
    icon: 'BOARD',
    isActive: false,
    lastUsed: new Date(Date.now() - 3600000)
  },
  {
    id: '3',
    name: 'SPACE_QUIZ',
    type: 'education',
    category: 'Science',
    level: 4,
    isUnlocked: true,
    progress: 90,
    maxProgress: 100,
    description: 'Test your knowledge about space and planets',
    icon: 'LIGHT_BULB',
    isActive: false,
    lastUsed: new Date(Date.now() - 7200000)
  },
  {
    id: '4',
    name: 'SPORTS_CHALLENGE',
    type: 'gaming',
    category: 'Physical Education',
    level: 1,
    isUnlocked: true,
    progress: 20,
    maxProgress: 100,
    description: 'Complete physical challenges and sports activities',
    icon: 'BASKETBALL',
    isActive: false,
    lastUsed: new Date(Date.now() - 86400000)
  },
  {
    id: '5',
    name: 'ART_STUDIO',
    type: 'tool',
    category: 'Creative Arts',
    level: 2,
    isUnlocked: true,
    progress: 60,
    maxProgress: 100,
    description: 'Create digital art with brushes and colors',
    icon: 'CRAYON',
    isActive: false,
    lastUsed: new Date(Date.now() - 172800000)
  },
  {
    id: '6',
    name: 'ACHIEVEMENT_HALL',
    type: 'achievement',
    category: 'Recognition',
    level: 5,
    isUnlocked: true,
    progress: 100,
    maxProgress: 100,
    description: 'View all your earned achievements and badges',
    icon: 'TROPHY',
    isActive: false,
    lastUsed: new Date(Date.now() - 259200000)
  }
];

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'education': return School;
    case 'gaming': return SportsEsports;
    case 'tool': return Psychology;
    case 'achievement': return EmojiEvents;
    default: return AutoAwesome;
  }
};

const getTypeColor = (type: string, theme: any) => {
  switch (type) {
    case 'education': return theme.palette.primary.main;
    case 'gaming': return theme.palette.secondary.main;
    case 'tool': return theme.palette.info.main;
    case 'achievement': return theme.palette.warning.main;
    default: return theme.palette.grey[500];
  }
};

export const RobloxDashboardGrid: React.FunctionComponent<RobloxDashboardGridProps> = ({
  items = SAMPLE_ITEMS,
  onItemClick,
  onItemPlay,
  onItemPause,
  onItemRefresh
}) => {
  const theme = useTheme();
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    setIsAnimating(true);
    const timer = setTimeout(() => setIsAnimating(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleItemClick = (item: DashboardItem) => {
    if (onItemClick) {
      onItemClick(item);
    }
  };

  const handleItemPlay = (item: DashboardItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (onItemPlay) {
      onItemPlay(item);
    }
  };

  const handleItemPause = (item: DashboardItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (onItemPause) {
      onItemPause(item);
    }
  };

  const handleItemRefresh = (item: DashboardItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (onItemRefresh) {
      onItemRefresh(item);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Fade in={isAnimating} timeout={1000}>
        <Typography
          variant="h4"
          sx={{
            mb: 3,
            fontWeight: 700,
            background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            textAlign: 'center'
          }}
        >
          Your Learning Tools
        </Typography>
      </Fade>

      <Grid container spacing={3}>
        {items.map((item, index) => {
          const TypeIcon = getTypeIcon(item.type);
          const typeColor = getTypeColor(item.type, theme);
          const progressPercentage = (item.progress / item.maxProgress) * 100;

          return (
            <Grid item xs={12} sm={6} md={4} lg={3} key={item.id}>
              <Zoom
                in={isAnimating}
                timeout={1000 + index * 200}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                <Card
                  sx={{
                    height: '100%',
                    background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(typeColor, 0.05)})`,
                    border: `2px solid ${alpha(typeColor, 0.2)}`,
                    borderRadius: 3,
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    cursor: item.isUnlocked ? 'pointer' : 'default',
                    transform: hoveredItem === item.id ? 'translateY(-8px) scale(1.02)' : 'translateY(0) scale(1)',
                    boxShadow: hoveredItem === item.id 
                      ? `0 20px 40px ${alpha(typeColor, 0.3)}`
                      : `0 8px 25px ${alpha(typeColor, 0.1)}`,
                    '&:hover': {
                      border: `2px solid ${typeColor}`,
                      boxShadow: `0 20px 40px ${alpha(typeColor, 0.3)}`,
                    }
                  }}
                  onMouseEnter={() => setHoveredItem(item.id)}
                  onMouseLeave={() => setHoveredItem(null)}
                  onClick={(e: React.MouseEvent) => () => handleItemClick(item)}
                >
                  <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                    {/* Header with icon and actions */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Roblox3DIcon
                          icon={{
                            name: item.icon,
                            type: item.type,
                            category: item.category,
                            level: item.level,
                            isUnlocked: item.isUnlocked,
                            imagePath: '',
                            description: item.description
                          }}
                          size="large"
                          animated={true}
                        />
                        <Box>
                          <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                            {item.name.replace(/_/g, ' ')}
                          </Typography>
                          <Chip
                            label={item.category}
                            size="small"
                            sx={{
                              background: `linear-gradient(135deg, ${typeColor}, ${alpha(typeColor, 0.7)})`,
                              color: 'white',
                              fontWeight: 600
                            }}
                          />
                        </Box>
                      </Box>

                      {/* Action buttons */}
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        {item.isActive ? (
                          <Tooltip title="Pause">
                            <IconButton
                              size="small"
                              onClick={(e: React.MouseEvent) => (e) => handleItemPause(item, e)}
                              sx={{
                                color: theme.palette.warning.main,
                                background: alpha(theme.palette.warning.main, 0.1),
                                '&:hover': {
                                  background: alpha(theme.palette.warning.main, 0.2),
                                }
                              }}
                            >
                              <Pause fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        ) : (
                          <Tooltip title="Play">
                            <IconButton
                              size="small"
                              onClick={(e: React.MouseEvent) => (e) => handleItemPlay(item, e)}
                              sx={{
                                color: theme.palette.success.main,
                                background: alpha(theme.palette.success.main, 0.1),
                                '&:hover': {
                                  background: alpha(theme.palette.success.main, 0.2),
                                }
                              }}
                            >
                              <PlayArrow fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        
                        <Tooltip title="Refresh">
                          <IconButton
                            size="small"
                            onClick={(e: React.MouseEvent) => (e) => handleItemRefresh(item, e)}
                            sx={{
                              color: theme.palette.info.main,
                              background: alpha(theme.palette.info.main, 0.1),
                              '&:hover': {
                                background: alpha(theme.palette.info.main, 0.2),
                              }
                            }}
                          >
                            <Refresh fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>

                    {/* Description */}
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 2, flex: 1 }}
                    >
                      {item.description}
                    </Typography>

                    {/* Progress section */}
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          Progress
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {item.progress}/{item.maxProgress}
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={progressPercentage}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          background: alpha(typeColor, 0.1),
                          '& .MuiLinearProgress-bar': {
                            background: `linear-gradient(90deg, ${typeColor}, ${alpha(typeColor, 0.7)})`,
                            borderRadius: 4,
                          }
                        }}
                      />
                    </Box>

                    {/* Level and status */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <TypeIcon sx={{ fontSize: 16, color: typeColor }} />
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          Level {item.level}
                        </Typography>
                      </Box>
                      
                      {item.isActive && (
                        <Chip
                          label="Active"
                          size="small"
                          sx={{
                            background: `linear-gradient(135deg, ${theme.palette.success.main}, ${alpha(theme.palette.success.main, 0.7)})`,
                            color: 'white',
                            fontWeight: 600,
                            animation: 'pulse 2s infinite',
                            '@keyframes pulse': {
                              '0%, 100%': { opacity: 1 },
                              '50%': { opacity: 0.7 }
                            }
                          }}
                        />
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Zoom>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

export default RobloxDashboardGrid;
