import React, { useRef, useEffect, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

const MapView = ({ data, onPointClick, selectedZone, showHeatmap }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markers = useRef([]);
  const [mapLoaded, setMapLoaded] = useState(false);

  // =============================
  // INIT MAP
  // =============================
  useEffect(() => {
    if (map.current) return;

    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [85.82, 20.30], // Bhubaneswar
      zoom: 11,
      pitch: 45
    });

    map.current.addControl(new mapboxgl.NavigationControl(), "top-right");
    map.current.addControl(new mapboxgl.FullscreenControl(), "top-right");
    map.current.addControl(
      new mapboxgl.ScaleControl({ maxWidth: 100, unit: "metric" }),
      "bottom-left"
    );

    map.current.on("load", () => {
      setMapLoaded(true);
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // =============================
  // MARKERS
  // =============================
  useEffect(() => {
    if (!mapLoaded || !data || !map.current) return;

    markers.current.forEach(m => m.remove());
    markers.current = [];

    const filteredData =
      selectedZone === "all"
        ? data
        : data.filter(p => p.zone === selectedZone);

    filteredData.forEach(point => {
      const el = document.createElement("div");

      const size = Math.max(
        12,
        Math.min(24, 12 + Math.abs(point.uhi_intensity) * 2)
      );

      Object.assign(el.style, {
        width: `${size}px`,
        height: `${size}px`,
        backgroundColor: point.color,
        borderRadius: "50%",
        border: "2px solid white",
        cursor: "pointer",
        boxShadow: "0 2px 4px rgba(0,0,0,0.3)"
      });

      const popup = new mapboxgl.Popup({
        offset: 25,
        maxWidth: "300px"
      }).setHTML(`
        <strong>${point.severity} Heat Zone</strong><br/>
        🌡️ Temp: ${point.lst.toFixed(1)}°C<br/>
        🔥 UHI: ${point.uhi_intensity.toFixed(1)}°C<br/>
        🌿 NDVI: ${point.ndvi.toFixed(3)}<br/>
        🌳 ${point.vegetation}<br/><br/>
        💡 ${point.recommendation}
      `);

      const marker = new mapboxgl.Marker(el)
        .setLngLat([point.lon, point.lat])
        .setPopup(popup)
        .addTo(map.current);

      el.onclick = () => onPointClick?.(point);
      markers.current.push(marker);
    });

    if (filteredData.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      filteredData.forEach(p => bounds.extend([p.lon, p.lat]));
      map.current.fitBounds(bounds, { padding: 50, maxZoom: 14 });
    }
  }, [data, mapLoaded, selectedZone, onPointClick]);

  // =============================
  // HEATMAP
  // =============================
  useEffect(() => {
    if (!mapLoaded || !data || !showHeatmap || !map.current) return;

    const id = "uhi-heatmap";

    if (map.current.getLayer(id)) map.current.removeLayer(id);
    if (map.current.getSource(id)) map.current.removeSource(id);

    map.current.addSource(id, {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features: data.map(p => ({
          type: "Feature",
          properties: {
            intensity: Math.abs(p.uhi_intensity),
            temperature: p.lst
          },
          geometry: {
            type: "Point",
            coordinates: [p.lon, p.lat]
          }
        }))
      }
    });

    map.current.addLayer({
      id,
      type: "heatmap",
      source: id,
      maxzoom: 15,
      paint: {
        "heatmap-weight": [
          "interpolate",
          ["linear"],
          ["get", "temperature"],
          25, 0,
          45, 1
        ],
        "heatmap-intensity": [
          "interpolate",
          ["linear"],
          ["zoom"],
          0, 1,
          15, 3
        ],
        "heatmap-radius": [
          "interpolate",
          ["linear"],
          ["zoom"],
          0, 2,
          15, 20
        ],
        "heatmap-color": [
          "interpolate",
          ["linear"],
          ["heatmap-density"],
          0, "rgba(0,0,255,0)",
          0.3, "rgb(0,255,255)",
          0.5, "rgb(255,255,0)",
          0.7, "rgb(255,165,0)",
          1, "rgb(255,0,0)"
        ],
        "heatmap-opacity": [
          "interpolate",
          ["linear"],
          ["zoom"],
          7, 1,
          15, 0.5
        ]
      }
    });
  }, [data, mapLoaded, showHeatmap]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div
        ref={mapContainer}
        style={{
          width: "100%",
          height: "100%",
          borderRadius: "12px"
        }}
      />

      {!mapLoaded && (
        <div style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "rgba(0,0,0,0.7)",
          color: "white",
          fontSize: "18px",
          fontWeight: "bold"
        }}>
          Loading Map...
        </div>
      )}
    </div>
  );
};

export default MapView;