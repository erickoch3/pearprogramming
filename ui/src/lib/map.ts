import type { Coordinates } from "@/types/events";

export const EDINBURGH_CENTER: [number, number] = [55.9533, -3.1883];
const LEGACY_DEGREE_SCALE = 0.01;

/**
 * Interpret stored coordinates as [latitude, longitude].
 * Older synthetic data used abstract cartesian offsets; those values were small (|value| < 1).
 * When we encounter Edinburgh lat/lng, we can return them directly to keep map markers precise.
 */
export function toLatLng([first, second]: Coordinates): [number, number] {
  const looksLikeLatitude = Math.abs(first) <= 90 && Math.abs(first) >= 1;
  const looksLikeLongitude = Math.abs(second) <= 180 && Math.abs(second) >= 1;

  if (looksLikeLatitude && looksLikeLongitude) {
    return [first, second];
  }

  // Fallback for legacy cartesian coordinates; treat first as x-offset, second as y-offset.
  const lat = EDINBURGH_CENTER[0] + second * LEGACY_DEGREE_SCALE;
  const lng = EDINBURGH_CENTER[1] + first * LEGACY_DEGREE_SCALE;
  return [lat, lng];
}
