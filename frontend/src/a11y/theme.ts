// Tema accesible (T031): texto base 16 px en rem, contraste WCAG 2.1 AA, zonas táctiles ≥ 44 px.
import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    primary: { main: "#0b3d63", contrastText: "#ffffff" },      // 11.4:1 sobre blanco
    secondary: { main: "#1b6e35", contrastText: "#ffffff" },    // 6.3:1
    error: { main: "#b3261e" },
    warning: { main: "#8a5300", contrastText: "#ffffff" },
    text: { primary: "#1a1a1a", secondary: "#454545" },         // 7.3:1
    background: { default: "#f6f8fb", paper: "#ffffff" },
  },
  typography: {
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif",
    fontSize: 16,
    htmlFontSize: 16,
    body1: { fontSize: "1rem", lineHeight: 1.55 },
    body2: { fontSize: "1rem", lineHeight: 1.5 },
    button: { fontSize: "1rem", textTransform: "none", fontWeight: 600 },
    h1: { fontSize: "1.6rem", fontWeight: 700 },
    h2: { fontSize: "1.3rem", fontWeight: 700 },
    h3: { fontSize: "1.1rem", fontWeight: 700 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiButton: { styleOverrides: { root: { minHeight: 48, minWidth: 48 } } },
    MuiIconButton: { styleOverrides: { root: { minHeight: 48, minWidth: 48 } } },
    MuiToggleButton: { styleOverrides: { root: { minHeight: 56, fontSize: "1rem" } } },
    MuiBottomNavigationAction: { styleOverrides: { root: { minWidth: 64, minHeight: 56 } } },
    MuiInputBase: { styleOverrides: { input: { fontSize: "1rem" } } },
    MuiChip: { styleOverrides: { root: { fontSize: "0.9rem", height: 32 } } },
  },
});
