// Layout con barra inferior accesible (T032). Sin "Perfil": MVP1 no tiene cuentas (FR-034).
import MapIcon from "@mui/icons-material/Map";
import ReportIcon from "@mui/icons-material/ReportProblem";
import SearchIcon from "@mui/icons-material/Search";
import SyncIcon from "@mui/icons-material/Sync";
import { AppBar, BottomNavigation, BottomNavigationAction, Box, Paper, Toolbar, Typography } from "@mui/material";
import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { ConnectionBadge } from "./ConnectionBadge";

const NAV = [
  { to: "/", label: "Inicio", icon: <SearchIcon aria-hidden /> },
  { to: "/mapa", label: "Mapa", icon: <MapIcon aria-hidden /> },
  { to: "/reportar", label: "Reportar", icon: <ReportIcon aria-hidden /> },
  { to: "/estado", label: "Estado", icon: <SyncIcon aria-hidden /> },
];

export function Layout({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const current = NAV.findIndex((n) => (n.to === "/" ? pathname === "/" : pathname.startsWith(n.to)));
  return (
    <Box sx={{ minHeight: "100vh", display: "flex", flexDirection: "column", bgcolor: "background.default" }}>
      <a href="#contenido" className="skip-link">Saltar al contenido</a>
      <AppBar position="sticky" color="primary" elevation={0}>
        <Toolbar sx={{ gap: 1, flexWrap: "wrap", py: 0.5 }}>
          <Typography component="p" variant="h2" sx={{ flexGrow: 1, fontSize: "1.25rem" }}>
            Muévete CB
          </Typography>
          <ConnectionBadge />
        </Toolbar>
      </AppBar>
      <Box component="main" id="contenido" tabIndex={-1} sx={{ flex: 1, p: 2, pb: 12, maxWidth: 720, width: "100%", mx: "auto" }}>
        {children}
      </Box>
      <Paper component="nav" aria-label="Navegación principal" elevation={8}
        sx={{ position: "fixed", bottom: 0, left: 0, right: 0 }}>
        <BottomNavigation showLabels value={current === -1 ? false : current}>
          {NAV.map((n) => (
            <BottomNavigationAction key={n.to} component={Link} to={n.to} label={n.label} icon={n.icon}
              aria-current={NAV[current]?.to === n.to ? "page" : undefined} />
          ))}
        </BottomNavigation>
      </Paper>
    </Box>
  );
}
