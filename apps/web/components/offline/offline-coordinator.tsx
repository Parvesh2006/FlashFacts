"use client";

import React, { useEffect, useState, useSyncExternalStore } from "react";
import { usePathname } from "next/navigation";
import { Wifi, ArrowLeft } from "lucide-react";
import { FactJumperGame } from "@/components/game/fact-jumper-game";

function subscribeOnline(callback: () => void) {
  window.addEventListener("online", callback);
  window.addEventListener("offline", callback);
  return () => {
    window.removeEventListener("online", callback);
    window.removeEventListener("offline", callback);
  };
}

function getOnlineSnapshot() {
  return typeof navigator !== "undefined" ? navigator.onLine : true;
}

function getServerOnlineSnapshot() {
  return true;
}

export function OfflineCoordinator() {
  const pathname = usePathname();
  const isOnline = useSyncExternalStore(
    subscribeOnline,
    getOnlineSnapshot,
    getServerOnlineSnapshot
  );

  const [dismissedGame, setDismissedGame] = useState<boolean>(false);
  const [onlineRestored, setOnlineRestored] = useState<boolean>(false);
  const [isOfflineReady, setIsOfflineReady] = useState<boolean>(false);

  // 1. Service Worker Registration & Cache Verification (Scenario 1)
  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) {
      return;
    }

    navigator.serviceWorker
      .register("/sw.js")
      .then(() => {
        if ("caches" in window) {
          caches.open("flashfacts-offline-v1").then((cache) => {
            cache.match("/offline.html").then((match) => {
              if (match) {
                setIsOfflineReady(true);
              }
            });
          });
        }
      })
      .catch((err) => {
        console.warn("[OfflineCoordinator] Service Worker registration failed:", err);
      });
  }, []);

  // 2. Track when online is restored while playing
  useEffect(() => {
    if (isOnline) {
      setOnlineRestored(true);
    } else {
      setDismissedGame(false);
      setOnlineRestored(false);
    }
  }, [isOnline]);

  const showGame = !isOnline && !dismissedGame;
  const isDedicatedGamePage = pathname === "/fact-jumper";

  // If offline on any other page, automatically launch Fact Jumper (Scenario 2)
  if (showGame && !isDedicatedGamePage) {
    return (
      <div className="fixed inset-0 z-50 bg-[var(--background)] flex flex-col overflow-y-auto p-4 sm:p-6 animate-in fade-in duration-200">
        {/* Top Status & Transition Bar */}
        <div className="w-full max-w-5xl mx-auto mb-4 flex flex-col gap-2">
          {onlineRestored ? (
            // Scenario 5: Internet restored without interrupting running game
            <div className="bg-emerald-600 text-white px-4 py-3 rounded-xl flex items-center justify-between shadow-lg">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Wifi className="w-4 h-4 animate-pulse" />
                <span>Internet Restored! FlashFacts services are available again.</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setDismissedGame(true)}
                  className="bg-white text-emerald-800 text-xs font-mono font-bold px-3 py-1.5 rounded-lg hover:bg-emerald-50 transition-colors flex items-center gap-1.5"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Return to FlashFacts</span>
                </button>
                <button
                  onClick={() => setOnlineRestored(false)}
                  className="text-white/80 hover:text-white text-xs px-2 py-1.5"
                >
                  Keep Playing
                </button>
              </div>
            </div>
          ) : (
            // Scenario 2: Offline detected, running Fact Jumper
            <div className="editorial-card px-4 py-3 flex items-center justify-between border-[var(--border)]">
              <div className="flex items-center gap-2.5">
                <div className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping" />
                <span className="text-xs font-mono font-bold tracking-wide uppercase text-[var(--text-primary)]">
                  Offline Detected — Fast Runner Activated
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-[var(--text-muted)] hidden sm:inline">
                  {isOfflineReady ? "Assets Precached" : "Running Locally"}
                </span>
                <button
                  onClick={() => setDismissedGame(true)}
                  className="text-xs font-mono text-[var(--brand-primary)] hover:underline flex items-center gap-1"
                >
                  <span>Dismiss</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Main Offline Game (Auto-started) */}
        <div className="w-full max-w-5xl mx-auto flex-1 flex flex-col justify-center">
          <FactJumperGame />
        </div>
      </div>
    );
  }

  // Subtle readiness indicator when online (Scenario 1)
  if (isOfflineReady && isOnline && !showGame) {
    return (
      <div
        className="fixed bottom-3 right-3 z-40 hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--surface)] border border-[var(--border)] text-[10px] font-mono text-[var(--text-muted)] opacity-70 hover:opacity-100 transition-opacity pointer-events-auto"
        title="Offline Fast Runner (Fact Jumper) cached and ready"
      >
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
        <span>Offline Ready</span>
      </div>
    );
  }

  return null;
}
