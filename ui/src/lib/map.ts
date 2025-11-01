import type { Coordinates } from "@/types/events";

export const EDINBURGH_CENTER: [number, number] = [55.9533, -3.1883];
const DEGREE_SCALE = 0.01;

export function toLatLng([x, y]: Coordinates): [number, number] {
  const lat = EDINBURGH_CENTER[0] + y * DEGREE_SCALE;
  const lng = EDINBURGH_CENTER[1] + x * DEGREE_SCALE;
  return [lat, lng];
}

