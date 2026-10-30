import React from "react";

interface IllustrationProps {
  className?: string;
  size?: number;
}

/**
 * Friendly Student Scholar Mascot reading an editorial newspaper/book with glasses.
 * Features a subtle greeting animation on initial render.
 */
export function StudentMascot({ className = "", size = 120 }: IllustrationProps) {
  return (
    <div
      className={`relative inline-flex items-center justify-center select-none ${className}`}
      style={{ width: size, height: size }}
      aria-label="Student scholar mascot reading current affairs"
    >
      <svg
        viewBox="0 0 160 160"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full drop-shadow-sm mascot-greeting"
      >
        {/* Soft Background Circular Glow */}
        <circle cx="80" cy="80" r="74" fill="var(--surface-muted)" stroke="var(--border)" strokeWidth="2" />
        <circle cx="80" cy="80" r="64" fill="var(--surface)" />

        {/* Head & Face */}
        <ellipse cx="80" cy="68" rx="34" ry="32" fill="#FCE7D0" stroke="#202124" strokeWidth="2.5" />

        {/* Hair - Neat Editorial Scholar Cut */}
        <path
          d="M48 62 C48 38, 70 32, 80 32 C92 32, 112 38, 112 62 C106 54, 98 50, 80 50 C62 50, 54 54, 48 62 Z"
          fill="#3B2314"
        />
        <path
          d="M46 64 C44 56, 48 44, 60 38 C72 32, 88 32, 100 38 C112 44, 116 56, 114 64"
          stroke="#202124"
          strokeWidth="2.5"
          strokeLinecap="round"
        />

        {/* Cheeks */}
        <circle cx="62" cy="76" r="4.5" fill="#F87171" opacity="0.4" />
        <circle cx="98" cy="76" r="4.5" fill="#F87171" opacity="0.4" />

        {/* Friendly Glasses (Editorial Reader) */}
        {/* Left Lens */}
        <circle cx="68" cy="68" r="12" fill="#FFFFFF" fillOpacity="0.75" stroke="#2457C5" strokeWidth="2.5" />
        <circle cx="68" cy="68" r="2.5" fill="#202124" />
        <circle cx="70" cy="66" r="1" fill="#FFFFFF" />

        {/* Right Lens */}
        <circle cx="92" cy="68" r="12" fill="#FFFFFF" fillOpacity="0.75" stroke="#2457C5" strokeWidth="2.5" />
        <circle cx="92" cy="68" r="2.5" fill="#202124" />
        <circle cx="94" cy="66" r="1" fill="#FFFFFF" />

        {/* Glasses Bridge */}
        <path d="M80 67 C80 65, 80 65, 80 65" stroke="#2457C5" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="77" y1="67" x2="83" y2="67" stroke="#2457C5" strokeWidth="2.5" strokeLinecap="round" />

        {/* Happy Smile */}
        <path d="M75 83 Q80 87 85 83" stroke="#202124" strokeWidth="2" strokeLinecap="round" fill="none" />

        {/* Torso / Warm Editorial Sweater */}
        <path
          d="M46 138 C48 112, 60 102, 80 102 C100 102, 112 112, 114 138 Z"
          fill="#2457C5"
          stroke="#202124"
          strokeWidth="2.5"
        />
        {/* Shirt Collar */}
        <polygon points="80,102 72,114 80,111 88,114" fill="#FFFFFF" stroke="#202124" strokeWidth="1.5" />

        {/* Open Study Book (Exam Revision) */}
        <g transform="translate(42, 108)">
          {/* Left Page */}
          <path
            d="M38 12 C24 10, 10 14, 2 24 L2 38 C10 28, 24 24, 38 26 Z"
            fill="#FAF9F6"
            stroke="#202124"
            strokeWidth="2"
          />
          {/* Right Page */}
          <path
            d="M38 12 C52 10, 66 14, 74 24 L74 38 C66 28, 52 24, 38 26 Z"
            fill="#FAF9F6"
            stroke="#202124"
            strokeWidth="2"
          />
          {/* Spine & Bookmark Ribbon */}
          <line x1="38" y1="12" x2="38" y2="28" stroke="#202124" strokeWidth="2" />
          <path d="M38 24 L42 34 L38 31 L34 34 Z" fill="#0F766E" />
          {/* Page Lines */}
          <line x1="10" y1="26" x2="30" y2="23" stroke="#CBD5E1" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="10" y1="31" x2="26" y2="28" stroke="#CBD5E1" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="46" y1="23" x2="66" y2="26" stroke="#CBD5E1" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="50" y1="28" x2="66" y2="31" stroke="#CBD5E1" strokeWidth="1.5" strokeLinecap="round" />
        </g>

        {/* Little Sparkle of Knowledge */}
        <path
          d="M124 42 Q124 48 130 48 Q124 48 124 54 Q124 48 118 48 Q124 48 124 42 Z"
          fill="#0F766E"
        />
        <circle cx="34" cy="46" r="2" fill="#2457C5" />
      </svg>
    </div>
  );
}

/**
 * Friendly Empty Search Results Illustration
 */
export function EmptySearchIllustration({ className = "", size = 120 }: IllustrationProps) {
  return (
    <div
      className={`relative inline-flex items-center justify-center select-none ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 140 140" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
        {/* Soft Background */}
        <rect x="10" y="10" width="120" height="120" rx="24" fill="var(--surface-muted)" stroke="var(--border)" strokeWidth="2" />

        {/* Newspaper Document */}
        <rect x="30" y="32" width="60" height="74" rx="4" fill="#FFFFFF" stroke="#202124" strokeWidth="2" />
        <rect x="36" y="40" width="30" height="6" rx="1.5" fill="#2457C5" />
        <line x1="36" y1="52" x2="74" y2="52" stroke="#E5E7EB" strokeWidth="2" strokeLinecap="round" />
        <line x1="36" y1="58" x2="80" y2="58" stroke="#E5E7EB" strokeWidth="2" strokeLinecap="round" />
        <line x1="36" y1="64" x2="70" y2="64" stroke="#E5E7EB" strokeWidth="2" strokeLinecap="round" />
        <line x1="36" y1="70" x2="78" y2="70" stroke="#E5E7EB" strokeWidth="2" strokeLinecap="round" />

        {/* Magnifying Glass */}
        <g transform="translate(62, 54)">
          <circle cx="26" cy="26" r="20" fill="#FFFFFF" fillOpacity="0.85" stroke="#202124" strokeWidth="3" />
          <circle cx="26" cy="26" r="16" fill="var(--brand-primary-soft)" opacity="0.6" />
          {/* Glass Glare */}
          <path d="M16 20 A 14 14 0 0 1 26 12" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" />
          {/* Question Mark Inside Lens */}
          <text
            x="26"
            y="32"
            textAnchor="middle"
            fontFamily="Georgia, serif"
            fontSize="18"
            fontWeight="bold"
            fill="#2457C5"
          >
            ?
          </text>
          {/* Handle */}
          <line x1="41" y1="41" x2="56" y2="56" stroke="#202124" strokeWidth="4.5" strokeLinecap="round" />
          <line x1="41" y1="41" x2="56" y2="56" stroke="#0F766E" strokeWidth="2.5" strokeLinecap="round" />
        </g>

        {/* Little Sparkles */}
        <path d="M24 24 Q24 28 28 28 Q24 28 24 32 Q24 28 20 28 Q24 28 24 24 Z" fill="#0F766E" />
      </svg>
    </div>
  );
}

/**
 * Friendly Empty Bookmarks / Mistake Book Illustration
 */
export function EmptyBookmarksIllustration({ className = "", size = 120 }: IllustrationProps) {
  return (
    <div
      className={`relative inline-flex items-center justify-center select-none ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 140 140" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
        <circle cx="70" cy="70" r="58" fill="var(--surface-muted)" stroke="var(--border)" strokeWidth="2" />

        {/* Open Book */}
        <path
          d="M32 46 C46 42, 60 44, 70 50 L70 94 C60 88, 46 86, 32 90 Z"
          fill="#FFFFFF"
          stroke="#202124"
          strokeWidth="2.5"
        />
        <path
          d="M70 50 C80 44, 94 42, 108 46 L108 90 C94 86, 80 88, 70 94 Z"
          fill="#FFFFFF"
          stroke="#202124"
          strokeWidth="2.5"
        />
        <line x1="70" y1="50" x2="70" y2="94" stroke="#202124" strokeWidth="2.5" />

        {/* Ribbon Bookmark */}
        <path d="M70 42 L70 76 L76 70 L82 76 L82 42 Z" fill="#0F766E" stroke="#202124" strokeWidth="1.5" />

        {/* Checkmark Ribbon badge */}
        <circle cx="94" cy="40" r="12" fill="#059669" stroke="#FFFFFF" strokeWidth="2" />
        <path d="M89 40 L93 44 L99 36" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

/**
 * Friendly Completed Mock Test Illustration
 */
export function CompletedTestIllustration({ className = "", size = 120 }: IllustrationProps) {
  return (
    <div
      className={`relative inline-flex items-center justify-center select-none ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 140 140" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
        <circle cx="70" cy="70" r="58" fill="var(--surface-muted)" stroke="var(--border)" strokeWidth="2" />

        {/* Trophy / Gold Cup */}
        <path
          d="M48 40 L92 40 L86 72 C84 80, 78 86, 70 86 C62 86, 56 80, 54 72 Z"
          fill="#F59E0B"
          stroke="#202124"
          strokeWidth="2.5"
        />
        {/* Handles */}
        <path d="M48 48 C36 48, 36 66, 52 66" stroke="#202124" strokeWidth="2.5" fill="none" />
        <path d="M92 48 C104 48, 104 66, 88 66" stroke="#202124" strokeWidth="2.5" fill="none" />

        {/* Trophy Stem & Base */}
        <rect x="66" y="86" width="8" height="14" fill="#D97706" stroke="#202124" strokeWidth="2" />
        <rect x="50" y="100" width="40" height="10" rx="3" fill="#202124" />

        {/* Star in Trophy */}
        <polygon
          points="70,52 72.5,58 79,58.5 74,62.5 75.5,69 70,65.5 64.5,69 66,62.5 61,58.5 67.5,58"
          fill="#FFFFFF"
        />

        {/* Sparkles around trophy */}
        <path d="M30 36 Q30 40 34 40 Q30 40 30 44 Q30 40 26 40 Q30 40 30 36 Z" fill="#2457C5" />
        <path d="M108 30 Q108 34 112 34 Q108 34 108 38 Q108 34 104 34 Q108 34 108 30 Z" fill="#0F766E" />
      </svg>
    </div>
  );
}

/**
 * Friendly Educational Topic Icon / Illustration (Science, Environment, Space, History)
 */
export function EducationalTopicBadge({
  topic = "science",
  className = "",
  size = 48,
}: {
  topic?: "science" | "space" | "environment" | "history" | "polity";
  className?: string;
  size?: number;
}) {
  return (
    <div
      className={`inline-flex items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-primary)] ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      {topic === "space" && (
        <svg viewBox="0 0 24 24" width={size * 0.55} height={size * 0.55} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" />
          <path d="M3.6 9h16.8" />
          <path d="M3.6 15h16.8" />
          <path d="M12 3a15 15 0 0 1 0 18" />
          <path d="M12 3a15 15 0 0 0 0 18" />
        </svg>
      )}
      {topic === "environment" && (
        <svg viewBox="0 0 24 24" width={size * 0.55} height={size * 0.55} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M11 20A7 7 0 0 1 4 13C4 8.5 8 3 12 3c4 0 8 5.5 8 10a7 7 0 0 1-7 7Z" />
          <path d="M12 10v10" />
        </svg>
      )}
      {topic === "history" && (
        <svg viewBox="0 0 24 24" width={size * 0.55} height={size * 0.55} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 21h18" />
          <path d="M5 21V7l7-4 7 4v14" />
          <path d="M9 10h6" />
          <path d="M9 14h6" />
          <path d="M9 18h6" />
        </svg>
      )}
      {topic === "polity" && (
        <svg viewBox="0 0 24 24" width={size * 0.55} height={size * 0.55} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M2 20h20" />
          <path d="m12 4 8 4H4l8-4Z" />
          <path d="M6 8v9" />
          <path d="M10 8v9" />
          <path d="M14 8v9" />
          <path d="M18 8v9" />
        </svg>
      )}
      {topic === "science" && (
        <svg viewBox="0 0 24 24" width={size * 0.55} height={size * 0.55} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 2v7.31L4.2 18.1A2 2 0 0 0 5.8 21h12.4a2 2 0 0 0 1.6-2.9L14 9.31V2" />
          <path d="M8.5 2h7" />
          <path d="M14 9.3 8.5 18" />
        </svg>
      )}
    </div>
  );
}
