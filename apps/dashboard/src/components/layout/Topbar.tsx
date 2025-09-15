import * as React from "react";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import Badge from "@mui/material/Badge";
import Avatar from "@mui/material/Avatar";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import FormControl from "@mui/material/FormControl";
import Tooltip from "@mui/material/Tooltip";
import NotificationsIcon from "@mui/icons-material/Notifications";
import MenuIcon from "@mui/icons-material/Menu";
import LanguageIcon from "@mui/icons-material/Language";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import LogoutIcon from "@mui/icons-material/Logout";
import SettingsIcon from "@mui/icons-material/Settings";
import { UserRole } from "../../types";
import { useAppDispatch, useAppSelector } from "../../store";
import { toggleSidebar, setTheme, setLanguage } from "../../store/slices/uiSlice";
import { setRole, signOut } from "../../store/slices/userSlice";
import { useNavigate } from "react-router-dom";
import { LANGUAGES } from "../../config";
// import { wsService } from "../../services/ws";
import { disconnectWebSocket } from "../../services/websocket";
import ConnectionStatus from "../widgets/ConnectionStatus";

export default function Topbar() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const role = useAppSelector((s) => s.user.role);
  const displayName = useAppSelector((s) => s.user.displayName);
  const avatarUrl = useAppSelector((s) => s.user.avatarUrl);
  const theme = useAppSelector((s) => s.ui.theme);
  const language = useAppSelector((s) => s.ui.language);
  const notifications = useAppSelector((s) => s.ui.notifications);
  
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [notifAnchor, setNotifAnchor] = React.useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotifAnchor(event.currentTarget);
  };

  const handleNotificationClose = () => {
    setNotifAnchor(null);
  };

  const handleSignOut = () => {
    // Disconnect WebSocket before signing out
    disconnectWebSocket();
    dispatch(signOut());
    handleProfileMenuClose();
    navigate("/");
  };

  const handleSettings = () => {
    handleProfileMenuClose();
    navigate("/settings");
  };

  return (
    <AppBar
      elevation={0}
      position="fixed"
      sx={{
        backdropFilter: "blur(8px)",
        background: "linear-gradient(90deg, rgba(10, 10, 10, 0.95) 0%, rgba(26, 26, 26, 0.95) 100%)",
        color: "white",
        borderBottom: "2px solid #00bcd4",
        boxShadow: "0 4px 20px rgba(0, 188, 212, 0.3)",
      }}
    >
      <Toolbar sx={{ gap: 2 }}>
        <IconButton
          aria-label="Toggle navigation"
          onClick={() => dispatch(toggleSidebar())}
          edge="start"
        >
          <MenuIcon />
        </IconButton>
        
        <Typography 
          variant="h6" 
          sx={{ 
            flexGrow: 1, 
            fontWeight: 700,
            background: "linear-gradient(135deg, #00bcd4, #e91e63)",
            backgroundClip: "text",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            textShadow: "0 0 10px rgba(0, 188, 212, 0.5)"
          }}
        >
          🚀 Space Station Dashboard
        </Typography>

        {/* Role Selector */}
        <FormControl size="small" sx={{ minWidth: 100 }}>
          <Select
            value={role}
            onChange={(e) => dispatch(setRole(e.target.value as UserRole))}
            aria-label="Select role"
            sx={{ 
              fontSize: "0.875rem",
              background: "linear-gradient(135deg, rgba(0, 188, 212, 0.1), rgba(233, 30, 99, 0.1))",
              border: "1px solid rgba(0, 188, 212, 0.3)",
              borderRadius: 2,
              color: "white",
              "& .MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(0, 188, 212, 0.3)",
              },
              "&:hover .MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(0, 188, 212, 0.6)",
              },
              "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                borderColor: "#00bcd4",
              },
            }}
          >
            {(["admin", "teacher", "student", "parent"] as UserRole[]).map((r) => (
              <MenuItem key={r} value={r}>
                {r.charAt(0).toUpperCase() + r.slice(1)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Connection Status */}
        <ConnectionStatus showLabel={true} size="small" />

        {/* Language Selector */}
        <Tooltip title="Change language">
          <FormControl size="small">
            <Select
              value={language}
              onChange={(e) => dispatch(setLanguage(e.target.value))}
              renderValue={() => <LanguageIcon fontSize="small" />}
              sx={{ minWidth: 40 }}
            >
              {LANGUAGES.map((lang) => (
                <MenuItem key={lang.code} value={lang.code}>
                  {lang.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Tooltip>

        {/* Theme Toggle */}
        <Tooltip title="Toggle theme">
          <IconButton
            onClick={() => dispatch(setTheme(theme === "light" ? "dark" : "light"))}
            aria-label="Toggle theme"
          >
            {theme === "light" ? <DarkModeIcon /> : <LightModeIcon />}
          </IconButton>
        </Tooltip>

        {/* Notifications */}
        <Tooltip title="Notifications">
          <IconButton
            aria-label="Notifications"
            onClick={handleNotificationOpen}
          >
            <Badge badgeContent={notifications.length} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
        </Tooltip>

        {/* Profile Menu */}
        <Tooltip title="Profile menu">
          <IconButton onClick={handleProfileMenuOpen} sx={{ p: 0.5 }}>
            {avatarUrl ? (
              <Avatar src={avatarUrl} alt={displayName || "User"} sx={{ width: 32, height: 32 }} />
            ) : (
              <AccountCircleIcon />
            )}
          </IconButton>
        </Tooltip>

        {/* Profile Dropdown Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleProfileMenuClose}
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
          transformOrigin={{ vertical: "top", horizontal: "right" }}
        >
          <MenuItem disabled>
            <Typography variant="body2" color="text.secondary">
              {displayName || "Guest User"}
            </Typography>
          </MenuItem>
          <MenuItem onClick={handleSettings}>
            <SettingsIcon fontSize="small" sx={{ mr: 1 }} />
            Settings
          </MenuItem>
          <MenuItem onClick={handleSignOut}>
            <LogoutIcon fontSize="small" sx={{ mr: 1 }} />
            Sign Out
          </MenuItem>
        </Menu>

        {/* Notification Dropdown */}
        <Menu
          anchorEl={notifAnchor}
          open={Boolean(notifAnchor)}
          onClose={handleNotificationClose}
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
          transformOrigin={{ vertical: "top", horizontal: "right" }}
          PaperProps={{
            sx: { width: 320, maxHeight: 400 }
          }}
        >
          {notifications.length === 0 ? (
            <MenuItem disabled>
              <Typography variant="body2" color="text.secondary">
                No new notifications
              </Typography>
            </MenuItem>
          ) : (
            notifications.map((notif) => (
              <MenuItem key={notif?.id || Math.random()} onClick={handleNotificationClose}>
                <Typography variant="body2">{notif?.message}</Typography>
              </MenuItem>
            ))
          )}
        </Menu>
      </Toolbar>
    </AppBar>
  );
}