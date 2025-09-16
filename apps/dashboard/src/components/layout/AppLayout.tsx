import * as React from "react";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Topbar from "./Topbar";
import Sidebar from "./Sidebar";
import { UserRole } from "../../types";
import { useAppSelector } from "../../store";
import { ParticleEffects } from "../roblox/ParticleEffects";

interface Props {
  role: UserRole;
  children: React.ReactNode;
  isRobloxPage?: boolean;
}

export default function AppLayout({ role, children, isRobloxPage = false }: Props) {
  const sidebarOpen = useAppSelector((s) => s.ui.sidebarOpen);
  const drawerWidth = 240;

  return (
    <Box sx={{ display: "flex", minHeight: "100dvh", bgcolor: "background.default" }}>
      <Topbar />
      <Sidebar role={role} />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 3 },
          width: { sm: sidebarOpen ? `calc(100% - ${drawerWidth}px)` : "100%" },
          ml: { sm: sidebarOpen ? `${drawerWidth}px` : 0 },
          // REMOVED ALL TRANSITIONS TO PREVENT MOVEMENT
          minHeight: "100vh",
          background: "linear-gradient(135deg, #0f0f2e 0%, #1a0b2e 50%, #2e0b2e 100%)",
        }}
      >
        {/* Particle Effects for enhanced visuals - Disabled on Roblox page */}
        {!isRobloxPage && (
          <ParticleEffects
            variant="mixed"
            intensity="low"
            position="absolute"
            zIndex={0}
          />
        )}

        <Toolbar />
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}