import type {
  Coordinates,
  Event,
  GetEventRecommendationsRequest,
  GetEventRecommendationsResponse,
} from "@/types/events";
import { validateEventRecommendationsResponse } from "@/lib/validation";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

const EVENT_RECOMMENDATIONS_PATH = "/events/recommendations";
const MOCK_ENABLED =
  process.env.NEXT_PUBLIC_MOCK === "1" || process.env.MOCK === "1";
const RESPONSE_CACHE_TTL_MS = 60_000;

type ResponseCacheEntry = {
  timestamp: number;
  payload: GetEventRecommendationsResponse;
};

const inFlightRequests = new Map<string, Promise<GetEventRecommendationsResponse>>();
const responseCache = new Map<string, ResponseCacheEntry>();

export async function fetchEventRecommendations(
  request: GetEventRecommendationsRequest,
  options?: RequestInit,
): Promise<GetEventRecommendationsResponse> {
  if (MOCK_ENABLED) {
    return {
      events: getMockEvents(request.number_events).map(normalizeEvent),
    };
  }

  const cacheKey = buildCacheKey(request, options);
  const now = Date.now();

  const cached = responseCache.get(cacheKey);
  if (cached && now - cached.timestamp < RESPONSE_CACHE_TTL_MS) {
    return cloneResponse(cached.payload);
  }

  let pending = inFlightRequests.get(cacheKey);
  if (!pending) {
    pending = requestEventRecommendations(request, options)
      .then((response) => {
        responseCache.set(cacheKey, {
          timestamp: Date.now(),
          payload: response,
        });
        return response;
      })
      .finally(() => {
        inFlightRequests.delete(cacheKey);
      });
    inFlightRequests.set(cacheKey, pending);
  }

  const response = await pending;
  return cloneResponse(response);
}

async function requestEventRecommendations(
  request: GetEventRecommendationsRequest,
  options?: RequestInit,
): Promise<GetEventRecommendationsResponse> {
  const response = await fetch(`${API_BASE_URL}${EVENT_RECOMMENDATIONS_PATH}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    body: JSON.stringify(request),
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `Failed to fetch event recommendations: ${response.status} ${errorText}`,
    );
  }

  const rawData = await response.json();
  const payload = validateEventRecommendationsResponse(rawData);

  return {
    events: payload.events.map(normalizeEvent),
  };
}

type LocationObject = { x: number; y: number };
type RawLocation = Event["location"] | LocationObject;
type RawEvent = Omit<Event, "location" | "link"> & {
  location: RawLocation;
  link?: string | null;
};

function normalizeEvent(event: RawEvent): Event {
  const location = Array.isArray(event.location)
    ? event.location
    : [(event.location as LocationObject).x, (event.location as LocationObject).y];

  return {
    ...event,
    location,
    link: event.link ?? undefined,
  };
}

function getMockEvents(limit: number): Event[] {
  return MOCK_EVENTS.slice(0, Math.max(0, limit));
}

function buildCacheKey(
  request: GetEventRecommendationsRequest,
  options?: RequestInit,
): string {
  const headers = options?.headers;
  // We only care about custom headers that might affect auth; stringify stable subset.
  const headerKey =
    headers instanceof Headers
      ? JSON.stringify(Object.fromEntries(headers.entries()))
      : headers && typeof headers === "object"
        ? JSON.stringify(Object.fromEntries(Object.entries(headers)))
        : "";
  return JSON.stringify({
    request,
    headerKey,
  });
}

function cloneResponse(
  response: GetEventRecommendationsResponse,
): GetEventRecommendationsResponse {
  return {
    events: response.events.map((event) => ({
      ...event,
      location: [...event.location] as Coordinates,
      link: event.link ?? undefined,
    })),
  };
}

const MOCK_EVENTS: Event[] = [
  {
    name: "Sunrise Arthurs Seat Hike",
    description: "Catch the sunrise over Edinburgh with a guided early morning climb.",
    emoji: "🌄",
    location: [1.5, -1.2],
    event_score: 9.2,
    link: "https://www.visitscotland.com/info/events/edinburgh-sunrise-hike-p123456",
  },
  {
    name: "Leith Street Food Market",
    description: "Sample dishes from 20+ local vendors, live music, and craft stalls.",
    emoji: "🍜",
    location: [0.3, 1.8],
    event_score: 8.7,
    link: "https://edinburghmarkets.com/leith-street-food",
  },
  {
    name: "Meadows Community Yoga",
    description: "Free outdoor yoga session suitable for all levels - bring a mat!",
    emoji: "🧘",
    location: [0.2, -0.8],
    event_score: 8.1,
    link: "https://facebook.com/events/edinburgh-meadows-yoga",
  },
  {
    name: "Portobello Beach Cleanup",
    description: "Join local volunteers to help clean the shoreline followed by coffee.",
    emoji: "🧹",
    location: [8.0, 0.2],
    event_score: 8.9,
    link: "https://keepedinburghbeautiful.org/portobello-cleanup",
  },
  {
    name: "Stockbridge Farmers Market",
    description: "Weekly market with artisan produce, fresh bakes, and local crafts.",
    emoji: "🧺",
    location: [-1.2, 0.8],
    event_score: 8.4,
    link: "https://stockbridgefarmersmarket.co.uk",
  },
  {
    name: "Water of Leith Cycle",
    description: "Guided family-friendly cycle along Water of Leith walkway.",
    emoji: "🚴",
    location: [-1.8, 0.5],
    event_score: 7.8,
  },
  {
    name: "Calton Hill Sketch Walk",
    description: "Urban sketching meetup—bring pencils and capture the skyline.",
    emoji: "✏️",
    location: [0.8, 0.3],
    event_score: 8.0,
  },
  {
    name: "Grassmarket Storytelling Night",
    description: "Local storytellers share Scottish folklore by candlelight.",
    emoji: "📖",
    location: [-0.5, -0.3],
    event_score: 8.6,
  },
];
