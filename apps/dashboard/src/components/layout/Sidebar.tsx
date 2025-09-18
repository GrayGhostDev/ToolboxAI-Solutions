import * as React from "react";
import { Link, useLocation } from "react-router-dom";
import Drawer from "@mui/material/Drawer";
import Toolbar from "@mui/material/Toolbar";
import List from "@mui/material/List";
import Divider from "@mui/material/Divider";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import LinearProgress from "@mui/material/LinearProgress";
import DashboardIcon from "@mui/icons-material/Dashboard";
import SchoolIcon from "@mui/icons-material/School";
import PeopleIcon from "@mui/icons-material/People";
import AssignmentIcon from "@mui/icons-material/Assignment";
import LeaderboardIcon from "@mui/icons-material/Leaderboard";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import SecurityIcon from "@mui/icons-material/Security";
import SettingsIcon from "@mui/icons-material/Settings";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import MessageIcon from "@mui/icons-material/Message";
import AssessmentIcon from "@mui/icons-material/Assessment";
import IntegrationInstructionsIcon from "@mui/icons-material/IntegrationInstructions";
import FlagIcon from "@mui/icons-material/Flag";
import GamesIcon from "@mui/icons-material/Games";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import { UserRole } from "../../types";
import { useAppSelector } from "../../store";

const drawerWidth = 240;

interface Props {
  role: UserRole;
}

const roleMenus: Record<UserRole, { label: string; icon: React.ReactNode; path: string }[]> = {
  admin: [
    { label: "Overview", icon: <DashboardIcon />, path: "/" },
    { label: "Schools", icon: <SchoolIcon />, path: "/schools" },
    { label: "Users", icon: <PeopleIcon />, path: "/users" },
    { label: "Compliance", icon: <SecurityIcon />, path: "/compliance" },
    { label: "Analytics", icon: <LeaderboardIcon />, path: "/analytics" },
    { label: "Agent System", icon: <SmartToyIcon />, path: "/agents" },
    { label: "Roblox Studio", icon: <GamesIcon />, path: "/roblox" },
    { label: "Integrations", icon: <IntegrationInstructionsIcon />, path: "/integrations" },
    { label: "Settings", icon: <SettingsIcon />, path: "/settings" },
  ],
  teacher: [
    { label: "Overview", icon: <DashboardIcon />, path: "/" },
    { label: "Classes", icon: <PeopleIcon />, path: "/classes" },
    { label: "Lessons", icon: <AssignmentIcon />, path: "/lessons" },
    { label: "Assessments", icon: <AssessmentIcon />, path: "/assessments" },
    { label: "Roblox Studio", icon: <GamesIcon />, path: "/roblox" },
    { label: "Reports", icon: <LeaderboardIcon />, path: "/reports" },
    { label: "Messages", icon: <MessageIcon />, path: "/messages" },
    { label: "Settings", icon: <SettingsIcon />, path: "/settings" },
  ],
  student: [
    { label: "Overview", icon: <DashboardIcon />, path: "/" },
    { label: "Missions", icon: <FlagIcon />, path: "/missions" },
    { label: "Progress", icon: <LeaderboardIcon />, path: "/progress" },
    { label: "Rewards", icon: <EmojiEventsIcon />, path: "/rewards" },
    { label: "Leaderboard", icon: <LeaderboardIcon />, path: "/leaderboard" },
    { label: "Avatar", icon: <AccountCircleIcon />, path: "/avatar" },
    { label: "Play", icon: <SportsEsportsIcon />, path: "/play" },
    { label: "Settings", icon: <SettingsIcon />, path: "/settings" },
  ],
  parent: [
    { label: "Overview", icon: <DashboardIcon />, path: "/" },
    { label: "Progress", icon: <LeaderboardIcon />, path: "/progress" },
    { label: "Reports", icon: <AssessmentIcon />, path: "/reports" },
    { label: "Messages", icon: <MessageIcon />, path: "/messages" },
    { label: "Settings", icon: <SettingsIcon />, path: "/settings" },
  ],
};

export default function Sidebar({ role }: Props) {
  const location = useLocation();
  const sidebarOpen = useAppSelector((s) => s.ui.sidebarOpen);
  const xp = useAppSelector((s) => s.gamification.xp);
  const level = useAppSelector((s) => s.gamification.level);
  const nextLevelXP = useAppSelector((s) => s.gamification.nextLevelXP);
  const displayName = useAppSelector((s) => s.user.displayName);
  const firstName = useAppSelector((s) => s.user.firstName);

  const progress = ((xp % 100) / 100) * 100;
  
  // Roles are already normalized as lowercase strings matching UserRole
  const menuItems = roleMenus[role] || roleMenus.student;

  return (
    <Drawer
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: drawerWidth,
          boxSizing: "border-box",
          background: "linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%)",
          color: "white",
          borderRight: "2px solid #00bcd4",
          boxShadow: "0 0 20px rgba(0, 188, 212, 0.3)",
        },
      }}
      variant="persistent"
      anchor="left"
      open={sidebarOpen}
    >
      <Toolbar />
      
      {/* User Info Section */}
      <Box sx={{ 
        p: 2, 
        textAlign: "center",
        background: "linear-gradient(135deg, rgba(0, 188, 212, 0.1), rgba(233, 30, 99, 0.1))",
        border: "1px solid rgba(0, 188, 212, 0.3)",
        borderRadius: 2,
        m: 2,
        mb: 1
      }}>
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 700, 
            mb: 1,
            background: "linear-gradient(135deg, #00bcd4, #e91e63)",
            backgroundClip: "text",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            textShadow: "0 0 10px rgba(0, 188, 212, 0.5)"
          }}
        >
          {firstName || displayName || role}
        </Typography>
        
        {/* XP Progress for Students */}
        {role === "student" && (
          <Box sx={{ mt: 2 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                Level {level}
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                {xp} / {nextLevelXP} XP
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: "rgba(255,255,255,0.1)",
                "& .MuiLinearProgress-bar": {
                  background: "linear-gradient(90deg, #9333EA 0%, #14B8A6 100%)",
                },
              }}
            />
          </Box>
        )}
      </Box>
      
      <Divider sx={{ bgcolor: "rgba(255,255,255,0.1)" }} />
      
      {/* Navigation Menu */}
      <List sx={{ px: 1, py: 2 }}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                component={Link}
                to={item.path}
                selected={isActive}
                sx={{
                  borderRadius: 2,
                  transition: "all 0.3s ease",
                  "&.Mui-selected": {
                    background: "linear-gradient(135deg, #00bcd4, #e91e63)",
                    color: "white",
                    boxShadow: "0 4px 15px rgba(0, 188, 212, 0.4)",
                    "&:hover": {
                      background: "linear-gradient(135deg, #0097a7, #c2185b)",
                      boxShadow: "0 6px 20px rgba(0, 188, 212, 0.6)",
                    },
                  },
                  "&:hover": {
                    background: "linear-gradient(135deg, rgba(0, 188, 212, 0.1), rgba(233, 30, 99, 0.1))",
                    border: "1px solid rgba(0, 188, 212, 0.3)",
                    transform: "translateX(4px)",
                  },
                }}
              >
                <ListItemIcon sx={{ color: "inherit", minWidth: 40 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: "0.875rem",
                    fontWeight: isActive ? 600 : 400,
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
      
      {/* Quick Stats for Teachers/Admins */}
      {(role === "teacher" || role === "admin") && (
        <>
          <Divider sx={{ bgcolor: "rgba(255,255,255,0.1)" }} />
          <Box sx={{ p: 2 }}>
            <Typography variant="caption" sx={{ opacity: 0.6, display: "block", mb: 1 }}>
              QUICK STATS
            </Typography>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
              <Typography variant="caption">Active Classes</Typography>
              <Typography variant="caption" sx={{ fontWeight: 600 }}>
                4
              </Typography>
            </Box>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
              <Typography variant="caption">Total Students</Typography>
              <Typography variant="caption" sx={{ fontWeight: 600 }}>
                86
              </Typography>
            </Box>
            <Box sx={{ display: "flex", justifyContent: "space-between" }}>
              <Typography variant="caption">Pending Tasks</Typography>
              <Typography variant="caption" sx={{ fontWeight: 600 }}>
                12
              </Typography>
            </Box>
          </Box>
        </>
      )}
    </Drawer>
  );
}