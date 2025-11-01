import type {
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

export async function fetchEventRecommendations(
  request: GetEventRecommendationsRequest,
  options?: RequestInit,
): Promise<GetEventRecommendationsResponse> {
  if (MOCK_ENABLED) {
    return {
      events: getMockEvents(request.number_events).map(normalizeEvent),
    };
  }

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

function normalizeEvent(event: Event): Event {
  return {
    ...event,
    link: event.link ?? undefined,
  };
}

function getMockEvents(limit: number): Event[] {
  return MOCK_EVENTS.slice(0, Math.max(0, limit));
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
