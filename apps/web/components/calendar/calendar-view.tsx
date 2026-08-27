"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  Layers,
  Sparkles,
  Info,
} from "lucide-react";
import { getCalendar } from "@/services/calendar";
import { getEvents } from "@/services/events";
import { CalendarResponse, CalendarDayStat } from "@/types/calendar";
import { Event } from "@/types/event";
import { EventList } from "@/components/events/event-list";
import { SkeletonGrid } from "@/components/common/skeleton-loader";
import { ErrorState } from "@/components/common/error-state";
import { DomainBadge } from "@/components/common/badge";
import { formatDate } from "@/lib/utils";
import { BackButton } from "@/components/navigation/back-button";

export function CalendarView() {
  const todayObj = new Date();
  const currentMonthStr = `${todayObj.getFullYear()}-${String(todayObj.getMonth() + 1).padStart(2, "0")}`;
  const todayDateStr = todayObj.toISOString().split("T")[0];

  const [activeMonth, setActiveMonth] = useState<string>(currentMonthStr);
  const [calendarData, setCalendarData] = useState<CalendarResponse | null>(null);
  const [loadingCalendar, setLoadingCalendar] = useState<boolean>(true);
  const [calendarError, setCalendarError] = useState<string | null>(null);

  const [selectedDate, setSelectedDate] = useState<string | null>(todayDateStr);
  const [selectedEvents, setSelectedEvents] = useState<Event[]>([]);
  const [loadingEvents, setLoadingEvents] = useState<boolean>(false);

  // Fetch Monthly Calendar Summary
  const fetchCalendar = useCallback(async (month: string) => {
    setLoadingCalendar(true);
    setCalendarError(null);
    try {
      const res = await getCalendar(month);
      setCalendarData(res);
    } catch (err: unknown) {
      setCalendarError(err instanceof Error ? err.message : "Failed to load calendar data.");
    } finally {
      setLoadingCalendar(false);
    }
  }, []);

  useEffect(() => {
    fetchCalendar(activeMonth);
  }, [activeMonth, fetchCalendar]);

  // Fetch Events for Selected Date
  const fetchEventsForDate = useCallback(async (date: string) => {
    setLoadingEvents(true);
    try {
      const res = await getEvents({ date, limit: 100 });
      setSelectedEvents(res.events || []);
    } catch {
      setSelectedEvents([]);
    } finally {
      setLoadingEvents(false);
    }
  }, []);

  useEffect(() => {
    if (selectedDate) {
      fetchEventsForDate(selectedDate);
    }
  }, [selectedDate, fetchEventsForDate]);

  // Month navigation helpers
  const handlePrevMonth = () => {
    const [year, month] = activeMonth.split("-").map(Number);
    const prevDate = new Date(year, month - 2, 1);
    const newMonth = `${prevDate.getFullYear()}-${String(prevDate.getMonth() + 1).padStart(2, "0")}`;
    setActiveMonth(newMonth);
  };

  const handleNextMonth = () => {
    const [year, month] = activeMonth.split("-").map(Number);
    const nextDate = new Date(year, month, 1);
    const newMonth = `${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, "0")}`;
    setActiveMonth(newMonth);
  };

  const handleToday = () => {
    setActiveMonth(currentMonthStr);
    setSelectedDate(todayDateStr);
  };

  // Calendar Grid Matrix calculation
  const [yearNum, monthNum] = activeMonth.split("-").map(Number);
  const daysInMonth = new Date(yearNum, monthNum, 0).getDate();
  const firstDayOfWeek = new Date(yearNum, monthNum - 1, 1).getDay(); // 0 = Sun

  const dayStatsMap: Record<string, CalendarDayStat> = {};
  if (calendarData?.days) {
    calendarData.days.forEach((day) => {
      dayStatsMap[day.date] = day;
    });
  }

  const selectedDayStat = selectedDate ? dayStatsMap[selectedDate] : null;

  // Visual intensity color helper based on event count
  const getIntensityClass = (count: number, isSelected: boolean) => {
    if (isSelected) {
      return "border-2 border-[var(--brand-primary)] bg-[var(--brand-primary-soft)] text-[var(--brand-primary)] shadow-md font-bold";
    }
    if (count === 0) {
      return "border bg-[var(--surface)] text-[var(--text-muted)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-raised)]";
    }
    if (count <= 3) {
      return "border border-[var(--accent-border)] bg-[var(--accent-soft)] text-[var(--accent)] hover:border-[var(--accent)]";
    }
    if (count <= 8) {
      return "border border-[var(--brand-primary-border)] bg-[var(--brand-primary-soft)] text-[var(--brand-primary)] hover:border-[var(--brand-primary)]";
    }
    return "border border-[var(--brand-primary)] bg-[var(--brand-primary)] text-white font-bold shadow-sm";
  };

  const formattedMonthHeader = new Date(yearNum, monthNum - 1, 1).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  return (
    <div className="space-y-8">
      <BackButton fallbackHref="/" />

      {/* Calendar Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <div className="eyebrow flex items-center gap-2 mb-1">
            <CalendarIcon className="w-4 h-4" />
            <span>Temporal Event Explorer</span>
          </div>
          <h1 className="headline text-3xl md:text-4xl">
            Current Affairs Calendar
          </h1>
          <p className="body-copy text-sm">
            Browse indexed news events day-by-day across all domain categories.
          </p>
        </div>

        {/* Month Navigation Controls */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handlePrevMonth}
            className="control icon-button"
            title="Previous Month"
            aria-label="Previous month"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <span className="control font-mono text-sm font-bold px-4 py-1.5 min-w-[140px] text-center">
            {formattedMonthHeader}
          </span>

          <button
            type="button"
            onClick={handleNextMonth}
            className="control icon-button"
            title="Next Month"
            aria-label="Next month"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={handleToday}
            className="brand-button px-3 py-1.5 text-xs font-mono font-semibold"
          >
            Today
          </button>
        </div>
      </div>

      {calendarError ? (
        <ErrorState message={calendarError} onRetry={() => fetchCalendar(activeMonth)} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Month Grid (2 Columns on desktop) */}
          <div className="editorial-card p-5 space-y-4 lg:col-span-2">
            <div className="grid grid-cols-7 text-center font-mono text-[11px] font-semibold text-[var(--text-secondary)] uppercase border-b pb-2">
              <span>Sun</span>
              <span>Mon</span>
              <span>Tue</span>
              <span>Wed</span>
              <span>Thu</span>
              <span>Fri</span>
              <span>Sat</span>
            </div>

            {/* Grid Days Cells */}
            {loadingCalendar ? (
              <div className="h-64 flex items-center justify-center font-mono text-xs text-[var(--text-secondary)]">
                Loading monthly calendar matrix...
              </div>
            ) : (
              <div className="grid grid-cols-7 gap-2">
                {/* Empty cells for preceding month padding */}
                {Array.from({ length: firstDayOfWeek }).map((_, i) => (
                  <div key={`empty-${i}`} className="h-16 rounded-lg bg-[var(--surface-muted)]/60 border" />
                ))}

                {/* Days of current month */}
                {Array.from({ length: daysInMonth }).map((_, i) => {
                  const dayNum = i + 1;
                  const dateStr = `${yearNum}-${String(monthNum).padStart(2, "0")}-${String(dayNum).padStart(2, "0")}`;
                  const dayStat = dayStatsMap[dateStr];
                  const total = dayStat ? dayStat.total : 0;
                  const isSelected = selectedDate === dateStr;

                  return (
                    <button
                      key={dateStr}
                      type="button"
                      onClick={() => setSelectedDate(dateStr)}
                      aria-pressed={isSelected}
                      aria-label={`${formatDate(dateStr)}${total ? `, ${total} events` : ", no events"}`}
                      className={`h-16 rounded-lg p-2 flex flex-col justify-between text-left transition-all ${getIntensityClass(
                        total,
                        isSelected
                      )}`}
                    >
                      <span className="font-mono text-xs font-semibold">{dayNum}</span>
                      <div className="flex items-center justify-between text-[10px] font-mono">
                        {total > 0 ? (
                          <span className="px-1.5 py-0.5 rounded bg-[var(--surface)] border text-[var(--text-primary)] font-bold">
                            {total} {total === 1 ? "evt" : "evts"}
                          </span>
                        ) : (
                          <span className="text-[var(--text-muted)]">-</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Intensity Legend */}
            <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t meta-text">
              <span className="flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 accent-mark" />
                Volume Intensity:
              </span>
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded bg-[var(--surface)] border" /> 0
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded bg-[var(--accent-soft)] border border-[var(--accent-border)]" /> 1-3
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded bg-[var(--brand-primary-soft)] border border-[var(--brand-primary-border)]" /> 4-8
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded bg-[var(--brand-primary)] border border-[var(--brand-primary)]" /> 9+
                </span>
              </div>
            </div>
          </div>

          {/* Selected Date Summary Sidebar Panel */}
          <div className="editorial-card p-5 space-y-4 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="border-b pb-3">
                <span className="eyebrow block">
                  Selected Date Summary
                </span>
                <h3 className="headline text-xl">
                  {selectedDate ? formatDate(selectedDate) : "Select a Date"}
                </h3>
              </div>

              {selectedDayStat ? (
                <div className="space-y-4 font-mono text-xs">
                  <div className="editorial-panel p-3 flex items-center justify-between">
                    <span className="text-[var(--text-secondary)]">Total Indexed Events:</span>
                    <span className="text-base font-bold text-[var(--brand-primary)]">{selectedDayStat.total}</span>
                  </div>

                  {/* Domain Breakdown */}
                  <div>
                    <h4 className="meta-text uppercase mb-2 flex items-center gap-1">
                      <Layers className="w-3 h-3 accent-mark" />
                      Domain Distribution
                    </h4>
                    {Object.keys(selectedDayStat.domains || {}).length > 0 ? (
                      <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                        {Object.entries(selectedDayStat.domains).map(([domain, count]) => (
                          <div
                            key={domain}
                            className="flex items-center justify-between p-2 rounded-md bg-[var(--surface-muted)] border"
                          >
                            <DomainBadge domain={domain} />
                            <span className="font-bold text-[var(--text-primary)]">{count}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[var(--text-muted)] italic text-[11px]">No domain activity recorded.</p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="meta-text">
                  Click any calendar date to view volume breakdown and individual current affairs.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Selected Date Events List Section */}
      {selectedDate && (
        <section className="space-y-4 pt-4 border-t">
          <div className="flex items-center justify-between">
            <h2 className="headline text-2xl flex items-center gap-2">
              <Sparkles className="w-4 h-4 accent-mark" />
              <span>Events for {formatDate(selectedDate)}</span>
            </h2>
            <span className="meta-text">
              {selectedEvents.length} {selectedEvents.length === 1 ? "Event" : "Events"} Found
            </span>
          </div>

          {loadingEvents ? (
            <SkeletonGrid count={3} />
          ) : (
            <EventList
              events={selectedEvents}
              emptyTitle={`No events recorded for ${formatDate(selectedDate)}`}
              emptyDescription="No current affairs were indexed on this specific date."
            />
          )}
        </section>
      )}
    </div>
  );
}
