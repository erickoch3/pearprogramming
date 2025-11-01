export type Coordinates = [number, number];

export interface Event {
  location: Coordinates;
  name: string;
  emoji: string;
  event_score: number;
  description: string;
  link?: string | null;
}

export interface GetEventRecommendationsResponse {
  events: Event[];
}

export interface GetEventRecommendationsRequest {
  number_events: number;
  response_preferences?: string | null;
}

