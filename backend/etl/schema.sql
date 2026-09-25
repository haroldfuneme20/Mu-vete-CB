-- Esquema de muevete.db (data-model.md §1). Coordenadas WGS84, geometrías WKB.

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  file TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('institutional','community','territorial','demo_simulated')),
  published_at TEXT,
  loaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS barrios (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  localidad TEXT,
  is_ciudad_bolivar INTEGER NOT NULL DEFAULT 0,
  centroid_lat REAL NOT NULL,
  centroid_lng REAL NOT NULL,
  geom BLOB NOT NULL,
  source_id TEXT NOT NULL REFERENCES sources(id)
);
CREATE VIRTUAL TABLE IF NOT EXISTS barrios_rtree USING rtree(rid, min_lng, max_lng, min_lat, max_lat);

CREATE TABLE IF NOT EXISTS stops (
  rid INTEGER PRIMARY KEY,
  id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('sitp_zonal','tm_station','transmicable','community_point')),
  lat REAL NOT NULL,
  lng REAL NOT NULL,
  barrio_id TEXT,
  source_id TEXT NOT NULL REFERENCES sources(id),
  source_ref TEXT,
  parent_id TEXT            -- estación padre GTFS (plataformas/vagones)
);
CREATE VIRTUAL TABLE IF NOT EXISTS stops_rtree USING rtree(rid, min_lng, max_lng, min_lat, max_lat);

CREATE TABLE IF NOT EXISTS patterns (
  id TEXT PRIMARY KEY,
  route_ref TEXT NOT NULL,
  name TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('troncal','provisional','zonal','alimentador','transmicable',
                                     'community')),
  fare_class TEXT NOT NULL,
  fare REAL,
  service_start TEXT NOT NULL,
  service_end TEXT NOT NULL,
  headway_peak_s INTEGER NOT NULL,
  headway_offpeak_s INTEGER NOT NULL,
  reliability REAL NOT NULL,
  confidence REAL NOT NULL,
  last_updated TEXT NOT NULL,
  source_id TEXT NOT NULL REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS pattern_stops (
  pattern_id TEXT NOT NULL REFERENCES patterns(id),
  seq INTEGER NOT NULL,
  stop_id TEXT NOT NULL REFERENCES stops(id),
  t_from_start_s INTEGER NOT NULL,
  PRIMARY KEY (pattern_id, seq)
);

CREATE TABLE IF NOT EXISTS segments (
  rid INTEGER PRIMARY KEY,
  id TEXT UNIQUE NOT NULL,
  pattern_id TEXT NOT NULL REFERENCES patterns(id),
  seq INTEGER NOT NULL,
  geom BLOB NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS segments_rtree USING rtree(rid, min_lng, max_lng, min_lat, max_lat);

-- Geometrías solo para visualización (trazado troncal, rutas provisionales, malla vial).
CREATE TABLE IF NOT EXISTS display_lines (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('trunk','provisional','road_main','road_other')),
  name TEXT,
  geom BLOB NOT NULL,
  source_id TEXT NOT NULL REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS footpaths (
  from_stop_id TEXT NOT NULL,
  to_stop_id TEXT NOT NULL,
  walk_s INTEGER NOT NULL,
  PRIMARY KEY (from_stop_id, to_stop_id)
);

CREATE TABLE IF NOT EXISTS gazetteer (
  name_norm TEXT NOT NULL,
  display_name TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('barrio','station','stop','landmark')),
  ref_id TEXT NOT NULL,
  lat REAL NOT NULL,
  lng REAL NOT NULL,
  localidad TEXT
);
CREATE INDEX IF NOT EXISTS gazetteer_name ON gazetteer(name_norm);

CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY,
  anon_id TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('blockage','delay','route_change','risk','other')),
  lat REAL NOT NULL,
  lng REAL NOT NULL,
  description TEXT,
  photo_path TEXT,
  created_at TEXT,
  received_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'citizen'
);

CREATE TABLE IF NOT EXISTS report_segments (
  report_id TEXT NOT NULL REFERENCES reports(id),
  segment_id TEXT NOT NULL,
  distance_m REAL NOT NULL,
  PRIMARY KEY (report_id, segment_id)
);
