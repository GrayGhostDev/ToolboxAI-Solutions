import * as React from "react";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Topbar from "./Topbar";
import Sidebar from "./Sidebar";
import { UserRole } from "../../types/roles";
import { useAppSelector } from "../../store";

interface Props {
  role: UserRole;
  children: React.ReactNode;
}

export default function AppLayout({ role, children }: Props) {
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
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: sidebarOpen ? `${drawerWidth}px` : 0 },
          transition: (theme) =>
            theme.transitions.create(["margin", "width"], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}