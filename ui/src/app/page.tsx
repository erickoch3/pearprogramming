"use client";

import { useMemo, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { EventDetailsModal } from "@/components/EventDetailsModal";
import { EventListSection } from "@/components/EventListSection";
import { MapSection } from "@/components/MapSection";
import { SettingsButton } from "@/components/SettingsButton";
import { useEventRecommendations } from "@/hooks/useEventRecommendations";
import { useUserSettings } from "@/hooks/useUserSettings";
import type { Event } from "@/types/events";

const DEFAULT_NUMBER_EVENTS = 8;

export default function HomePage() {
  const { activityPreferences } = useUserSettings();
  const eventRequest = useMemo(
    () => ({
      number_events: DEFAULT_NUMBER_EVENTS,
      response_preferences: activityPreferences,
    }),
    [activityPreferences],
  );

  const { events, loading, error } = useEventRecommendations(eventRequest);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);

  const handleSelectEvent = (event: Event) => {
    setSelectedEvent(event);
  };

  const handleCloseModal = () => {
    setSelectedEvent(null);
  };

  return (
    <div className="relative h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-neutral-50 font-sans text-neutral-900 dark:from-neutral-950 dark:via-neutral-900 dark:to-neutral-950 dark:text-neutral-50 overflow-hidden">
      <SettingsButton />

      <div className="flex h-full flex-col items-center px-4 py-24">
        <AppHeader />

        <div className="flex flex-row gap-4 w-full max-w-7xl h-[calc(100%-10rem)] mb-16">
          <MapSection events={events} />
          <EventListSection
            events={events}
            loading={loading}
            error={error}
            onSelectEvent={handleSelectEvent}
          />
        </div>
      </div>

      {selectedEvent ? (
        <EventDetailsModal event={selectedEvent} onClose={handleCloseModal} />
      ) : null}
    </div>
  );
}
