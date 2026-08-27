import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString?: string): string {
  if (!dateString) return "N/A";
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateString;
  }
}

export function formatDateTime(dateString?: string): string {
  if (!dateString) return "N/A";
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateString;
  }
}

export function getDomainColor(domain: string) {
  const d = domain.toLowerCase();
  if (d.includes("ai")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-ai)_12%,transparent)]",
      text: "text-[var(--domain-ai)]",
      border: "border-[color-mix(in_srgb,var(--domain-ai)_34%,var(--border))]",
      accent: "var(--domain-ai)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-ai)_10%,transparent)]",
    };
  }
  if (d.includes("tech")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-technology)_12%,transparent)]",
      text: "text-[var(--domain-technology)]",
      border: "border-[color-mix(in_srgb,var(--domain-technology)_34%,var(--border))]",
      accent: "var(--domain-technology)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-technology)_10%,transparent)]",
    };
  }
  if (d.includes("gov")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-government)_12%,transparent)]",
      text: "text-[var(--domain-government)]",
      border: "border-[color-mix(in_srgb,var(--domain-government)_34%,var(--border))]",
      accent: "var(--domain-government)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-government)_10%,transparent)]",
    };
  }
  if (d.includes("politi")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-politics)_12%,transparent)]",
      text: "text-[var(--domain-politics)]",
      border: "border-[color-mix(in_srgb,var(--domain-politics)_34%,var(--border))]",
      accent: "var(--domain-politics)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-politics)_10%,transparent)]",
    };
  }
  if (d.includes("econ") || d.includes("financ")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-economy)_12%,transparent)]",
      text: "text-[var(--domain-economy)]",
      border: "border-[color-mix(in_srgb,var(--domain-economy)_34%,var(--border))]",
      accent: "var(--domain-economy)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-economy)_10%,transparent)]",
    };
  }
  if (d.includes("defen") || d.includes("milit")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-defence)_12%,transparent)]",
      text: "text-[var(--domain-defence)]",
      border: "border-[color-mix(in_srgb,var(--domain-defence)_34%,var(--border))]",
      accent: "var(--domain-defence)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-defence)_10%,transparent)]",
    };
  }
  if (d.includes("scien") || d.includes("space")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-science)_12%,transparent)]",
      text: "text-[var(--domain-science)]",
      border: "border-[color-mix(in_srgb,var(--domain-science)_34%,var(--border))]",
      accent: "var(--domain-science)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-science)_10%,transparent)]",
    };
  }
  if (d.includes("envir") || d.includes("clima")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-environment)_12%,transparent)]",
      text: "text-[var(--domain-environment)]",
      border: "border-[color-mix(in_srgb,var(--domain-environment)_34%,var(--border))]",
      accent: "var(--domain-environment)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-environment)_10%,transparent)]",
    };
  }
  if (d.includes("sport")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-sports)_12%,transparent)]",
      text: "text-[var(--domain-sports)]",
      border: "border-[color-mix(in_srgb,var(--domain-sports)_34%,var(--border))]",
      accent: "var(--domain-sports)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-sports)_10%,transparent)]",
    };
  }
  if (d.includes("internat") || d.includes("world")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-international)_12%,transparent)]",
      text: "text-[var(--domain-international)]",
      border: "border-[color-mix(in_srgb,var(--domain-international)_34%,var(--border))]",
      accent: "var(--domain-international)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-international)_10%,transparent)]",
    };
  }
  if (d.includes("medic") || d.includes("health")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-medical)_12%,transparent)]",
      text: "text-[var(--domain-medical)]",
      border: "border-[color-mix(in_srgb,var(--domain-medical)_34%,var(--border))]",
      accent: "var(--domain-medical)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-medical)_10%,transparent)]",
    };
  }
  if (d.includes("educ")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-education)_12%,transparent)]",
      text: "text-[var(--domain-education)]",
      border: "border-[color-mix(in_srgb,var(--domain-education)_34%,var(--border))]",
      accent: "var(--domain-education)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-education)_10%,transparent)]",
    };
  }
  if (d.includes("engineer")) {
    return {
      bg: "bg-[color-mix(in_srgb,var(--domain-engineering)_12%,transparent)]",
      text: "text-[var(--domain-engineering)]",
      border: "border-[color-mix(in_srgb,var(--domain-engineering)_34%,var(--border))]",
      accent: "var(--domain-engineering)",
      badgeBg: "bg-[color-mix(in_srgb,var(--domain-engineering)_10%,transparent)]",
    };
  }
  return {
    bg: "bg-[var(--surface-muted)]",
    text: "text-[var(--text-secondary)]",
    border: "border-[var(--border)]",
    accent: "var(--text-muted)",
    badgeBg: "bg-[var(--surface-muted)]",
  };
}
