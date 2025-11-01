"use client";

import { useEffect, useState } from "react";

import { useLeafletModules } from "@/hooks/useLeafletModules";
import { useUserSettings } from "@/hooks/useUserSettings";
import type { MapMode } from "@/hooks/useUserSettings";
import { EDINBURGH_CENTER, toLatLng } from "@/lib/map";
import type { Event } from "@/types/events";

import type { Map as LeafletMap } from "leaflet";
type LeafletCore = typeof import("leaflet");

interface UserLocation {
  lat: number;
  lng: number;
}

const MAP_TILES: Record<MapMode, { url: string; attribution: string }> = {
  standard: {
    url: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
  dark: {
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
  satellite: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution:
      "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
  },
};

export interface MapViewProps {
  events: Event[];
}

// Component to update map bounds - must be inside MapContainer
function MapUpdater({ events, userLocation, useMapHook }: {
  events: Event[];
  userLocation: UserLocation | null;
  useMapHook: () => LeafletMap;
}) {
  const map = useMapHook();
  const [hasInitialized, setHasInitialized] = useState(false);

  useEffect(() => {
    if (!map || events.length === 0) return;

    const bounds: [number, number][] = [];

    // Add all event locations
    events.forEach((event) => {
      const latLng = toLatLng(event.location);
      bounds.push([latLng[0], latLng[1]]);
    });

    // Add user location if available
    if (userLocation) {
      bounds.push([userLocation.lat, userLocation.lng]);
    }

    // Fit bounds with padding
    if (bounds.length > 0) {
      map.fitBounds(bounds, {
        padding: [50, 50],
        maxZoom: 14,
        animate: hasInitialized, // Don't animate on first load
        duration: 0.5,
      });

      if (!hasInitialized) {
        setHasInitialized(true);
      }
    }
  }, [map, events, userLocation, hasInitialized]);

  return null;
}

export function MapView({ events }: MapViewProps) {
  const leafletModules = useLeafletModules();
  const { mapMode } = useUserSettings();
  const [userLocation, setUserLocation] = useState<UserLocation | null>(null);

  useEffect(() => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          });
        },
        (error) => {
          console.warn("Could not get user location:", error);
        }
      );
    }
  }, []);

  if (!leafletModules) {
    return (
      <div className="flex h-full w-full items-center justify-center rounded-2xl border border-dashed border-neutral-300 text-neutral-500 dark:border-neutral-700 dark:text-neutral-400">
        Loading map...
      </div>
    );
  }

  const { MapContainer, Marker, Popup, TileLayer, useMap, divIcon } = leafletModules;
  const tileConfig = MAP_TILES[mapMode];

  return (
    <MapContainer
      center={EDINBURGH_CENTER}
      zoom={13}
      className="h-full w-full rounded-2xl overflow-hidden"
      style={{ height: "100%", minHeight: "400px" }}
      scrollWheelZoom
      zoomControl={false}
    >
      <TileLayer
        key={mapMode}
        attribution={tileConfig.attribution}
        url={tileConfig.url}
        maxZoom={20}
      />

      <MapUpdater events={events} userLocation={userLocation} useMapHook={useMap} />

      {userLocation && (
        <Marker
          position={[userLocation.lat, userLocation.lng]}
          icon={createUserLocationIcon(divIcon)}
          zIndexOffset={1000}
        />
      )}

      {events.map((event) => (
        <Marker
          key={`${event.name}-${event.location[0]}-${event.location[1]}`}
          position={toLatLng(event.location)}
          icon={createEmojiIcon(divIcon, event.emoji)}
        >
          <Popup className="modern-popup" maxWidth={280} closeButton={false}>
            <div className="space-y-2.5 p-1">
              <div className="flex items-start gap-2.5">
                <div className="text-2xl leading-none">{event.emoji}</div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-base text-neutral-900 dark:text-neutral-50 leading-tight">
                    {event.name}
                  </h3>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1.5 leading-relaxed">
                    {event.description}
                  </p>
                </div>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-neutral-200 dark:border-neutral-700">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">Score:</span>
                  <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                    {event.event_score}/10
                  </span>
                </div>
                {event.link ? (
                  <a
                    href={event.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
                  >
                    View details →
                  </a>
                ) : null}
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

function createUserLocationIcon(divIconFn: LeafletCore["divIcon"]) {
  return divIconFn({
    html: `
      <div class="user-location-marker">
        <div class="user-location-accuracy"></div>
        <div class="user-location-pulse-ring"></div>
        <div class="user-location-dot"></div>
      </div>
    `,
    className: "",
    iconSize: [100, 100],
    iconAnchor: [50, 50],
  });
}

function createEmojiIcon(divIconFn: LeafletCore["divIcon"], emoji: string) {
  return divIconFn({
    html: `
      <div class="modern-marker">
        <div class="marker-bg"></div>
        <div class="marker-emoji">${emoji}</div>
      </div>
    `,
    className: "",
    iconSize: [44, 44],
    iconAnchor: [22, 22],
    popupAnchor: [0, -16],
  });
}
