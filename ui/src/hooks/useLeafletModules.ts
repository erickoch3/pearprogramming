import { useEffect, useState } from "react";

type LeafletLib = typeof import("react-leaflet");
type LeafletCore = typeof import("leaflet");

export interface LeafletModules {
  MapContainer: LeafletLib["MapContainer"];
  Marker: LeafletLib["Marker"];
  Popup: LeafletLib["Popup"];
  TileLayer: LeafletLib["TileLayer"];
  useMap: LeafletLib["useMap"];
  divIcon: LeafletCore["divIcon"];
}

export function useLeafletModules() {
  const [modules, setModules] = useState<LeafletModules | null>(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      const [leafletLib, leafletCore] = await Promise.all([
        import("react-leaflet"),
        import("leaflet"),
      ]);

      if (!mounted) {
        return;
      }

      setModules({
        MapContainer: leafletLib.MapContainer,
        Marker: leafletLib.Marker,
        Popup: leafletLib.Popup,
        TileLayer: leafletLib.TileLayer,
        useMap: leafletLib.useMap,
        divIcon: leafletCore.divIcon,
      });
    }

    void load();

    return () => {
      mounted = false;
    };
  }, []);

  return modules;
}

