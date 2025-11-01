import { useCallback, useEffect, useState } from "react";

export type MapMode = "standard" | "dark" | "satellite";

export interface UseUserSettingsResult {
  mapMode: MapMode;
  setMapMode: (mode: MapMode) => void;
}

const MAP_MODE_STORAGE_KEY = "mapMode";
const DEFAULT_MAP_MODE: MapMode = "standard";

function isMapMode(value: unknown): value is MapMode {
  return value === "standard" || value === "dark" || value === "satellite";
}

export function useUserSettings(): UseUserSettingsResult {
  const [mapMode, setMapModeState] = useState<MapMode>(() => {
    if (typeof window === "undefined") {
      return DEFAULT_MAP_MODE;
    }
    const stored = window.localStorage.getItem(MAP_MODE_STORAGE_KEY);
    return isMapMode(stored) ? stored : DEFAULT_MAP_MODE;
  });

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const handleStorage = (event: StorageEvent) => {
      if (event.key === MAP_MODE_STORAGE_KEY && isMapMode(event.newValue)) {
        setMapModeState(event.newValue);
      }
    };

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const setMapMode = useCallback((mode: MapMode) => {
    setMapModeState(mode);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(MAP_MODE_STORAGE_KEY, mode);
    }
  }, []);

  return {
    mapMode,
    setMapMode,
  };
}

