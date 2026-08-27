import React from "react";
import { Event } from "@/types/event";
import { EventCard } from "./event-card";
import { EmptyState } from "@/components/common/empty-state";

interface EventListProps {
  events: Event[];
  emptyTitle?: string;
  emptyDescription?: string;
  onRetry?: () => void;
}

export function EventList({
  events,
  emptyTitle = "No current affairs matching criteria.",
  emptyDescription = "Try adjusting your search filters or date range to discover events.",
  onRetry,
}: EventListProps) {
  if (events.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} onRetry={onRetry} />;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  );
}
