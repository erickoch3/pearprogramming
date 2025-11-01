import { useCallback, useEffect, useState } from "react";

import { fetchEventRecommendations } from "@/lib/api";
import type {
  Event,
  GetEventRecommendationsRequest,
  GetEventRecommendationsResponse,
} from "@/types/events";

export interface UseEventRecommendationsOptions {
  autoLoad?: boolean;
}

export interface UseEventRecommendationsResult {
  events: Event[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<GetEventRecommendationsResponse | void>;
}

export function useEventRecommendations(
  request: GetEventRecommendationsRequest,
  { autoLoad = true }: UseEventRecommendationsOptions = {},
): UseEventRecommendationsResult {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState<boolean>(autoLoad);
  const [error, setError] = useState<string | null>(null);

  // Destructure primitive values to avoid object reference issues in dependencies
  const numberEvents = request.number_events;
  const responsePreferences = request.response_preferences;

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Reconstruct request object from stable primitive values
      const requestPayload: GetEventRecommendationsRequest = {
        number_events: numberEvents,
        response_preferences: responsePreferences,
      };
      const response = await fetchEventRecommendations(requestPayload);
      setEvents(response.events);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [numberEvents, responsePreferences]);

  useEffect(() => {
    if (!autoLoad) {
      return;
    }

    void refresh();
  }, [autoLoad, refresh]);

  return {
    events,
    loading,
    error,
    refresh,
  };
}
