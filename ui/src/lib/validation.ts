import type { Event, GetEventRecommendationsResponse } from "@/types/events";

/**
 * Validates coordinate values are within valid latitude/longitude ranges
 */
function isValidCoordinate(lat: number, lng: number): boolean {
  return (
    typeof lat === "number" &&
    typeof lng === "number" &&
    !isNaN(lat) &&
    !isNaN(lng) &&
    lat >= -90 &&
    lat <= 90 &&
    lng >= -180 &&
    lng <= 180
  );
}

/**
 * Validates a single event object has all required fields with valid types
 */
type CoordinateObject = { x: number; y: number };

function toCoordinatePair(location: unknown): [number, number] | null {
  if (Array.isArray(location) && location.length === 2) {
    const [lat, lng] = location;
    return typeof lat === "number" && typeof lng === "number"
      ? [lat, lng]
      : null;
  }

  if (
    location &&
    typeof location === "object" &&
    "x" in location &&
    "y" in location
  ) {
    const { x, y } = location as CoordinateObject;
    return typeof x === "number" && typeof y === "number" ? [x, y] : null;
  }

  return null;
}

function isValidEvent(event: unknown): event is Event {
  if (!event || typeof event !== "object") return false;

  const e = event as Partial<Event>;

  // Check required fields
  if (typeof e.name !== "string" || e.name.length === 0) return false;
  if (typeof e.description !== "string") return false;
  if (typeof e.emoji !== "string" || e.emoji.length === 0) return false;
  if (typeof e.event_score !== "number" || isNaN(e.event_score)) return false;

  // Validate score range
  if (e.event_score < 0 || e.event_score > 10) return false;

  // Validate location
  const coords = toCoordinatePair(e.location);
  if (!coords) return false;
  const [lat, lng] = coords;
  if (!isValidCoordinate(lat, lng)) return false;

  // Validate optional link field
  if (e.link !== undefined && typeof e.link !== "string") return false;

  return true;
}

/**
 * Validates the API response structure and content
 * @throws Error if validation fails with descriptive message
 */
export function validateEventRecommendationsResponse(
  data: unknown,
): GetEventRecommendationsResponse {
  if (!data || typeof data !== "object") {
    throw new Error("Invalid API response: expected object");
  }

  const response = data as Partial<GetEventRecommendationsResponse>;

  if (!Array.isArray(response.events)) {
    throw new Error("Invalid API response: events must be an array");
  }

  // Validate each event
  const invalidEvents: number[] = [];
  response.events.forEach((event, index) => {
    if (!isValidEvent(event)) {
      invalidEvents.push(index);
    }
  });

  if (invalidEvents.length > 0) {
    throw new Error(
      `Invalid events at indices: ${invalidEvents.join(", ")}. Events must have valid name, description, emoji, location coordinates, and score (0-10).`,
    );
  }

  return response as GetEventRecommendationsResponse;
}
