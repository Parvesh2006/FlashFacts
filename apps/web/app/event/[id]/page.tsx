"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { EventDetailView } from "@/components/events/event-detail-view";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { ErrorState } from "@/components/common/error-state";
import { getEvent, getEvents } from "@/services/events";
import { Event } from "@/types/event";

export default function EventDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [event, setEvent] = useState<Event | null>(null);
  const [relatedEvents, setRelatedEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const eventData = await getEvent(id);
      setEvent(eventData);

      // Fetch related events in same domain
      if (eventData?.domain) {
        try {
          const relRes = await getEvents({ domain: eventData.domain, limit: 4 });
          // Filter out current event from related list
          setRelatedEvents(relRes.events.filter((e) => e.id !== eventData.id));
        } catch {
          setRelatedEvents([]);
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Event not found or failed to load.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  if (loading) {
    return <LoadingSpinner label="Fetching event intelligence record..." />;
  }

  if (error || !event) {
    return (
      <ErrorState
        title="Event Intelligence Record Not Found"
        message={error || "The requested event record does not exist or has been removed."}
        onRetry={fetchDetail}
      />
    );
  }

  return <EventDetailView event={event} relatedEvents={relatedEvents} />;
}
