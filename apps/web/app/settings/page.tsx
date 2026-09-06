"use client";

import React, { useEffect, useState } from "react";
import {
  Settings,
  Server,
  Rss,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Shield,
} from "lucide-react";
import { api } from "@/lib/api";
import { getSources } from "@/services/sources";
import { Source } from "@/types/source";
import { BackButton } from "@/components/navigation/back-button";

interface HealthCheck {
  status: string;
}

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState<string>("");
  const [healthStatus, setHealthStatus] = useState<"checking" | "online" | "offline">("checking");
  const [healthDetails, setHealthDetails] = useState<HealthCheck | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [loadingSources, setLoadingSources] = useState<boolean>(true);

  useEffect(() => {
    setApiUrl(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

    // Check FastAPI /health endpoint
    api
      .get<HealthCheck>("/health")
      .then((res) => {
        setHealthStatus("online");
        setHealthDetails(res);
      })
      .catch(() => {
        setHealthStatus("offline");
      });

    // Fetch permitted RSS sources list
    getSources()
      .then(setSources)
      .catch(() => setSources([]))
      .finally(() => setLoadingSources(false));
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <BackButton fallbackHref="/" />

      {/* Header */}
      <div className="border-b pb-4">
        <div className="eyebrow flex items-center gap-2 mb-1">
          <Settings className="w-4 h-4" />
          <span>System Configuration & Telemetry</span>
        </div>
        <h1 className="headline text-3xl md:text-4xl">
          Settings
        </h1>
        <p className="body-copy text-sm">
          Environment configuration, API connection state, and source registry status.
        </p>
      </div>

      {/* 1. API Connection & Telemetry */}
      <div className="editorial-card p-5 md:p-6 space-y-4">
        <h2 className="text-sm font-bold text-[var(--text-primary)] font-mono flex items-center gap-2 border-b pb-3">
          <Server className="w-4 h-4 accent-mark" />
          <span>API Backend Connection Status</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
          <div className="editorial-panel p-4 space-y-2">
            <span className="text-[var(--text-secondary)] text-[11px] uppercase block">Configured API Base URL</span>
            <div className="flex flex-wrap items-center justify-between gap-2 text-[var(--text-primary)]">
              <span className="font-semibold text-[var(--brand-primary)] break-all">{apiUrl}</span>
              <span className="soft-badge text-[10px] px-2 py-0.5">
                NEXT_PUBLIC_API_URL
              </span>
            </div>
          </div>

          <div className="editorial-panel p-4 space-y-2">
            <span className="text-[var(--text-secondary)] text-[11px] uppercase block">FastAPI Health Response</span>
            <div className="flex items-center justify-between">
              {healthStatus === "checking" ? (
                <span className="text-[var(--text-secondary)] animate-pulse">Checking status...</span>
              ) : healthStatus === "online" ? (
                <span className="status-success inline-flex items-center gap-1.5 px-2 py-1 font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Backend Ready ({healthDetails?.status || "ok"})</span>
                </span>
              ) : (
                <span className="status-danger inline-flex items-center gap-1.5 px-2 py-1 font-bold">
                  <XCircle className="w-4 h-4" />
                  <span>Connection Failed</span>
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 2. Permitted RSS Sources Registry Status */}
      <div className="editorial-card p-5 md:p-6 space-y-4">
        <div className="flex items-center justify-between gap-3 border-b pb-3">
          <h2 className="text-sm font-bold text-[var(--text-primary)] font-mono flex items-center gap-2">
            <Rss className="w-4 h-4 accent-mark" />
            <span>Permitted News Sources Registry</span>
          </h2>
          <span className="meta-text text-right">
            {sources.length} Registered Sources
          </span>
        </div>

        {loadingSources ? (
          <p className="meta-text">Loading sources registry...</p>
        ) : (
          <div className="space-y-2">
            {sources.map((src) => (
              <div
                key={src.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 editorial-panel p-3 text-xs font-mono"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <span className="w-2 h-2 rounded-full bg-[var(--success)] mt-1.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <h4 className="font-bold text-[var(--text-primary)]">{src.name}</h4>
                    <span className="text-[11px] text-[var(--text-secondary)] break-all">{src.feed_url}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3 text-[var(--text-secondary)] sm:flex-shrink-0">
                  <span className="soft-badge text-[10px] px-2 py-0.5">
                    Reliability: {Math.round(src.reliability_score * 100)}%
                  </span>
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-[var(--brand-primary)] transition-colors"
                    aria-label={`Open ${src.name} website`}
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 4. Platform System Information */}
      <div className="editorial-panel p-4 text-xs font-mono text-[var(--text-secondary)] space-y-1">
        <div className="flex items-center gap-2 text-[var(--text-primary)] font-semibold mb-1">
          <Shield className="w-4 h-4 accent-mark" />
          <span>FlashFacts Intelligence Platform Architecture</span>
        </div>
        <p>Frontend: Next.js 15 (App Router, TypeScript, Tailwind CSS)</p>
        <p>Backend Engine: FastAPI Python 3.12 (PostgreSQL / SQLite, Alembic)</p>
        <p>Pipeline Phase: Phase 2 Web Application Completed</p>
      </div>
    </div>
  );
}
