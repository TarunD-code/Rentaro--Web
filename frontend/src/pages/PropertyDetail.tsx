import React, { useEffect, useState, useRef } from 'react';
import { 
  Box, 
  Typography, 
  Container, 
  Grid, 
  Paper, 
  Button, 
  alpha, 
  useTheme, 
  Divider,
  Card,
  Avatar,
  IconButton,
  Chip
} from '@mui/material';
import { 
  LocationOn, 
  Star, 
  Share, 
  FavoriteBorder, 
  ChevronLeft,
  DirectionsRun,
  DirectionsBike,
  Commute,
  LocalHospital,
  School,
  ShoppingBag,
  Work,
  Park as ParkIcon,
  LocalPharmacy,
  Restaurant,
  LocalAtm,
  FitnessCenter
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { getPropertyById } from '../api/properties';
import { Helmet } from 'react-helmet-async';
import TrustBadge from '../components/TrustBadge';
import ChatBox from '../components/ChatBox';
import { Rating, TextField } from '@mui/material';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { Dayjs } from 'dayjs';

import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY || 'VGr2EA4T8DcPNjZSXJos';


// Mock Child Components for first pass
const Gallery: React.FC<{ media: any[] }> = ({ media }) => {
  const theme = useTheme();
  const [active, setActive] = useState(0);
  
  if (!media || !Array.isArray(media) || media.length === 0) {
    return (
      <Box sx={{ position: 'relative', borderRadius: 6, overflow: 'hidden', height: { xs: 300, md: 500 }, bgcolor: alpha(theme.palette.text.primary, 0.05), display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <img 
          src="https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&q=80" 
          alt="Property Fallback" 
          style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
        />
      </Box>
    );
  }
  
  const activeMedia = media[active] || media[0];
  if (!activeMedia) return null;
  
  return (
    <Box sx={{ position: 'relative', borderRadius: 6, overflow: 'hidden', height: { xs: 300, md: 500 } }}>
       <img 
         src={activeMedia.url || "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&q=80"} 
         alt="Property" 
         style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
         loading="lazy"
       />
       <Box 
         sx={{ 
           position: 'absolute', 
           bottom: 20, 
           left: 20, 
           display: 'flex', 
           gap: 1.5, 
           p: 1, 
           bgcolor: 'rgba(0,0,0,0.4)', 
           backdropFilter: 'blur(10px)', 
           borderRadius: 4 
         }}
       >
         {media.map((m, i) => {
           if (!m) return null;
           return (
             <Box 
               key={i} 
               onClick={() => setActive(i)}
               sx={{ 
                 width: 60, 
                 height: 60, 
                 borderRadius: 2, 
                 overflow: 'hidden', 
                 cursor: 'pointer',
                 border: active === i ? `2px solid ${theme.palette.primary.main}` : 'none',
                 opacity: active === i ? 1 : 0.6
               }}
             >
               <img src={m.thumbnailUrl || m.url || "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&q=80"} alt="Thumb" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
             </Box>
           );
         })}
       </Box>
    </Box>
  );
};

const HostCard: React.FC<{ host: any }> = ({ host }) => {
  const theme = useTheme();
  if (!host) return null;
  const hostName = host.name || "Trusted Host";
  return (
    <Card 
       elevation={0}
       sx={{ 
         p: 3, 
         borderRadius: 6, 
         border: `1px solid ${theme.palette.divider}`,
         bgcolor: alpha(theme.palette.background.paper, 0.4),
         backdropFilter: 'blur(10px)'
       }}
    >
      <Box display="flex" alignItems="center" gap={2} mb={2}>
        <Avatar sx={{ width: 56, height: 56, bgcolor: theme.palette.primary.main }}>{hostName[0] || 'H'}</Avatar>
        <Box>
          <Box display="flex" alignItems="center" gap={1} mb={0.5}>
            <Typography variant="h6" fontWeight={700}>{hostName}</Typography>
            <TrustBadge status={host.verified ? 'verified' : 'unverified'} />
          </Box>
          <Typography variant="caption" color="text.secondary">Response time: {host.responseTime || 'Within 1h'}</Typography>
        </Box>
      </Box>
      <Button variant="outlined" fullWidth sx={{ borderRadius: 3 }}>View Profile</Button>
    </Card>
  );
};

interface PropertyMapProps {
  property: any;
  commuteData: any;
  pois?: any[];
  selectedRoute: any;
  selectedPoi?: any;       // drives the destination pin
  isRouteLoading?: boolean; // shows a loading overlay on the map while fetching
  onPoiClick?: (poi: any) => void;
}

const PropertyMap: React.FC<PropertyMapProps> = ({
  property, commuteData, pois, selectedRoute, selectedPoi,
  isRouteLoading = false, onPoiClick,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<maplibregl.Map | null>(null);
  const [mapError, setMapError] = useState<string | null>(null);
  const [mapLoading, setMapLoading] = useState(true);

  // Destination pin — dropped at the selected POI before the route arrives
  const destinationMarkerRef = useRef<maplibregl.Marker | null>(null);
  // Small dot markers for all POIs in the active category
  const categoryMarkersRef = useRef<maplibregl.Marker[]>([]);

  // Draw (or clear) the Ola Maps route polyline + last-mile dotted connector.
  //
  // Three MapLibre artefacts are managed together so cleanup is always atomic:
  //   route-source        / route-layer          — the main snapped road route
  //   route-last-mile-source / route-last-mile-layer — dotted line from the
  //                           last road-snapped point to the exact POI pin
  //
  // Key design decisions:
  //   1. Read mapInstanceRef.current INSIDE drawRoute so we always get the live
  //      instance even after a map rebuild.
  //   2. Depend on [selectedRoute, mapLoading] — mapLoading flipping to false
  //      means a fresh map instance just became ready; re-running ensures any
  //      pending route gets drawn on the new canvas.
  //   3. Clean up the 'style.load' one-time listener on effect teardown so
  //      stale closures from previous renders don't fire on the new map.
  useEffect(() => {
    let styleLoadListener: (() => void) | null = null;

    const drawRoute = (): void => {
      const map = mapInstanceRef.current;
      if (!map || !map.isStyleLoaded()) return;

      // ── Purge ALL previous route artefacts (layers before sources) ──────────
      const layersToClear  = ['route-layer', 'route-first-mile-layer', 'route-last-mile-layer'];
      const sourcesToClear = ['route-source', 'route-first-mile-source', 'route-last-mile-source'];
      layersToClear .forEach(id => { try { if (map.getLayer (id)) map.removeLayer (id); } catch (_) {} });
      sourcesToClear.forEach(id => { try { if (map.getSource(id)) map.removeSource(id); } catch (_) {} });

      // ── Normalise coordinate array from all possible backend shapes ──────────
      let rawCoords: unknown = null;

      if (Array.isArray(selectedRoute)) {
        rawCoords = selectedRoute;
      } else if (selectedRoute?.geometry?.coordinates) {
        rawCoords = selectedRoute.geometry.coordinates;
      } else if (selectedRoute?.coordinates) {
        rawCoords = selectedRoute.coordinates;
      }

      if (!Array.isArray(rawCoords) || rawCoords.length < 2) {
        console.warn('[Rentora] drawRoute: no valid coordinates extracted.', selectedRoute);
        return;
      }

      // Filter out NaN / Infinity pairs that Ola Maps occasionally emits
      const coords: [number, number][] = (rawCoords as unknown[])
        .filter((c): c is [number, number] =>
          Array.isArray(c) && c.length >= 2 && isFinite(c[0]) && isFinite(c[1])
        )
        .map((c) => [c[0], c[1]]);

      if (coords.length < 2) {
        console.warn('[Rentora] drawRoute: fewer than 2 valid [lng,lat] pairs.', rawCoords);
        return;
      }

      console.log('[Rentora Route]', `${coords.length} pts`, coords[0], '→', coords[coords.length - 1]);

      try {
        // ── Primary route — solid brand-blue road line ──────────────────────
        map.addSource('route-source', {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: { type: 'LineString', coordinates: coords },
          },
        });

        map.addLayer({
          id: 'route-layer',
          type: 'line',
          source: 'route-source',
          layout: { 'line-join': 'round', 'line-cap': 'round' },
          paint: {
            'line-color':   '#00467F',
            'line-width':   5,
            'line-opacity': 0.85,
          },
        });

        // ── First-mile connector — dotted line from exact property → road snap ─
        // The routing engine also snaps the *origin* to the nearest road,
        // leaving a gap at the property end identical to the destination gap.
        // We bridge it with the same [2,2] dash style so both ends are consistent.
        const routeStart = coords[0]; // [lng, lat] of first road-snapped point

        const propLng = property?.address?.geo?.lng;
        const propLat = property?.address?.geo?.lat;

        const hasValidOrigin =
          typeof propLng === 'number' && isFinite(propLng) &&
          typeof propLat === 'number' && isFinite(propLat);

        const originGapVisible = hasValidOrigin && (
          Math.abs(routeStart[0] - propLng) > 0.00002 ||
          Math.abs(routeStart[1] - propLat) > 0.00002
        );

        if (originGapVisible) {
          map.addSource('route-first-mile-source', {
            type: 'geojson',
            data: {
              type: 'Feature',
              properties: {},
              geometry: {
                type: 'LineString',
                coordinates: [
                  [propLng, propLat],          // Point A: exact property pin
                  [routeStart[0], routeStart[1]], // Point B: road-snapped origin
                ],
              },
            },
          });

          map.addLayer({
            id: 'route-first-mile-layer',
            type: 'line',
            source: 'route-first-mile-source',
            layout: { 'line-join': 'round', 'line-cap': 'round' },
            paint: {
              'line-color':     '#00467F',
              'line-width':     4,
              'line-opacity':   0.75,
              'line-dasharray': [2, 2],
            },
          });
        }

        // ── Last-mile connector — dotted line from road snap → exact POI ────
        // The routing engine snaps to the nearest road, leaving a gap between
        // the route terminus and the actual POI pin. We bridge that gap with a
        // dotted segment styled identically to the route but with line-dasharray
        // so it reads as "approximate / off-road" — matching Google Maps' UX.
        const routeEnd = coords[coords.length - 1]; // [lng, lat] of last road point

        // Only draw the connector when we have a valid POI coordinate AND the
        // gap is worth showing (>2 m — avoids a zero-length dash artefact).
        const poiLng = selectedPoi?.lng;
        const poiLat = selectedPoi?.lat;

        const hasValidPoi =
          typeof poiLng === 'number' && isFinite(poiLng) &&
          typeof poiLat === 'number' && isFinite(poiLat);

        // Rough gap check in degrees (0.00002° ≈ 2 m at Bengaluru latitude)
        const gapIsVisible = hasValidPoi && (
          Math.abs(routeEnd[0] - poiLng) > 0.00002 ||
          Math.abs(routeEnd[1] - poiLat) > 0.00002
        );

        if (gapIsVisible) {
          const lastMileCoords: [number, number][] = [
            [routeEnd[0], routeEnd[1]],   // Point A: road-snapped terminus
            [poiLng,      poiLat],         // Point B: exact POI coordinate
          ];

          map.addSource('route-last-mile-source', {
            type: 'geojson',
            data: {
              type: 'Feature',
              properties: {},
              geometry: { type: 'LineString', coordinates: lastMileCoords },
            },
          });

          map.addLayer({
            id: 'route-last-mile-layer',
            type: 'line',
            source: 'route-last-mile-source',
            layout: { 'line-join': 'round', 'line-cap': 'round' },
            paint: {
              'line-color':     '#00467F',  // same brand blue as main route
              'line-width':     4,
              'line-opacity':   0.75,
              // [dash_length, gap_length] in units of line-width.
              // [2, 2] produces a balanced dot-dash that reads clearly at zoom 14–16.
              'line-dasharray': [2, 2],
            },
          });
        }

        // ── Fit viewport to the full extent: property + route + POI pin ──────
        // Include the property origin so the first-mile connector is never
        // clipped off-screen when the road snap is far from the property pin.
        const allPoints: [number, number][] = [
          ...(hasValidOrigin ? [[propLng, propLat] as [number, number]] : []),
          ...coords,
          ...(hasValidPoi    ? [[poiLng,  poiLat]  as [number, number]] : []),
        ];

        const bounds = allPoints.reduce(
          (b, coord) => b.extend(coord as maplibregl.LngLatLike),
          new maplibregl.LngLatBounds(allPoints[0], allPoints[0])
        );
        map.fitBounds(bounds, { padding: 70, maxZoom: 16, duration: 1000 });

      } catch (layerErr) {
        console.error('[Rentora] Error drawing route layers:', layerErr);
      }
    };

    const map = mapInstanceRef.current;
    if (!map) return;

    if (map.isStyleLoaded()) {
      drawRoute();
    } else {
      styleLoadListener = drawRoute;
      map.once('style.load', styleLoadListener);
    }

    return () => {
      if (styleLoadListener && mapInstanceRef.current) {
        try { mapInstanceRef.current.off('style.load', styleLoadListener); } catch (_) {}
      }
    };
  }, [selectedRoute, mapLoading, selectedPoi]);

  // ── Map initialisation ──────────────────────────────────────────────────────
  // Runs ONLY when the property changes (i.e. once per page load).
  // Keeping commuteData/pois out of this dependency array prevents the map from
  // being torn down and rebuilt every time async POI data arrives — which was
  // the root cause of route layers being silently lost.
  useEffect(() => {
    if (!property || !mapContainerRef.current) return;

    const lat = property.address?.geo?.lat;
    const lng = property.address?.geo?.lng;

    if (typeof lat !== 'number' || typeof lng !== 'number' || isNaN(lat) || isNaN(lng) || !isFinite(lat) || !isFinite(lng)) {
      setMapError("Invalid coordinates");
      setMapLoading(false);
      return;
    }

    let map: maplibregl.Map | null = null;

    try {
      map = new maplibregl.Map({
        container: mapContainerRef.current,
        style: `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`,
        center: [lng, lat],
        zoom: 14,
      });

      mapInstanceRef.current = map;

      map.on('styleimagemissing', (e) => {
        const id = e.id;
        if (!map || map.hasImage(id)) return;
        const canvas = document.createElement('canvas');
        canvas.width = 16; canvas.height = 16;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.fillStyle = 'rgba(0,0,0,0)';
          ctx.fillRect(0, 0, 16, 16);
          try { map.addImage(id, ctx.getImageData(0, 0, 16, 16)); } catch (_) {}
        }
      });

      map.on('load', () => {
        setMapLoading(false);
      });

      // Property pin marker
      const markerEl = document.createElement('div');
      const titleSnippet = property.title
        ? property.title.substring(0, 20) + (property.title.length > 20 ? '...' : '')
        : 'Property';
      markerEl.innerHTML = `<div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;padding:8px 14px;border-radius:20px;font-size:13px;font-weight:700;box-shadow:0 4px 16px rgba(99,102,241,0.4);font-family:'Inter',sans-serif;">📍 ${titleSnippet}</div>`;
      new maplibregl.Marker({ element: markerEl }).setLngLat([lng, lat]).addTo(map);

      map.addControl(new maplibregl.NavigationControl(), 'top-right');
    } catch (err: any) {
      console.error('Failed to initialize MapLibre map:', err);
      setMapError(err.message || 'Failed to load map style');
      setMapLoading(false);
    }

    return () => {
      if (mapInstanceRef.current && mapInstanceRef.current === map) {
        try { mapInstanceRef.current.remove(); } catch (_) {}
        mapInstanceRef.current = null;
      }
    };
  }, [property]);

  // ── POI marker layer ─────────────────────────────────────────────────────────
  // Runs whenever the POI dataset changes. Adds markers to the existing map
  // instance without touching the map lifecycle or the route layer.
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const activePois: any[] = pois ?? commuteData?.pois ?? [];
    if (!activePois.length) return;

    const categoryIcons: Record<string, string> = {
      metro: '🚇', bus: '🚌', bus_depot: '🚏', bus_station: '🚏', bus_stop: '🚌',
      hospital: '🏥', clinic: '🏥', pharmacy: '💊',
      grocery: '🛒', supermarket: '🛒',
      restaurant: '🍽️', cafe: '☕',
      office: '🏢', company: '🏢', tech_park: '🏢', coworking: '🏢',
      school: '🏫', college: '🎓', university: '🎓',
      park: '🌳', playground: '🛝', gym: '💪', atm: '🏧', bank: '🏦',
    };

    const poiMarkers: maplibregl.Marker[] = [];

    const addMarkers = () => {
      activePois.forEach((p: any) => {
        if (typeof p.lat !== 'number' || typeof p.lng !== 'number' || isNaN(p.lat) || isNaN(p.lng)) return;
        const icon = categoryIcons[p.category] ?? '📍';
        const poiEl = document.createElement('div');
        poiEl.innerHTML = `<div style="background:white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.2);font-size:14px;cursor:pointer;">${icon}</div>`;

        const popup = new maplibregl.Popup({ offset: 15 }).setHTML(
          `<strong>${p.name ?? ''}</strong><br/><small>${p.category ?? ''}</small>`
        );

        const marker = new maplibregl.Marker({ element: poiEl })
          .setLngLat([p.lng, p.lat])
          .setPopup(popup)
          .addTo(map!);

        poiEl.addEventListener('click', (e) => {
          e.stopPropagation();
          onPoiClick?.(p);
        });

        poiMarkers.push(marker);
      });
    };

    // Map may not be loaded yet when this effect first fires
    if (map.isStyleLoaded()) {
      addMarkers();
    } else {
      map.once('load', addMarkers);
    }

    return () => {
      poiMarkers.forEach((m) => m.remove());
    };
  }, [commuteData, pois, onPoiClick]);

  // ── Destination pin ──────────────────────────────────────────────────────────
  // Dropped immediately when selectedPoi changes — gives the user instant visual
  // confirmation before the async route response arrives.
  useEffect(() => {
    const map = mapInstanceRef.current;

    // Remove any previous destination pin
    if (destinationMarkerRef.current) {
      destinationMarkerRef.current.remove();
      destinationMarkerRef.current = null;
    }

    if (!map || !selectedPoi) return;

    const { lat, lng, name, category } = selectedPoi;
    if (typeof lat !== 'number' || typeof lng !== 'number') return;

    // Build a prominent red destination pin
    const el = document.createElement('div');
    el.innerHTML = `
      <div style="
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        cursor: default;
      ">
        <!-- Circle head -->
        <div style="
          width: 36px; height: 36px; border-radius: 50%;
          background: #e53935;
          border: 3px solid #fff;
          box-shadow: 0 3px 12px rgba(229,57,53,0.55);
          display: flex; align-items: center; justify-content: center;
          font-size: 16px;
          z-index: 2;
        ">📍</div>
        <!-- Stem -->
        <div style="
          width: 3px; height: 14px;
          background: linear-gradient(to bottom, #e53935, rgba(229,57,53,0));
          margin-top: -2px;
        "></div>
        <!-- Label -->
        <div style="
          background: #e53935; color: #fff;
          font-family: 'Inter', sans-serif;
          font-size: 11px; font-weight: 700;
          padding: 2px 8px; border-radius: 10px;
          white-space: nowrap;
          box-shadow: 0 2px 6px rgba(0,0,0,0.25);
          max-width: 140px; overflow: hidden; text-overflow: ellipsis;
        ">${name || category || 'Destination'}</div>
      </div>
    `;

    const pin = new maplibregl.Marker({ element: el, anchor: 'bottom' })
      .setLngLat([lng, lat])
      .addTo(map);

    destinationMarkerRef.current = pin;

    // Pan to the destination so the pin is always visible
    map.easeTo({ center: [lng, lat], zoom: Math.max(map.getZoom(), 14), duration: 600 });
  }, [selectedPoi]);

  // ── Category dot markers ──────────────────────────────────────────────────────
  // Renders a small coloured circle for every POI in the active category list.
  // Proves the data exists even when base-map tiles lack text labels.
  useEffect(() => {
    const map = mapInstanceRef.current;

    // Clear previous category markers
    categoryMarkersRef.current.forEach(m => m.remove());
    categoryMarkersRef.current = [];

    if (!map) return;

    const activePois: any[] = pois ?? commuteData?.pois ?? [];
    if (!activePois.length) return;

    const categoryColors: Record<string, string> = {
      metro: '#1a73e8', bus: '#1a73e8', bus_station: '#1a73e8', bus_stop: '#1a73e8', bus_depot: '#1a73e8',
      hospital: '#e53935', clinic: '#e53935',
      pharmacy: '#43a047',
      school: '#fb8c00', college: '#fb8c00', university: '#fb8c00',
      grocery: '#00897b', supermarket: '#00897b',
      restaurant: '#c62828', cafe: '#c62828',
      office: '#546e7a', tech_park: '#546e7a', company: '#546e7a', coworking: '#7b1fa2',
      park: '#2e7d32', playground: '#2e7d32', gym: '#e65100',
      mall: '#6a1b9a', atm: '#1565c0', bank: '#1565c0',
    };

    const addDots = () => {
      activePois.forEach((p: any) => {
        if (typeof p.lat !== 'number' || typeof p.lng !== 'number') return;

        // Skip the currently selected POI — it already has the prominent destination pin
        if (
          selectedPoi &&
          Math.abs(p.lat - selectedPoi.lat) < 0.00001 &&
          Math.abs(p.lng - selectedPoi.lng) < 0.00001
        ) return;

        const color = categoryColors[p.category] ?? '#607d8b';

        const el = document.createElement('div');
        el.innerHTML = `
          <div style="
            width: 12px; height: 12px; border-radius: 50%;
            background: ${color};
            border: 2px solid #fff;
            box-shadow: 0 1px 4px rgba(0,0,0,0.3);
            cursor: pointer;
            transition: transform 0.15s ease;
          "></div>
        `;
        el.addEventListener('mouseenter', () => {
          (el.firstElementChild as HTMLElement).style.transform = 'scale(1.6)';
        });
        el.addEventListener('mouseleave', () => {
          (el.firstElementChild as HTMLElement).style.transform = 'scale(1)';
        });

        const popup = new maplibregl.Popup({ offset: 10, closeButton: false })
          .setHTML(
            `<div style="font-family:'Inter',sans-serif;padding:2px">
              <strong style="font-size:12px">${p.name ?? ''}</strong><br/>
              <span style="font-size:10px;color:${color};text-transform:uppercase;font-weight:600">
                ${p.category ?? ''}
              </span>
              ${p.distance_m ? `<br/><span style="font-size:10px;color:#94a3b8">~${p.distance_m}m</span>` : ''}
            </div>`
          );

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([p.lng, p.lat])
          .setPopup(popup)
          .addTo(map!);

        el.addEventListener('click', (e) => {
          e.stopPropagation();
          onPoiClick?.(p);
        });

        categoryMarkersRef.current.push(marker);
      });
    };

    if (map.isStyleLoaded()) {
      addDots();
    } else {
      map.once('load', addDots);
    }

    return () => {
      categoryMarkersRef.current.forEach(m => m.remove());
      categoryMarkersRef.current = [];
    };
  }, [pois, commuteData, selectedPoi, onPoiClick]);

  if (mapError) {
    return (
      <Box 
        sx={{ 
          height: '100%', 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          bgcolor: 'background.paper',
          p: 3,
          textAlign: 'center'
        }}
      >
        <LocationOn color="primary" sx={{ fontSize: 48, mb: 1 }} />
        <Typography variant="h6" fontWeight={700}>{property.address?.city || 'Location Details'}</Typography>
        <Typography variant="body2" color="text.secondary">
          {property.address?.city ? `${property.address.city}, ${property.address.state || ''}` : 'Map unavailable'}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', width: '100%', position: 'relative' }}>
      {/* Base map loading */}
      {mapLoading && (
        <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'rgba(255,255,255,0.7)', zIndex: 1 }}>
          <Typography variant="body2" color="text.secondary">Loading map...</Typography>
        </Box>
      )}
      {/* Route-fetching overlay — appears after map load, while route is in-flight */}
      {!mapLoading && isRouteLoading && (
        <Box sx={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-start',
          p: 2, zIndex: 2, pointerEvents: 'none',
        }}>
          <Box sx={{
            display: 'flex', alignItems: 'center', gap: 1,
            bgcolor: 'rgba(255,255,255,0.92)', backdropFilter: 'blur(6px)',
            borderRadius: 3, px: 2, py: 1,
            boxShadow: '0 2px 12px rgba(0,0,0,0.12)',
            border: '1px solid rgba(99,102,241,0.2)',
          }}>
            <Box sx={{
              width: 14, height: 14, borderRadius: '50%',
              border: '2px solid #6366f1',
              borderTopColor: 'transparent',
              animation: 'spin 0.7s linear infinite',
              '@keyframes spin': { to: { transform: 'rotate(360deg)' } },
            }} />
            <Typography variant="caption" fontWeight={700} color="primary.main">
              Calculating route…
            </Typography>
          </Box>
        </Box>
      )}
      <div ref={mapContainerRef} style={{ height: '100%', width: '100%' }} />
    </Box>
  );
};

export default function PropertyDetail() {
  const { id } = useParams<{ id: string }>();
  const theme = useTheme();
  const navigate = useNavigate();
  const [property, setProperty] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);
  const [reviews, setReviews] = useState<any[]>([]);
  const [newReviewText, setNewReviewText] = useState('');
  const [newReviewRating, setNewReviewRating] = useState<number | null>(0);
  const [selectedDate, setSelectedDate] = useState<Dayjs | null>(null);
  const [profile, setProfile] = useState<any>(null);
  const [commuteData, setCommuteData] = useState<any>(null);

  const [selectedPoi, setSelectedPoi] = useState<any>(null);
  const [commuteMode, setCommuteMode] = useState<string>('driving');
  const [selectedRoute, setSelectedRoute] = useState<any>(null);
  const [fetchingRoute, setFetchingRoute] = useState<boolean>(false);
  const [activeCategoryTab, setActiveCategoryTab] = useState<string>('All');
  const [isPoisLoading, setIsPoisLoading] = useState<boolean>(false);

  const formatCommuteTime = (route: any) => {
    if (!route) return "";
    let durationInMins = 0;
    
    const rawDuration = route.duration_min ?? route.durationMin ?? route.duration_mins ?? route.duration;
    
    if (rawDuration !== undefined && rawDuration !== null) {
      durationInMins = rawDuration > 120 ? rawDuration / 60 : rawDuration;
    } else if (route.distance_km !== undefined && route.distance_km !== null) {
      const dist = route.distance_km;
      const mode = (route.mode || commuteMode || 'driving').toLowerCase();
      if (mode === 'walking') {
        durationInMins = dist * 12; // 5 km/h
      } else if (mode === 'cycling' || mode === 'bicycle') {
        durationInMins = dist * 4; // 15 km/h
      } else {
        durationInMins = (dist / 35) * 60; // 35 km/h
      }
    } else {
      return "";
    }

    durationInMins = Math.round(durationInMins);
    if (durationInMins < 1) return "Under 1 min";
    if (durationInMins < 60) {
      return `${durationInMins} mins`;
    }
    const hours = Math.floor(durationInMins / 60);
    const mins = durationInMins % 60;
    if (mins === 0) {
      return `${hours} hr${hours > 1 ? 's' : ''}`;
    }
    return `${hours} hr${hours > 1 ? 's' : ''} ${mins} mins`;
  };

  const getCategoryIcon = (category: string) => {
    const cat = (category || '').toLowerCase();
    if (['metro', 'bus', 'bus_depot', 'bus_station', 'bus_stop'].includes(cat)) {
      return <Commute sx={{ fontSize: 18 }} />;
    }
    if (['hospital', 'clinic'].includes(cat)) {
      return <LocalHospital sx={{ fontSize: 18 }} />;
    }
    if (['pharmacy'].includes(cat)) {
      return <LocalPharmacy sx={{ fontSize: 18 }} />;
    }
    if (['school', 'college', 'university'].includes(cat)) {
      return <School sx={{ fontSize: 18 }} />;
    }
    if (['grocery', 'supermarket', 'mall'].includes(cat)) {
      return <ShoppingBag sx={{ fontSize: 18 }} />;
    }
    if (['restaurant', 'cafe'].includes(cat)) {
      return <Restaurant sx={{ fontSize: 18 }} />;
    }
    if (['office', 'company', 'tech_park', 'coworking'].includes(cat)) {
      return <Work sx={{ fontSize: 18 }} />;
    }
    if (['park', 'playground'].includes(cat)) {
      return <ParkIcon sx={{ fontSize: 18 }} />;
    }
    if (['atm', 'bank'].includes(cat)) {
      return <LocalAtm sx={{ fontSize: 18 }} />;
    }
    if (['gym'].includes(cat)) {
      return <FitnessCenter sx={{ fontSize: 18 }} />;
    }
    return <DirectionsRun sx={{ fontSize: 18 }} />;
  };

  const amenityCategories = [
    { key: 'All', label: 'All POIs' },
    { key: 'Healthcare', label: 'Healthcare', subcategories: ['hospital', 'clinic', 'pharmacy'] },
    { key: 'Education', label: 'Education', subcategories: ['school', 'college', 'university'] },
    { key: 'Transport', label: 'Transport', subcategories: ['metro', 'bus', 'bus_depot', 'bus_station', 'bus_stop'] },
    { key: 'Food', label: 'Food & Dining', subcategories: ['grocery', 'supermarket', 'restaurant', 'cafe', 'mall'] },
    { key: 'Offices', label: 'Offices', subcategories: ['office', 'company', 'tech_park', 'coworking'] },
    { key: 'Recreation', label: 'Recreation', subcategories: ['park', 'playground', 'gym'] },
    { key: 'Banking', label: 'Banking', subcategories: ['atm', 'bank'] }
  ];

  const filteredPois = commuteData?.pois?.filter((p: any) => {
    if (activeCategoryTab === 'All') return true;
    const catDef = amenityCategories.find(c => c.key === activeCategoryTab);
    return catDef?.subcategories?.includes(p.category.toLowerCase());
  }) || [];

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${import.meta.env.VITE_API_URL}/profile/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) setProfile(await res.json());
    } catch (err) { console.error(err); }
  };

  const handleGenerateAgreement = async () => {
    if (!id) return;
    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${import.meta.env.VITE_API_URL}/property/agreements/generate`, {
            method: 'POST',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                property_id: parseInt(id), 
                tenant_id: 'mock-tenant-id' // In real app, select from inquiries
            })
        });
        if (res.ok) {
            const data = await res.json();
            navigate(`/agreements/${data.id}`);
        }
    } catch (err) { console.error(err); }
  };

  const fetchReviews = async (propId: string) => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/property/${propId}/reviews`);
      if (res.ok) {
        setReviews(await res.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleScheduleVisit = async () => {
    if (!selectedDate || !id) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${import.meta.env.VITE_API_URL}/property/visits`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          property_id: parseInt(id), 
          requested_slot: selectedDate.toISOString() 
        })
      });
      if (res.ok) {
        alert("Visit request sent successfully!");
        setSelectedDate(null);
      } else {
        alert("Failed to send visit request.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    setSelectedPoi(null);
    setSelectedRoute(null);
  }, [id]);

  useEffect(() => {
    if (id) {
      getPropertyById(id).then(data => {
        setProperty(data);
        setLoading(false);
        // Fetch Location POIs - with proper null check
        if (data?.address?.geo?.lat && data?.address?.geo?.lng) {
          setIsPoisLoading(true);
          fetch(`${import.meta.env.VITE_API_URL}/property/location/pois?lat=${data.address.geo.lat}&lng=${data.address.geo.lng}`)
            .then(res => res.json())
            .then(d => { setCommuteData(d); setIsPoisLoading(false); })
            .catch(err => { console.error("Commute Error", err); setIsPoisLoading(false); });
        }
      });
      fetchReviews(id);
      fetchProfile();
    }
  }, [id]);

  useEffect(() => {
    if (!selectedPoi || !property) {
      setSelectedRoute(null);
      return;
    }
    const originLat = property?.address?.geo?.lat;
    const originLng = property?.address?.geo?.lng;
    const destLat = selectedPoi.lat;
    const destLng = selectedPoi.lng;

    if (!originLat || !originLng || !destLat || !destLng) return;

    setFetchingRoute(true);
    fetch(`${import.meta.env.VITE_API_URL}/geo/commute/route?origin_lat=${originLat}&origin_lng=${originLng}&dest_lat=${destLat}&dest_lng=${destLng}&mode=${commuteMode}`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch route");
        return res.json();
      })
      .then(data => {
        setSelectedRoute(data);
        setFetchingRoute(false);
      })
      .catch(err => {
        console.error("Error fetching commute route:", err);
        setFetchingRoute(false);
      });
  }, [selectedPoi, commuteMode, property]);

  const handleReviewSubmit = async () => {
    if (!newReviewRating || !id) return;
    try {
      const token = localStorage.getItem('token');
      await fetch(`${import.meta.env.VITE_API_URL}/property/${id}/reviews`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rating: newReviewRating, text: newReviewText })
      });
      setNewReviewText('');
      setNewReviewRating(0);
      fetchReviews(id);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading || !property) {
    return (
      <Container sx={{ py: 10, textAlign: 'center' }}>
        <Typography>Loading premium details...</Typography>
      </Container>
    );
  }

  return (
    <Box sx={{ py: 4 }}>
      <Helmet>
        <title>{`${property.title || 'Untitled Property'} | Rentora`}</title>
        <meta name="description" content={(property.description || "").substring(0, 160)} />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Accommodation",
            "name": property.title || 'Untitled Property',
            "description": property.description || '',
            "address": {
              "@type": "PostalAddress",
              "addressLocality": property.address?.city || '',
              "addressRegion": property.address?.state || ''
            },
            "offers": {
              "@type": "Offer",
              "price": property.price || 0,
              "priceCurrency": property.currency || 'INR'
            }
          })}
        </script>
      </Helmet>
      
      <Container maxWidth="lg">
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
           <IconButton onClick={() => navigate(-1)} sx={{ bgcolor: alpha(theme.palette.text.primary, 0.05) }}>
              <ChevronLeft />
           </IconButton>
           <Box display="flex" gap={2}>
              <IconButton sx={{ border: `1px solid ${theme.palette.divider}` }}><Share /></IconButton>
              <IconButton sx={{ border: `1px solid ${theme.palette.divider}` }}><FavoriteBorder /></IconButton>
           </Box>
        </Box>

        {/* Professional Airbnb/99acres Style Detail Hero Header */}
        <Box mb={4}>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" flexWrap="wrap" gap={2}>
            <Box>
              <Typography variant="h3" fontWeight={800} sx={{ letterSpacing: '-0.5px', mb: 1 }}>
                {property.title || 'Untitled Property'}
              </Typography>
              <Box display="flex" alignItems="center" gap={1.5} color="text.secondary" mb={2}>
                <LocationOn color="primary" fontSize="small" />
                <Typography variant="body1" fontWeight={500}>
                  {property.address?.full_address || `${property.address?.city || ''}, ${property.address?.state || ''}`}
                </Typography>
                <Chip 
                  label={property.property_type || 'Apartment'} 
                  size="small" 
                  color="primary" 
                  variant="outlined" 
                  sx={{ borderRadius: 2, fontWeight: 600, ml: 1 }} 
                />
              </Box>
            </Box>
            <Box textAlign={{ xs: 'left', sm: 'right' }}>
              <Typography variant="h3" fontWeight={800} color="primary.main" sx={{ letterSpacing: '-0.5px' }}>
                ₹{typeof property.price === 'number' ? property.price.toLocaleString('en-IN') : property.price}
                <span style={{ fontSize: '18px', fontWeight: 500, color: theme.palette.text.secondary }}>/month</span>
              </Typography>
              <Typography variant="body2" color="text.secondary" mt={0.5}>
                Plus standard taxes & maintenance
              </Typography>
            </Box>
          </Box>
        </Box>

        <Grid container spacing={5}>
          {/* Main Info */}
          <Grid size={{ xs: 12, md: 8 }}>
            <Gallery media={property.media} />
            
            <Box mt={5} mb={3}>
              <Typography variant="h5" fontWeight={700} gutterBottom>About this property</Typography>
            </Box>

            <Divider sx={{ my: 4 }} />

            <Box mb={5}>
              <Typography variant="h5" fontWeight={700} gutterBottom>Description</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.8 }}>
                {property.description || 'No description provided.'}
              </Typography>
            </Box>

            <Box mb={5}>
              <Typography variant="h5" fontWeight={700} gutterBottom>Location & Neighborhood</Typography>
              <Paper elevation={0} sx={{ p: 3, borderRadius: 5, border: `1px solid ${theme.palette.divider}`, bgcolor: alpha(theme.palette.primary.main, 0.02), mb: 3 }}>
                 <Typography variant="subtitle1" fontWeight={700} mb={2}>Nearby Points of Interest</Typography>
                 
                 {/* Category Filter Tabs */}
                 <Box display="flex" gap={1} overflow="auto" pb={2} mb={3} sx={{ '&::-webkit-scrollbar': { display: 'none' } }}>
                    {amenityCategories.map((cat) => (
                      <Chip
                        key={cat.key}
                        label={cat.label}
                        clickable
                        variant={activeCategoryTab === cat.key ? "filled" : "outlined"}
                        color={activeCategoryTab === cat.key ? "primary" : "default"}
                        onClick={() => {
                          setActiveCategoryTab(cat.key);
                          setSelectedPoi(null);
                          // Briefly show skeletons while filteredPois re-derives
                          // from the new category — prevents "No amenities" flash.
                          setIsPoisLoading(true);
                          setTimeout(() => setIsPoisLoading(false), 120);
                        }}
                        sx={{ borderRadius: 4, px: 1, fontWeight: 600 }}
                      />
                    ))}
                 </Box>

                 <Grid container spacing={2}>
                    {/* Skeleton shimmer — shown while POIs are loading */}
                    {isPoisLoading && Array.from({ length: 4 }).map((_, i) => (
                      <Grid key={`skel-${i}`} size={{ xs: 12, sm: 4 }}>
                        <Box sx={{
                          display: 'flex', alignItems: 'center', gap: 1.5,
                          p: 1.5, borderRadius: 3,
                          border: '1px solid transparent',
                        }}>
                          {/* Avatar skeleton */}
                          <Box sx={{
                            width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                            background: 'linear-gradient(90deg, #e8edf3 25%, #f5f8fc 50%, #e8edf3 75%)',
                            backgroundSize: '200% 100%',
                            animation: 'shimmer 1.4s ease-in-out infinite',
                            '@keyframes shimmer': {
                              '0%':   { backgroundPosition: '200% 0' },
                              '100%': { backgroundPosition: '-200% 0' },
                            },
                          }} />
                          {/* Text lines skeleton */}
                          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 0.8 }}>
                            <Box sx={{
                              height: 12, borderRadius: 1, width: '70%',
                              background: 'linear-gradient(90deg, #e8edf3 25%, #f5f8fc 50%, #e8edf3 75%)',
                              backgroundSize: '200% 100%',
                              animation: 'shimmer 1.4s ease-in-out infinite',
                              animationDelay: `${i * 0.08}s`,
                            }} />
                            <Box sx={{
                              height: 10, borderRadius: 1, width: '50%',
                              background: 'linear-gradient(90deg, #e8edf3 25%, #f5f8fc 50%, #e8edf3 75%)',
                              backgroundSize: '200% 100%',
                              animation: 'shimmer 1.4s ease-in-out infinite',
                              animationDelay: `${i * 0.08 + 0.1}s`,
                            }} />
                          </Box>
                        </Box>
                      </Grid>
                    ))}

                    {/* Actual POI cards — only shown when not loading */}
                    {!isPoisLoading && filteredPois.map((p: any, i: number) => {
                      const isSelected = selectedPoi?.name === p.name && selectedPoi?.lat === p.lat;
                      return (
                        <Grid key={i} size={{ xs: 12, sm: 4 }}>
                           <Box 
                              onClick={() => setSelectedPoi(isSelected ? null : p)}
                              sx={{ 
                                 display: 'flex', 
                                 alignItems: 'center', 
                                 gap: 1.5,
                                 p: 1.5,
                                 borderRadius: 3,
                                 cursor: 'pointer',
                                 transition: 'all 0.2s ease',
                                 border: '1px solid',
                                 borderColor: isSelected ? 'primary.main' : 'transparent',
                                 bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.08) : 'transparent',
                                 '&:hover': {
                                    bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.12) : alpha(theme.palette.text.primary, 0.04),
                                    transform: 'translateY(-2px)'
                                 }
                              }}
                           >
                              <Avatar sx={{ 
                                 bgcolor: isSelected ? 'primary.main' : alpha(theme.palette.primary.main, 0.1), 
                                 color: isSelected ? 'white' : 'primary.main', 
                                 width: 36, 
                                 height: 36,
                                 transition: 'all 0.2s ease'
                              }}>
                                 {/* Show a spinning ring while this card's route is loading */}
                                 {isSelected && fetchingRoute ? (
                                   <Box sx={{
                                     width: 18, height: 18, borderRadius: '50%',
                                     border: '2px solid rgba(255,255,255,0.35)',
                                     borderTopColor: '#fff',
                                     animation: 'spin 0.7s linear infinite',
                                     '@keyframes spin': { to: { transform: 'rotate(360deg)' } },
                                   }} />
                                 ) : getCategoryIcon(p.category)}
                              </Avatar>
                              <Box sx={{ overflow: 'hidden', flex: 1 }}>
                                 <Typography variant="body2" fontWeight={700} color={isSelected ? 'primary.main' : 'text.primary'} noWrap>{p.name}</Typography>
                                 <Typography variant="caption" color="text.secondary">
                                    {p.category.toUpperCase()} • ~{p.distance_m || p.distance || 0}m
                                 </Typography>
                                 {/* Inline "Calculating…" label beneath the selected card */}
                                 {isSelected && fetchingRoute && (
                                   <Typography variant="caption" color="primary.main" fontWeight={700} display="block">
                                     Calculating route…
                                   </Typography>
                                 )}
                              </Box>
                           </Box>
                        </Grid>
                      );
                    })}

                    {/* Empty state — ONLY shown when not loading AND list is empty */}
                    {!isPoisLoading && filteredPois.length === 0 && (
                      <Grid size={{ xs: 12 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                          No amenities found for this category nearby.
                        </Typography>
                      </Grid>
                    )}
                 </Grid>
              </Paper>

              {selectedPoi && (
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 2.5, 
                    mb: 3, 
                    borderRadius: 5, 
                    border: `1px solid ${theme.palette.primary.main}`, 
                    bgcolor: alpha(theme.palette.primary.main, 0.01),
                  }}
                >
                  <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
                    <Box>
                      <Typography variant="subtitle2" fontWeight={600} color="text.secondary">NAVIGATION TO AMENITY</Typography>
                      <Typography variant="h6" fontWeight={800} color="text.primary">{selectedPoi.name}</Typography>
                    </Box>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Button 
                        variant={commuteMode === 'driving' ? 'contained' : 'outlined'} 
                        size="small"
                        onClick={() => setCommuteMode('driving')}
                        startIcon={<Commute />}
                        sx={{ borderRadius: 2 }}
                      >
                        Drive
                      </Button>
                      <Button 
                        variant={commuteMode === 'walking' ? 'contained' : 'outlined'} 
                        size="small"
                        onClick={() => setCommuteMode('walking')}
                        startIcon={<DirectionsRun />}
                        sx={{ borderRadius: 2 }}
                      >
                        Walk
                      </Button>
                      <Button 
                        variant={commuteMode === 'cycling' ? 'contained' : 'outlined'} 
                        size="small"
                        onClick={() => setCommuteMode('cycling')}
                        startIcon={<DirectionsBike />}
                        sx={{ borderRadius: 2 }}
                      >
                        Bike
                      </Button>
                    </Box>
                  </Box>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  {fetchingRoute ? (
                    <Typography variant="body2" color="text.secondary">Calculating route details...</Typography>
                  ) : selectedRoute ? (
                    <Box display="flex" gap={4}>
                      <Box>
                        <Typography variant="caption" color="text.secondary" display="block">ESTIMATED TIME</Typography>
                        <Typography variant="h5" fontWeight={800} color="primary.main">
                          {formatCommuteTime(selectedRoute)}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary" display="block">DISTANCE</Typography>
                        <Typography variant="h5" fontWeight={800} color="text.primary">
                          {selectedRoute.distance_km} km
                        </Typography>
                      </Box>
                      {selectedRoute.estimated && (
                        <Box display="flex" alignItems="end">
                          <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                            (Straight-line estimate)
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">Select an amenity to see distance and travel time.</Typography>
                  )}
                </Paper>
              )}

              <Box sx={{ height: 350, borderRadius: 6, overflow: 'hidden', border: `1px solid ${theme.palette.divider}` }}>
                <PropertyMap 
                  property={property} 
                  commuteData={commuteData} 
                  pois={filteredPois}
                  selectedRoute={selectedRoute}
                  selectedPoi={selectedPoi}
                  isRouteLoading={fetchingRoute}
                  onPoiClick={(p) => setSelectedPoi(p)}
                />
              </Box>
            </Box>

            {/* REVIEWS SECTION */}
            <Divider sx={{ my: 4 }} />
            <Box mb={5}>
              <Typography variant="h5" fontWeight={700} gutterBottom>Reviews & Ratings</Typography>
              <Box mb={3} p={3} border={`1px solid ${theme.palette.divider}`} borderRadius={4}>
                <Typography variant="subtitle1" fontWeight={600} mb={1}>Write a Review</Typography>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                   <Rating value={newReviewRating} onChange={(_, v) => setNewReviewRating(v)} />
                </Box>
                <TextField 
                   fullWidth multiline rows={3} placeholder="Share your experience..." 
                   value={newReviewText} onChange={e => setNewReviewText(e.target.value)}
                   sx={{ mb: 2 }}
                />
                <Button variant="contained" sx={{ mt: 2 }} onClick={handleReviewSubmit}>Submit Review</Button>
              </Box>
              
              <Box display="flex" flexDirection="column" gap={3}>
                {reviews.length === 0 ? (
                   <Typography variant="body2" color="text.secondary">No reviews yet. Be the first!</Typography>
                ) : (
                   reviews.map((rev: any) => (
                     <Box key={rev.id} p={2} bgcolor={alpha(theme.palette.background.paper, 0.5)} borderRadius={3} border={`1px solid ${theme.palette.divider}`}>
                        <Box display="flex" alignItems="center" gap={1} mb={1}>
                          <Rating value={rev.rating} readOnly size="small" />
                          <Typography variant="caption" color="text.secondary">{new Date(rev.created_at).toLocaleDateString()}</Typography>
                        </Box>
                        <Typography variant="body2">{rev.text}</Typography>
                     </Box>
                   ))
                )}
              </Box>
            </Box>

          </Grid>

          {/* Sidebar */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Box sx={{ position: 'sticky', top: 100 }}>
              <Paper 
                elevation={0}
                sx={{ 
                  p: 4, 
                  borderRadius: 6, 
                  border: `1px solid ${theme.palette.divider}`,
                  bgcolor: alpha(theme.palette.background.paper, 0.4),
                  backdropFilter: 'blur(20px)',
                  mb: 4
                }}
              >
                <Typography variant="h4" fontWeight={800} color="primary.main" gutterBottom>
                  ₹ {typeof property.price === 'number' ? property.price.toLocaleString('en-IN') : '0'} <Typography component="span" variant="body1" color="text.secondary">/mo</Typography>
                </Typography>
                
                <Box display="flex" alignItems="center" gap={1} mb={4}>
                   <Star sx={{ color: '#FFB800' }} />
                   <Typography variant="subtitle1" fontWeight={700}>{property.average_rating ? property.average_rating.toFixed(1) : 'New'}</Typography>
                   <Typography variant="caption" color="text.secondary">({property.reviews_count || 0} reviews)</Typography>
                </Box>

                <Box mb={4}>
                  <Typography variant="subtitle2" fontWeight={700} gutterBottom>Pick a Visit Date</Typography>
                  <LocalizationProvider dateAdapter={AdapterDayjs}>
                    <DatePicker 
                      value={selectedDate} 
                      onChange={(newValue) => setSelectedDate(newValue)}
                      sx={{ width: '100%' }}
                    />
                  </LocalizationProvider>
                </Box>

                <Button 
                   variant="contained" fullWidth size="large" sx={{ height: 60, borderRadius: 3, mb: 2 }}
                   onClick={() => setChatOpen(true)}
                >
                  Contact Host
                </Button>
                <Button 
                  variant="outlined" fullWidth size="large" 
                  sx={{ height: 60, borderRadius: 3 }}
                  onClick={handleScheduleVisit}
                  disabled={!selectedDate}
                >
                  Schedule a Visit
                </Button>

                <Typography variant="caption" display="block" textAlign="center" mt={2} color="text.secondary">
                   No booking fees for first-time tenants.
                </Typography>
              </Paper>

              <HostCard host={property.host} />

              {(profile?.role === 'owner' || profile?.role === 'admin') && (
                <Box mt={4}>
                  <Button 
                    variant="contained" 
                    color="secondary" 
                    fullWidth 
                    size="large" 
                    sx={{ height: 60, borderRadius: 3 }}
                    onClick={handleGenerateAgreement}
                  >
                    Generate Agreement
                  </Button>
                  <Typography variant="caption" color="text.secondary" display="block" textAlign="center" mt={1}>
                    Initiate digital rental contract with tenant.
                  </Typography>
                </Box>
              )}
            </Box>
          </Grid>

        </Grid>
      </Container>
      
      {chatOpen && property.host && (
         <ChatBox 
            propertyId={property.id} 
            hostId={property.host.id || ''} 
            hostName={property.host.name || 'Host'} 
            onClose={() => setChatOpen(false)} 
         />
      )}
    </Box>
  );
}
