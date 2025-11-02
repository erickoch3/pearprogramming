import { useCallback, useEffect, useState, useRef } from "react";
import type {
  Event,
  GetEventRecommendationsRequest,
} from "@/types/events";

export interface ProgressUpdate {
  status: string;
  message: string;
  progress: number;
}

export interface UseStreamingEventRecommendationsOptions {
  autoLoad?: boolean;
}

export interface UseStreamingEventRecommendationsResult {
  events: Event[];
  loading: boolean;
  error: string | null;
  progress: ProgressUpdate | null;
  refresh: () => void;
}

export function useStreamingEventRecommendations(
  request: GetEventRecommendationsRequest,
  { autoLoad = true }: UseStreamingEventRecommendationsOptions = {},
): UseStreamingEventRecommendationsResult {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState<boolean>(autoLoad);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const eventSourceRef = useRef<EventSource | AbortController | null>(null);

  // Destructure primitive values to avoid object reference issues in dependencies
  const numberEvents = request.number_events;
  const responsePreferences = request.response_preferences;

  const closeEventSource = useCallback(() => {
    if (eventSourceRef.current) {
      if (eventSourceRef.current instanceof EventSource) {
        eventSourceRef.current.close();
      } else if (eventSourceRef.current instanceof AbortController) {
        eventSourceRef.current.abort();
      }
      eventSourceRef.current = null;
    }
  }, []);

  const refresh = useCallback(() => {
    // Close any existing connection
    closeEventSource();

    setLoading(true);
    setError(null);
    setEvents([]);
    setProgress({
      status: "starting",
      message: "Initializing...",
      progress: 0,
    });

    try {
      // Construct the API URL
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const url = new URL(`${apiBaseUrl}/events/recommendations/stream`);

      // Create EventSource with POST-like parameters encoded in URL
      // Note: EventSource only supports GET, so we need to encode the request as query params
      const params = new URLSearchParams({
        number_events: numberEvents.toString(),
      });
      if (responsePreferences) {
        params.append("response_preferences", responsePreferences);
      }

      // For POST requests with EventSource, we need a workaround
      // We'll use fetch with streaming instead
      const controller = new AbortController();

      fetch(`${apiBaseUrl}/events/recommendations/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "text/event-stream",
        },
        body: JSON.stringify({
          number_events: numberEvents,
          response_preferences: responsePreferences,
        }),
        signal: controller.signal,
      })
        .then(async (response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const reader = response.body?.getReader();
          if (!reader) {
            throw new Error("No response body");
          }

          const decoder = new TextDecoder();
          let buffer = "";

          while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              if (!line.trim()) continue;

              const eventMatch = line.match(/^event: (.+)$/m);
              const dataMatch = line.match(/^data: (.+)$/m);

              if (eventMatch && dataMatch) {
                const eventType = eventMatch[1];
                const data = JSON.parse(dataMatch[1]);

                console.log(`[SSE] Received ${eventType}:`, data.progress ? `${data.progress}%` : '', data.message || '');

                if (eventType === "progress") {
                  setProgress({
                    status: data.status,
                    message: data.message,
                    progress: data.progress,
                  });
                } else if (eventType === "complete") {
                  setProgress({
                    status: data.status,
                    message: data.message,
                    progress: data.progress,
                  });
                  setEvents(data.events);
                  setLoading(false);
                } else if (eventType === "error") {
                  setError(data.message);
                  setLoading(false);
                }
              }
            }
          }
        })
        .catch((err) => {
          if (err.name === "AbortError") {
            return; // Request was cancelled
          }
          const message = err instanceof Error ? err.message : "Unknown error";
          setError(message);
          setLoading(false);
        });

      // Store controller for cleanup
      eventSourceRef.current = controller;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setLoading(false);
    }
  }, [numberEvents, responsePreferences, closeEventSource]);

  useEffect(() => {
    if (!autoLoad) {
      return;
    }

    refresh();

    // Cleanup on unmount
    return () => {
      closeEventSource();
    };
  }, [autoLoad, refresh, closeEventSource]);

  return {
    events,
    loading,
    error,
    progress,
    refresh,
  };
}
