import { CssBaseline, ThemeProvider } from "@mui/material";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { theme } from "./a11y/theme";
import { Layout } from "./components/Layout";
import { Home } from "./pages/Home";
import { MapPage } from "./pages/MapPage";
import { Report } from "./pages/Report";
import { Results } from "./pages/Results";
import { RouteDetail } from "./pages/RouteDetail";
import { Status } from "./pages/Status";
import { AppStateProvider } from "./state/AppState";

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppStateProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/resultados" element={<Results />} />
              <Route path="/ruta/:id" element={<RouteDetail />} />
              <Route path="/mapa" element={<MapPage />} />
              <Route path="/reportar" element={<Report />} />
              <Route path="/estado" element={<Status />} />
              <Route path="*" element={<Home />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </AppStateProvider>
    </ThemeProvider>
  );
}
