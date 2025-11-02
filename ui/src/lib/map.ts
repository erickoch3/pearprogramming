import type { Coordinates } from "@/types/events";

export const EDINBURGH_CENTER: [number, number] = [55.9533, -3.1883];

/**
 * Convert coordinates to [latitude, longitude] format.
 * The coordinates are already latitude and longitude values,
 * so this function simply returns them in the correct order.
 */
export function toLatLng([x, y]: Coordinates): [number, number] {
  // x is latitude, y is longitude - return as [lat, lng] for Leaflet
  return [x, y];
}

