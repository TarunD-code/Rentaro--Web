import React, { useEffect, useRef, useState } from 'react';
import { Box } from '@mui/material';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY || 'VGr2EA4T8DcPNjZSXJos';

// Bengaluru city centre — used as the accuracy-guard fallback
const BLR_LNG = 77.5946;
const BLR_LAT = 12.9716;

interface MapViewProps {
  center: [number, number]; // [lat, lng]
  zoom: number;
  properties: any[];
  pois: any[];
  favorites: number[];
  onLike: (id: number) => void;
  darkMode?: boolean;
  onBoundsChange?: (bounds: {
    minLat: number; minLng: number;
    maxLat: number; maxLng: number;
  }) => void;
}

const MapView: React.FC<MapViewProps> = ({
  center,
  zoom,
  properties,
  pois,
  favorites,
  darkMode = false,
  onBoundsChange,
}) => {
  const mapContainer    = useRef<HTMLDivElement>(null);
  const mapRef          = useRef<maplibregl.Map | null>(null);
  const markersRef      = useRef<maplibregl.Marker[]>([]);
  const poiMarkersRef   = useRef<maplibregl.Marker[]>([]);
  const geoControlRef   = useRef<maplibregl.GeolocateControl | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  const styleUrl = darkMode
    ? `https://api.maptiler.com/maps/darkmatter/style.json?key=${MAPTILER_KEY}`
    : `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`;

  // Stable ref so moveend never captures a stale onBoundsChange closure
  const onBoundsChangeRef = useRef(onBoundsChange);
  useEffect(() => { onBoundsChangeRef.current = onBoundsChange; }, [onBoundsChange]);

  // ── Map initialisation ──────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: styleUrl,
      center: [center[1], center[0]], // MapLibre: [lng, lat]
      zoom,
      attributionControl: false,
      maxZoom: 18,
      minZoom: 3,
    });

    // Suppress missing symbol-layer image warnings
    map.on('styleimagemissing', (e) => {
      if (!map || map.hasImage(e.id)) return;
      const canvas = document.createElement('canvas');
      canvas.width = 16; canvas.height = 16;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.fillStyle = 'rgba(0,0,0,0)';
        ctx.fillRect(0, 0, 16, 16);
        try { map.addImage(e.id, ctx.getImageData(0, 0, 16, 16)); } catch (_) {}
      }
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    // GeolocateControl — blue dot + accuracy circle
    const geoControl = new maplibregl.GeolocateControl({
      positionOptions: { enableHighAccuracy: true, timeout: 8000 },
      trackUserLocation: true,
      showAccuracyCircle: true,
      showUserHeading: true,
    });
    map.addControl(geoControl, 'top-right');
    geoControlRef.current = geoControl;

    map.on('load', () => {
      setMapLoaded(true);

      // ── Auto-locate on mount ──────────────────────────────────────────────
      // Accuracy guard: desktop browsers often return ISP-based locations with
      // accuracy radii > 3 000 m, placing the user well outside Bengaluru.
      // When accuracy is poor we snap to central Bengaluru at zoom 12 so the
      // user always sees the relevant market rather than a random suburb.
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            const { latitude, longitude, accuracy } = pos.coords;
            if (accuracy > 3000) {
              // Imprecise (desktop / IP triangulation) — show full city
              map.flyTo({
                center: [BLR_LNG, BLR_LAT],
                zoom: 12,
                speed: 1.2,
                curve: 1.3,
                essential: true,
              });
            } else {
              // Precise (GPS / mobile) — zoom to actual position
              map.flyTo({
                center: [longitude, latitude],
                zoom: 14,
                speed: 1.4,
                curve: 1.2,
                essential: true,
              });
            }
            try { geoControl.trigger(); } catch (_) {}
          },
          // Permission denied or unavailable — stay on the passed-in center
          () => { try { geoControl.trigger(); } catch (_) {} },
          { enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 }
        );
      }

      // ── moveend -> emit bounding box ─────────────────────────────────────
      // Using a ref so the latest callback is always called without rebuilding
      // the map when the prop changes.
      map.on('moveend', () => {
        const cb = onBoundsChangeRef.current;
        if (!cb) return;
        const b = map.getBounds();
        cb({
          minLat: b.getSouth(),
          minLng: b.getWest(),
          maxLat: b.getNorth(),
          maxLng: b.getEast(),
        });
      });
    });

    mapRef.current = map;

    return () => {
      markersRef.current.forEach((m) => m.remove());
      poiMarkersRef.current.forEach((m) => m.remove());
      if (mapRef.current === map) {
        map.remove();
        mapRef.current = null;
      }
    };
  // styleUrl is the only lifecycle dep — center/zoom changes use flyTo below
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [styleUrl]);

  // ── Fly to center when prop changes ────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || center[0] === 0) return;
    let lat = center[0];
    let lng = center[1];
    // Snap near-Bengaluru coords to exact city centre
    if (Math.abs(lat - BLR_LAT) < 0.15 && Math.abs(lng - BLR_LNG) < 0.15) {
      lat = BLR_LAT; lng = BLR_LNG;
    }
    mapRef.current.flyTo({ center: [lng, lat], zoom, speed: 1.2, curve: 1.4, essential: true });
  }, [center, zoom]);

  // ── Property price-pill markers ─────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    properties.forEach((property) => {
      const lat = property.address?.geo?.lat ?? property.address_geo_lat ?? property.lat;
      const lng = property.address?.geo?.lng ?? property.address_geo_lng ?? property.lng;
      if (typeof lat !== 'number' || typeof lng !== 'number' || !isFinite(lat) || !isFinite(lng)) return;

      const isFavorite = favorites.includes(property.id);
      const el = document.createElement('div');
      el.className = 'rentora-property-marker';
      el.innerHTML = `
        <div style="
          background:${isFavorite
            ? 'linear-gradient(135deg,#f43f5e,#ec4899)'
            : 'linear-gradient(135deg,#6366f1,#8b5cf6)'};
          color:white;padding:6px 12px;border-radius:20px;font-size:12px;font-weight:700;
          box-shadow:0 4px 12px rgba(0,0,0,0.25);cursor:pointer;
          transition:transform 0.2s ease;white-space:nowrap;font-family:'Inter',sans-serif;">
          ₹${(property.price || 0).toLocaleString('en-IN')}
        </div>`;
      el.addEventListener('mouseenter', () => {
        (el.firstElementChild as HTMLElement).style.transform = 'scale(1.15)';
        el.style.zIndex = '100';
      });
      el.addEventListener('mouseleave', () => {
        (el.firstElementChild as HTMLElement).style.transform = 'scale(1)';
        el.style.zIndex = '1';
      });

      const popup = new maplibregl.Popup({ offset: 25, closeButton: true, maxWidth: '260px' })
        .setHTML(`
          <div style="width:240px;font-family:'Inter',sans-serif;">
            ${property.media?.length
              ? `<img src="${property.media[0].url || property.media[0].thumbnailUrl}"
                   style="width:100%;height:140px;object-fit:cover;border-radius:8px 8px 0 0;"
                   alt="${property.title}" />`
              : ''}
            <div style="padding:10px;">
              <div style="font-weight:700;font-size:14px;margin-bottom:4px;color:#1e293b;">${property.title}</div>
              <div style="font-size:16px;font-weight:800;color:#6366f1;margin-bottom:6px;">
                ₹${(property.price || 0).toLocaleString('en-IN')}
                <span style="font-size:12px;color:#94a3b8;font-weight:400;">/mo</span>
              </div>
              <div style="font-size:11px;padding:3px 8px;background:#f1f5f9;border-radius:12px;
                          display:inline-block;color:#64748b;text-transform:uppercase;">
                ${property.property_type || 'Apartment'}
              </div>
              <div style="margin-top:10px;text-align:center;">
                <a href="/listings/${property.id}" style="
                  display:inline-block;padding:6px 16px;background:#6366f1;color:white;
                  border-radius:6px;text-decoration:none;font-size:12px;font-weight:600;">
                  View Details
                </a>
              </div>
            </div>
          </div>`);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([lng, lat]).setPopup(popup).addTo(mapRef.current!);
      el.addEventListener('click', (e) => { e.stopPropagation(); marker.togglePopup(); });
      markersRef.current.push(marker);
    });
  }, [properties, favorites, mapLoaded]);

  // ── POI emoji markers ───────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    poiMarkersRef.current.forEach((m) => m.remove());
    poiMarkersRef.current = [];

    const categoryConfig: Record<string, { icon: string; color: string }> = {
      metro:      { icon: '🚇', color: '#1a73e8' },
      hospital:   { icon: '🏥', color: '#d93025' },
      school:     { icon: '🏫', color: '#f9ab00' },
      grocery:    { icon: '🛒', color: '#34a853' },
      office:     { icon: '🏢', color: '#5f6368' },
      park:       { icon: '🌳', color: '#0d652d' },
      gym:        { icon: '💪', color: '#e8710a' },
      restaurant: { icon: '🍽️', color: '#c5221f' },
      pharmacy:   { icon: '💊', color: '#137333' },
      bus:        { icon: '🚌', color: '#1967d2' },
      mall:       { icon: '🛍️', color: '#9334e6' },
      fuel:       { icon: '⛽', color: '#e37400' },
      college:    { icon: '🎓', color: '#185abc' },
      coworking:  { icon: '💼', color: '#7c3aed' },
    };

    pois.forEach((poi) => {
      if (typeof poi.lat !== 'number' || typeof poi.lng !== 'number') return;
      const config = categoryConfig[poi.category] || { icon: '📍', color: '#5f6368' };

      const el = document.createElement('div');
      el.innerHTML = `
        <div style="background:white;border-radius:50%;width:30px;height:30px;
          display:flex;align-items:center;justify-content:center;
          box-shadow:0 2px 8px rgba(0,0,0,0.2);font-size:16px;
          border:2px solid ${config.color};cursor:pointer;
          transition:transform 0.2s ease;">${config.icon}</div>`;
      el.addEventListener('mouseenter', () => {
        (el.firstElementChild as HTMLElement).style.transform = 'scale(1.2)';
      });
      el.addEventListener('mouseleave', () => {
        (el.firstElementChild as HTMLElement).style.transform = 'scale(1)';
      });

      const popup = new maplibregl.Popup({ offset: 20, closeButton: false }).setHTML(`
        <div style="font-family:'Inter',sans-serif;padding:4px;">
          <div style="font-weight:700;font-size:13px;">${poi.name}</div>
          <div style="font-size:11px;color:${config.color};text-transform:uppercase;font-weight:600;">
            ${poi.category}
          </div>
          ${poi.distance
            ? `<div style="font-size:11px;color:#94a3b8;margin-top:2px;">~${poi.distance}m away</div>`
            : ''}
        </div>`);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([poi.lng, poi.lat]).setPopup(popup).addTo(mapRef.current!);
      poiMarkersRef.current.push(marker);
    });
  }, [pois, mapLoaded]);

  return (
    <Box sx={{
      height: '600px', borderRadius: 6, overflow: 'hidden',
      border: '1px solid', borderColor: 'divider',
      bgcolor: 'background.paper', position: 'relative', zIndex: 0,
    }}>
      <div ref={mapContainer} style={{ height: '100%', width: '100%' }} />
    </Box>
  );
};

export default MapView;
