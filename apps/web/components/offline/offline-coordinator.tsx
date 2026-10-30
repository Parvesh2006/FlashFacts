"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import { usePathname } from "next/navigation";
import { Wifi, WifiOff, ArrowLeft, Loader2 } from "lucide-react";
import { FactJumperGame } from "@/components/game/fact-jumper-game";

async function probeBackendHealth(): Promise<boolean> {
  if (typeof window === "undefined") return true;
  if (!navigator.onLine) return false;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2500);
    const res = await fetch("/api/v1/health", {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    });
    clearTimeout(timer);
    return res.ok;
  } catch {
    return false;
  }
}

export function OfflineCoordinator() {
  const pathname = usePathname();
  const [isOffline, setIsOffline] = useState<boolean>(false);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [isReconnected, setIsReconnected] = useState<boolean>(false);
  const [dismissedGame, setDismissedGame] = useState<boolean>(false);

  const failureCountRef = useRef<number>(0);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 1. Service Worker Registration & Cache Verification
  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) {
      return;
    }

    navigator.serviceWorker
      .register("/sw.js")
      .catch((err) => {
        console.warn("[OfflineCoordinator] Service Worker registration failed:", err);
      });
  }, []);

  const handleConnectivityLoss = useCallback(() => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(async () => {
      // Confirm with active probe
      const healthy = await probeBackendHealth();
      if (!healthy) {
        setIsOffline(true);
        setIsReconnected(false);
        setIsVerifying(false);
        setDismissedGame(false);
      }
    }, 600);
  }, []);

  const handleConnectivityRestore = useCallback(async () => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    setIsVerifying(true);

    const healthy = await probeBackendHealth();
    setIsVerifying(false);

    if (healthy) {
      failureCountRef.current = 0;
      setIsReconnected(true);
    } else {
      // False positive (e.g. Wi-Fi connected to captive portal without internet)
      setIsOffline(true);
      setIsReconnected(false);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // Check initial state
    if (!navigator.onLine) {
      handleConnectivityLoss();
    }

    const onOffline = () => {
      handleConnectivityLoss();
    };

    const onOnline = () => {
      handleConnectivityRestore();
    };

    window.addEventListener("offline", onOffline);
    window.addEventListener("online", onOnline);

    // Periodic heartbeat every 45s while browsing to detect silent network loss
    const heartbeat = setInterval(async () => {
      if (!isOffline && navigator.onLine) {
        const healthy = await probeBackendHealth();
        if (!healthy) {
          failureCountRef.current += 1;
          if (failureCountRef.current >= 2) {
            handleConnectivityLoss();
          }
        } else {
          failureCountRef.current = 0;
        }
      }
    }, 45000);

    return () => {
      window.removeEventListener("offline", onOffline);
      window.removeEventListener("online", onOnline);
      clearInterval(heartbeat);
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [isOffline, handleConnectivityLoss, handleConnectivityRestore]);

  const isDedicatedGamePage = pathname === "/fact-jumper";
  const shouldShowOfflineScreen = isOffline && !dismissedGame && !isDedicatedGamePage;

  // Normal online behavior: completely hidden, zero screen clutter
  if (!shouldShowOfflineScreen) {
    return null;
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Offline Mode — Fact Jumper"
      className="fixed inset-0 z-50 bg-[var(--background)] flex flex-col overflow-y-auto p-4 sm:p-6 animate-in fade-in duration-200"
    >
      {/* Top Status & Transition Bar */}
      <div className="w-full max-w-5xl mx-auto mb-4 flex flex-col gap-2">
        {isVerifying ? (
          <div className="bg-[var(--surface)] border border-[var(--brand-primary)] text-[var(--text-primary)] px-4 py-3 rounded-xl flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2.5 text-xs font-mono">
              <Loader2 className="w-4 h-4 animate-spin text-[var(--brand-primary)]" />
              <span>Checking connection to FlashFacts servers...</span>
            </div>
          </div>
        ) : isReconnected ? (
          // Connection restored: offers explicit return or keep playing
          <div className="bg-emerald-600 text-white px-4 py-3 rounded-xl flex items-center justify-between shadow-lg animate-in fade-in duration-200">
            <div className="flex items-center gap-2.5 text-xs font-medium">
              <Wifi className="w-4 h-4 animate-pulse" />
              <span>Internet Restored! FlashFacts services are available again.</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setIsOffline(false);
                  setIsReconnected(false);
                  setDismissedGame(true);
                }}
                className="bg-white text-emerald-800 text-xs font-mono font-bold px-3 py-1.5 rounded-lg hover:bg-emerald-50 transition-colors flex items-center gap-1.5 cursor-pointer shadow-xs"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Return to FlashFacts</span>
              </button>
              <button
                type="button"
                onClick={() => setIsReconnected(false)}
                className="text-white/80 hover:text-white text-xs px-2.5 py-1.5 cursor-pointer"
              >
                Keep Playing
              </button>
            </div>
          </div>
        ) : (
          // Genuine Offline state: auto-running Fact Jumper
          <div className="editorial-card px-4 py-3 flex items-center justify-between border-[var(--border)] shadow-xs">
            <div className="flex items-center gap-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
              <div className="flex items-center gap-1.5 text-xs font-mono font-bold tracking-wide uppercase text-[var(--text-primary)]">
                <WifiOff className="w-3.5 h-3.5 text-amber-500" />
                <span>Offline Mode — Fact Jumper Activated</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-[11px] font-mono text-[var(--text-muted)] hidden sm:inline">
                Playing locally. Your page state is preserved.
              </span>
              <button
                type="button"
                onClick={() => setDismissedGame(true)}
                className="text-xs font-mono font-semibold text-[var(--brand-primary)] hover:underline flex items-center gap-1 cursor-pointer"
              >
                <span>Dismiss</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Offline Game Interface (Auto-running at tuned Chrome T-Rex speed) */}
      <div className="w-full max-w-5xl mx-auto flex-1 flex flex-col justify-center">
        <FactJumperGame
          autoStart={true}
          onReturnToApp={() => {
            setIsOffline(false);
            setDismissedGame(true);
          }}
        />
      </div>
    </div>
  );
}
