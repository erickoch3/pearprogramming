import type { Event } from "@/types/events";
import type { ProgressUpdate } from "@/hooks/useStreamingEventRecommendations";
import { EventList } from "./EventList";

interface EventListSectionProps {
  events: Event[];
  loading: boolean;
  error: string | null;
  progress?: ProgressUpdate | null;
  onSelectEvent?: (event: Event) => void;
}

export function EventListSection({ events, loading, error, progress, onSelectEvent }: EventListSectionProps) {
  return (
    <aside className="flex-1 h-full overflow-hidden">
      <EventList
        events={events}
        loading={loading}
        error={error}
        progress={progress}
        onSelectEvent={onSelectEvent}
      />
    </aside>
  );
}
