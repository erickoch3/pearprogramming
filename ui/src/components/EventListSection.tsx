import type { Event } from "@/types/events";
import { EventList } from "./EventList";

interface EventListSectionProps {
  events: Event[];
  loading: boolean;
  error: string | null;
  onSelectEvent?: (event: Event) => void;
}

export function EventListSection({ events, loading, error, onSelectEvent }: EventListSectionProps) {
  return (
    <aside className="flex-1 h-full overflow-hidden">
      <EventList
        events={events}
        loading={loading}
        error={error}
        onSelectEvent={onSelectEvent}
      />
    </aside>
  );
}
